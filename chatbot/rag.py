"""
RAG (Retrieval Augmented Generation) service for the recipe chatbot.

Flow:
1. Index: Recipe text → embeddings → ChromaDB
2. Query: User message → embedding → retrieve similar recipes
3. Generate: Retrieved recipes + user message → LLM → answer
"""

import os
from typing import Optional

from django.conf import settings


def _get_recipe_document(recipe) -> str:
    """Build a single searchable text document from a Recipe instance."""
    parts = [
        f"Title: {recipe.title}",
        f"Description: {recipe.description}",
        f"Difficulty: {recipe.difficulty}",
        f"Prep time: {recipe.prep_time} minutes. Cook time: {recipe.cook_time} minutes.",
        f"Servings: {recipe.servings}",
        f"Instructions: {recipe.instructions}",
    ]
    # Add ingredient names and quantities
    ing_parts = []
    for ri in recipe.recipe_ingredients.select_related("ingredient").all():
        ing_parts.append(f"{ri.quantity} {ri.ingredient.name}")
    if ing_parts:
        parts.append("Ingredients: " + ", ".join(ing_parts))
    if recipe.category_id:
        parts.append(f"Category: {recipe.category.name}")
    return "\n".join(parts)


def _get_openai_api_key() -> Optional[str]:
    """Get OpenAI API key from environment or Django settings."""
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        return key
    key = getattr(settings, "OPENAI_API_KEY", None)
    return key if key else None


def _get_gemini_api_key() -> Optional[str]:
    """Get Gemini API key from environment or Django settings."""
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if key:
        return key
    key = getattr(settings, "GEMINI_API_KEY", None)
    return key if key else None


def _use_gemini() -> bool:
    """Use Gemini when its API key is set (default for learning/free tier)."""
    return bool(_get_gemini_api_key())


def index_recipes_into_chroma(collection, embedding_fn, Recipe):
    """
    Index all recipes into a ChromaDB collection.
    collection: ChromaDB collection (with .add expecting ids, documents, metadatas).
    embedding_fn: callable(documents: list[str]) -> list[list[float]].
    Recipe: the Recipe model class (avoid circular import).
    """
    from recipes.models import Recipe as RecipeModel

    recipes = list(
        RecipeModel.objects.select_related("category")
        .prefetch_related("recipe_ingredients__ingredient")
    )
    if not recipes:
        return 0

    ids = []
    documents = []
    metadatas = []

    for recipe in recipes:
        ids.append(str(recipe.pk))
        documents.append(_get_recipe_document(recipe))
        metadatas.append({
            "recipe_id": recipe.pk,
            "title": recipe.title[:200],
        })

    # Chroma can do batch add; if embedding_fn is per-doc, we still pass texts
    embeddings = embedding_fn(documents)
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )
    return len(recipes)


def get_chroma_collection(persist_directory: str, embedding_fn):
    """Get or create a ChromaDB collection for recipes."""
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    client = chromadb.PersistentClient(
        path=persist_directory,
        settings=ChromaSettings(anonymized_telemetry=False),
    )
    collection = client.get_or_create_collection(
        name="recipe_docs",
        metadata={"description": "Recipe documents for RAG"},
    )
    return collection


def build_openai_embedding_fn():
    """Build a function that embeds a list of texts using OpenAI."""
    from openai import OpenAI

    key = _get_openai_api_key()
    if not key:
        return None

    client = OpenAI(api_key=key)
    model = "text-embedding-3-small"

    def embed(texts):
        out = client.embeddings.create(input=texts, model=model)
        return [item.embedding for item in out.data]

    return embed


def build_gemini_embedding_fn(task_type: str = "RETRIEVAL_DOCUMENT"):
    """
    Build a function that embeds a list of texts using Gemini (gemini-embedding-001).
    task_type: RETRIEVAL_DOCUMENT for indexing recipes, RETRIEVAL_QUERY for user queries.
    """
    key = _get_gemini_api_key()
    if not key:
        return None

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return None

    client = genai.Client(api_key=key)
    model = "gemini-embedding-001"

    def embed(texts):
        result = client.models.embed_content(
            model=model,
            contents=texts,
            config=types.EmbedContentConfig(task_type=task_type),
        )
        if not result or not getattr(result, "embeddings", None):
            return [[]] * len(texts) if texts else []
        return [list(e.values) for e in result.embeddings]

    return embed


def retrieve_relevant_recipes(collection, query: str, embedding_fn, n: int = 5):
    """
    Retrieve top-n recipe IDs and their snippets from ChromaDB.
    Returns list of dicts: [{"recipe_id": int, "title": str, "snippet": str}, ...]
    """
    if not query.strip():
        return []
    try:
        total = collection.count()
    except Exception:
        total = 0
    if total == 0:
        return []

    query_embedding = embedding_fn([query.strip()])[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n, total),
        include=["documents", "metadatas", "distances"],
    )

    if not results or not results["ids"] or not results["ids"][0]:
        return []

    out = []
    for i, doc_id in enumerate(results["ids"][0]):
        metadatas = results["metadatas"][0]
        documents = results["documents"][0]
        meta = metadatas[i] if i < len(metadatas) else {}
        doc = documents[i] if i < len(documents) else ""
        snippet = (doc[:300] + "...") if len(doc) > 300 else doc
        out.append({
            "recipe_id": meta.get("recipe_id") or int(doc_id),
            "title": meta.get("title", ""),
            "snippet": snippet,
        })
    return out


def generate_answer_with_openai(user_message: str, retrieved: list, base_url: str = "") -> str:
    """
    Build a prompt from retrieved recipes and call OpenAI to generate an answer.
    base_url: e.g. "http://127.0.0.1:8001" for linking recipes in the answer.
    """
    from openai import OpenAI

    key = _get_openai_api_key()
    if not key:
        return (
            "I don't have an API key configured for the AI. "
            "Add OPENAI_API_KEY to your environment to enable smart answers. "
            "You can still search recipes on the site!"
        )

    client = OpenAI(api_key=key)

    context_parts = []
    for r in retrieved:
        link = f"{base_url}/{r['recipe_id']}/" if base_url else ""
        context_parts.append(f"[Recipe: {r['title']} (ID: {r['recipe_id']})]\n{r['snippet']}\n")

    context = "\n".join(context_parts) if context_parts else "No specific recipes were found in the database."

    system = (
        "You are a helpful recipe assistant for a recipe sharing website. "
        "Answer the user's question based ONLY on the recipe context below. "
        "If the context doesn't contain enough information, say so and suggest they browse the site. "
        "Keep answers concise and friendly. Mention recipe names when relevant."
    )
    user_content = (
        "Recipe context:\n" + context + "\n\nUser question: " + user_message
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        max_tokens=500,
    )
    return response.choices[0].message.content or "I couldn't generate an answer."


def generate_answer_with_gemini(user_message: str, retrieved: list, base_url: str = "") -> str:
    """
    Build a prompt from retrieved recipes and call Gemini to generate an answer.
    """
    key = _get_gemini_api_key()
    if not key:
        return (
            "I don't have a Gemini API key configured. "
            "Add GEMINI_API_KEY to your environment to enable smart answers. "
            "You can still search recipes on the site!"
        )

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return "Please install google-genai: pip install google-genai"

    client = genai.Client(api_key=key)

    context_parts = []
    for r in retrieved:
        context_parts.append(f"[Recipe: {r['title']} (ID: {r['recipe_id']})]\n{r['snippet']}\n")
    context = "\n".join(context_parts) if context_parts else "No specific recipes were found in the database."

    system = (
        "You are a helpful recipe assistant for a recipe sharing website. "
        "Answer the user's question based ONLY on the recipe context below. "
        "If the context doesn't contain enough information, say so and suggest they browse the site. "
        "Keep answers concise and friendly. Mention recipe names when relevant."
    )
    user_content = "Recipe context:\n" + context + "\n\nUser question: " + user_message

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_content,
        config=types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=500,
        ),
    )
    if response and getattr(response, "text", None):
        return response.text
    return "I couldn't generate an answer."


def fallback_answer(user_message: str, Recipe) -> tuple[str, list]:
    """
    When Chroma/OpenAI is not available: simple keyword search on Recipe model.
    Returns (answer_text, list of recipe IDs that were used).
    """
    from django.db.models import Q

    # Simple keyword search on title, description, instructions
    words = [w.strip() for w in user_message.split() if len(w.strip()) > 2][:5]
    if not words:
        return (
            "Ask me about recipes, ingredients, or cooking! For example: 'Easy Italian recipes' or 'What can I make with tomatoes?'",
            [],
        )

    q = Q()
    for w in words:
        q |= (
            Q(title__icontains=w)
            | Q(description__icontains=w)
            | Q(instructions__icontains=w)
        )
    recipes = list(Recipe.objects.filter(q).select_related("category").distinct()[:5])
    recipe_ids = [r.pk for r in recipes]

    if not recipes:
        return (
            f"I couldn't find recipes matching '{user_message}'. Try different keywords or browse all recipes on the site!",
            [],
        )

    titles = [r.title for r in recipes]
    answer = (
        f"I found {len(recipes)} recipe(s) that might match: {', '.join(titles)}. "
        "Check them out on the recipes page for full details!"
    )
    return answer, recipe_ids


def get_rag_response(user_message: str, request=None) -> dict:
    """
    Full RAG pipeline: retrieve recipes (from Chroma if available), then generate answer.
    Prefers Gemini when GEMINI_API_KEY is set, otherwise uses OpenAI.
    Falls back to keyword search + template when no API key or no index.

    Returns dict: {
        "answer": str,
        "retrieved_docs": [{"recipe_id": int, "title": str}, ...],
        "confidence": float,
    }
    """
    from recipes.models import Recipe

    base_url = ""
    if request:
        base_url = request.build_absolute_uri("/").rstrip("/")

    persist_dir = getattr(settings, "CHROMA_PERSIST_DIR", None)
    if not persist_dir:
        persist_dir = os.path.join(settings.BASE_DIR, "chroma_recipe_db")

    # Prefer Gemini (free tier), then OpenAI
    use_gemini = _use_gemini()
    if use_gemini:
        embedding_fn = build_gemini_embedding_fn("RETRIEVAL_QUERY")  # for user query
        generate_fn = generate_answer_with_gemini
    else:
        embedding_fn = build_openai_embedding_fn()
        generate_fn = generate_answer_with_openai

    use_rag = bool(embedding_fn and os.path.isdir(persist_dir))

    if use_rag:
        try:
            collection = get_chroma_collection(persist_dir, embedding_fn)
            if collection.count() == 0:
                use_rag = False
        except Exception:
            use_rag = False

    if use_rag:
        try:
            retrieved = retrieve_relevant_recipes(
                collection, user_message, embedding_fn, n=5
            )
            if retrieved:
                answer = generate_fn(user_message, retrieved, base_url)
                confidence = 0.9
                retrieved_docs = [
                    {"recipe_id": r["recipe_id"], "title": r["title"]}
                    for r in retrieved
                ]
            else:
                answer = generate_fn(user_message, [], base_url)
                confidence = 0.6
                retrieved_docs = []
        except Exception:
            answer, recipe_ids = fallback_answer(user_message, Recipe)
            retrieved_docs = [
                {"recipe_id": rid, "title": Recipe.objects.filter(pk=rid).values_list("title", flat=True).first() or ""}
                for rid in recipe_ids
            ]
            confidence = 0.5
    else:
        answer, recipe_ids = fallback_answer(user_message, Recipe)
        retrieved_docs = [
            {"recipe_id": rid, "title": Recipe.objects.filter(pk=rid).values_list("title", flat=True).first() or ""}
            for rid in recipe_ids
        ]
        confidence = 0.6

    return {
        "answer": answer,
        "retrieved_docs": retrieved_docs,
        "confidence": confidence,
    }
