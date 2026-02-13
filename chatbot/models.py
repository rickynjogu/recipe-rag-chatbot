from django.db import models
from django.contrib.auth.models import User


class ChatHistory(models.Model):
    """Store chat conversations for the RAG chatbot"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_histories", null=True, blank=True)
    session_id = models.CharField(max_length=255, help_text="Unique session identifier")
    message = models.TextField(help_text="User's message")
    response = models.TextField(help_text="Bot's response")
    created_at = models.DateTimeField(auto_now_add=True)
    
    # RAG-related fields
    retrieved_docs = models.JSONField(
        default=list,
        blank=True,
        help_text="List of recipe IDs or content retrieved for context"
    )
    confidence_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Confidence score of the response (0-1)"
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["session_id", "-created_at"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        return f"Chat {self.session_id[:8]}... - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
