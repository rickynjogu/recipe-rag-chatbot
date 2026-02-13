from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
import uuid
from .models import ChatHistory


class ChatView(View):
    """Main chat interface"""
    template_name = "chatbot/chat.html"

    def get(self, request):
        # Generate or get session ID
        session_id = request.session.get("chat_session_id", str(uuid.uuid4()))
        request.session["chat_session_id"] = session_id
        
        # Get recent chat history
        recent_chats = ChatHistory.objects.filter(
            session_id=session_id
        ).order_by("-created_at")[:10]
        
        context = {
            "session_id": session_id,
            "recent_chats": recent_chats,
        }
        return render(request, self.template_name, context)


@method_decorator(csrf_exempt, name="dispatch")
class ChatAPIView(View):
    """API endpoint for chatbot interactions"""
    
    def post(self, request):
        """Handle chat messages"""
        try:
            data = json.loads(request.body)
            message = data.get("message", "")
            session_id = data.get("session_id", str(uuid.uuid4()))
            
            if not message:
                return JsonResponse({"error": "Message is required"}, status=400)
            
            from chatbot.rag import get_rag_response
            response = get_rag_response(message, request=request)
            
            # Save chat history
            ChatHistory.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session_id=session_id,
                message=message,
                response=response["answer"],
                retrieved_docs=response.get("retrieved_docs", []),
                confidence_score=response.get("confidence"),
            )

            return JsonResponse({
                "response": response["answer"],
                "retrieved_docs": response.get("retrieved_docs", []),
                "confidence": response.get("confidence"),
            })
            
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

class ChatHistoryView(View):
    """View chat history"""
    template_name = "chatbot/history.html"

    def get(self, request):
        session_id = request.session.get("chat_session_id")
        chats = ChatHistory.objects.filter(session_id=session_id).order_by("-created_at") if session_id else []
        
        context = {
            "chats": chats,
        }
        return render(request, self.template_name, context)
