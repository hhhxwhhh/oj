from django.conf.urls import url
from . import views

urlpatterns = [
    url(r"^api/admin/ai_model/?$", views.AIModelAdminAPI.as_view(), name="ai_model_admin_api"),
    url(r"^api/admin/ai_model/list/?$", views.AIModelListAdminAPI.as_view(), name="ai_model_list_admin_api"),
    
    url(r"^api/ai_chat/conversation/?$", views.AIConversationAPI.as_view(), name="ai_conversation_api"),
    url(r"^api/ai_chat/message/?$", views.AIMessageAPI.as_view(), name="ai_message_api"),
    url(r"^api/ai_chat/conversations/?$", views.AIConversationListAPI.as_view(), name="ai_conversation_list_api"),
    
    url(r"^api/ai_code_explanation/?$", views.AICodeExplanationAPI.as_view(), name="ai_code_explanation_api"),
    url(r"^api/ai_problem_solution/?$", views.AIProblemSolutionAPI.as_view(), name="ai_problem_solution_api"),
    url(r"^api/ai_code_review/?$", views.AICodeReviewAPI.as_view(), name="ai_code_review_api"),
    
    url(r"^api/ai_feedback/?$", views.AIFeedbackAPI.as_view(), name="ai_feedback_api"),
]

