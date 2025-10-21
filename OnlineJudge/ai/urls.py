from django.conf.urls import url
from . import views

urlpatterns = [
    url(r"^admin/ai_model/?$", views.AIModelAdminAPI.as_view(), name="ai_model_admin_api"),
    url(r"^admin/ai_model/list/?$", views.AIModelListAdminAPI.as_view(), name="ai_model_list_admin_api"),
    
    url(r"^ai/models/?$", views.AIModelListAPI.as_view(), name="ai_model_list_api"), 
    url(r"^ai/learning_path/?$", views.AILearningPathAPI.as_view(), name="ai_learning_path_api"),
    url(r"^ai/learning_path/(?P<path_id>\d+)/?$", views.AILearningPathDetailAPI.as_view(), name="ai_learning_path_detail_api"),
    url(r"^ai/learning_path/node/(?P<node_id>\d+)/?$", views.AILearningPathNodeAPI.as_view(), name="ai_learning_path_node_api"),
    
    url(r"^ai/conversation/?$", views.AIConversationAPI.as_view(), name="ai_conversation_api"),
    url(r"^ai/message/?$", views.AIMessageAPI.as_view(), name="ai_message_api"),
    url(r"^ai/conversations/?$", views.AIConversationListAPI.as_view(), name="ai_conversation_list_api"),
    url(r"^ai/code/diagnosis/?$", views.AICodeDiagnosisAPI.as_view(), name="ai_code_diagnosis_api"),
    
    url(r"^ai/code/explain/?$", views.AICodeExplanationAPI.as_view(), name="ai_code_explanation_api"),
    url(r"^ai/problem/solution/?$", views.AIProblemSolutionAPI.as_view(), name="ai_problem_solution_api"),
    url(r"^ai/code/review/?$", views.AICodeReviewAPI.as_view(), name="ai_code_review_api"),
    url(r"^ai/submission/diagnose/?$", views.AIDiagnoseSubmissionAPI.as_view(), name="ai_submission_diagnosis_api"),
    url(r"^ai/problems/recommend/?$", views.AIRecommendProblemsAPI.as_view(), name="ai_problem_recommendation_api"),
    url(r"^ai/recommendation/feedback/?$", views.AIRecommendationFeedbackAPI.as_view(), name="ai_recommendation_feedback_api"),
    url(r"^ai/next_problem/?$", views.AINextProblemRecommendationAPI.as_view(), name="ai_next_problem_recommendation_api"),
    url(r"^ai/feedback/?$", views.AIFeedbackAPI.as_view(), name="ai_feedback_api"),
]