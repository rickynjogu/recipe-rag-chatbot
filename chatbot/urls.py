from django.urls import path
from . import views

app_name = "chatbot"

urlpatterns = [
    path("chat/", views.ChatView.as_view(), name="chat"),
    path("api/chat/", views.ChatAPIView.as_view(), name="chat_api"),
    path("history/", views.ChatHistoryView.as_view(), name="chat_history"),
]
