from django.contrib import admin
from .models import ChatHistory


@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    list_display = ["session_id", "user", "created_at", "confidence_score"]
    list_filter = ["created_at", "user"]
    search_fields = ["message", "response", "session_id", "user__username"]
    readonly_fields = ["created_at"]
    
    fieldsets = (
        ("Chat Information", {
            "fields": ("user", "session_id", "created_at")
        }),
        ("Messages", {
            "fields": ("message", "response")
        }),
        ("RAG Metadata", {
            "fields": ("retrieved_docs", "confidence_score")
        }),
    )
