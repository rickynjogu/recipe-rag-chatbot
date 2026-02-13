"""
Management command to index all recipes into ChromaDB for RAG.

Usage:
  python manage.py index_recipes

Requires OPENAI_API_KEY to be set (for embeddings).
Creates/updates the persistent Chroma collection at CHROMA_PERSIST_DIR or chroma_recipe_db/.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import os


class Command(BaseCommand):
    help = "Index all recipes into ChromaDB for the RAG chatbot (requires OPENAI_API_KEY)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing collection and re-index from scratch.",
        )

    def handle(self, *args, **options):
        from chatbot.rag import (
            build_gemini_embedding_fn,
            build_openai_embedding_fn,
            get_chroma_collection,
            index_recipes_into_chroma,
            _use_gemini,
        )

        # Prefer Gemini (free tier), then OpenAI
        use_gemini = _use_gemini()
        if use_gemini:
            embedding_fn = build_gemini_embedding_fn()  # RETRIEVAL_DOCUMENT for indexing
            key_name = "GEMINI_API_KEY"
        else:
            embedding_fn = build_openai_embedding_fn()
            key_name = "OPENAI_API_KEY"

        if not embedding_fn:
            self.stderr.write(
                self.style.ERROR(
                    f"{key_name} (or OPENAI_API_KEY) is not set. Set it in .env or environment."
                )
            )
            return

        persist_dir = getattr(settings, "CHROMA_PERSIST_DIR", None)
        if not persist_dir:
            persist_dir = os.path.join(settings.BASE_DIR, "chroma_recipe_db")
        os.makedirs(persist_dir, exist_ok=True)

        try:
            import chromadb
        except ImportError:
            self.stderr.write(self.style.ERROR("chromadb is not installed. pip install chromadb"))
            return

        client = chromadb.PersistentClient(
            path=persist_dir,
            settings=chromadb.config.Settings(anonymized_telemetry=False),
        )

        if options["clear"]:
            try:
                client.delete_collection("recipe_docs")
                self.stdout.write(self.style.WARNING("Deleted existing collection 'recipe_docs'."))
            except Exception:
                pass

        collection = client.get_or_create_collection(
            name="recipe_docs",
            metadata={"description": "Recipe documents for RAG"},
        )

        count = index_recipes_into_chroma(collection, embedding_fn, None)
        provider = "Gemini" if use_gemini else "OpenAI"
        self.stdout.write(
            self.style.SUCCESS(f"Indexed {count} recipes into ChromaDB at {persist_dir} (using {provider}).")
        )
