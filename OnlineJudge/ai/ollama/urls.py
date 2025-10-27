from django.conf.urls import url
from .views import OllamaChatAPI,OllamaCodeCompletionAPI,OllamaModelListAPI

urlpatterns = [
    url(r"^ollama/code/complete/?$", OllamaCodeCompletionAPI.as_view(), name="ollama_code_completion_api"),
    url(r"^ollama/models/?$", OllamaModelListAPI.as_view(), name="ollama_model_list_api"),
    url(r"^ollama/chat/?$", OllamaChatAPI.as_view(), name="ollama_chat_api"),
]