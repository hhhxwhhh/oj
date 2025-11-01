from django.conf.urls import url,include
from . import views

urlpatterns = [
    url(r"^admin/ai_model/?$", views.AIModelAdminAPI.as_view(), name="ai_model_admin_api"),
    url(r"^admin/ai_model/list/?$", views.AIModelListAdminAPI.as_view(), name="ai_model_list_admin_api"),
    
    url(r"^ai/models/?$", views.AIModelListAPI.as_view(), name="ai_model_list_api"), 
    url(r"^ai/learning_path/?$", views.AILearningPathAPI.as_view(), name="ai_learning_path_api"),
    url(r"^ai/learning_path/(?P<path_id>\d+)/?$", views.AILearningPathDetailAPI.as_view(), name="ai_learning_path_detail_api"),
    url(r"^ai/learning_path/node/(?P<node_id>\d+)/?$", views.AILearningPathNodeAPI.as_view(), name="ai_learning_path_node_api"),
    
    url(r"^ai/knowledge_point/?$", views.KnowledgePointAPI.as_view(), name="knowledge_point_api"),
    url(r"^ai/knowledge_point/recommend/?$", views.KnowledgePointRecommendationAPI.as_view(), name="knowledge_point_recommendation_api"),
    url(r"^ai/knowledge_point/manage/?$", views.KnowledgePointManagementAPI.as_view(), name="knowledge_point_manage_api"),
    url(r"^ai/knowledge_point/graph/?$", views.KnowledgePointGraphAPI.as_view(), name="knowledge_point_graph_api"),  
    url(r"^ai/knowledge_graph/recommend/?$", views.KnowledgeGraphAPI.as_view(), name="knowledge_graph_recommend_api"),
    url(r"^ai/knowledge_point/problems/?$", views.KnowledgePointProblemsAPI.as_view(), name="knowledge_point_problems_api"),
    url(r"^ai/knowledge_point/initialize/?$", views.KnowledgePointInitializationAPI.as_view(), name="knowledge_point_initialize_api"),
        
    url(r"^ai/singleknowledge_point/?$", views.SingleKnowledgePointAPI.as_view(), name="single_knowledge_point_api"),

    url(r"^ai/conversation/?$", views.AIConversationAPI.as_view(), name="ai_conversation_api"),
    url(r"^ai/message/?$", views.AIMessageAPI.as_view(), name="ai_message_api"),
    url(r"^ai/conversations/?$", views.AIConversationListAPI.as_view(), name="ai_conversation_list_api"),
    url(r"^ai/code/diagnose/?$", views.AICodeDiagnosisAPI.as_view(), name="ai_code_diagnosis_api"),

    url(r"^ai/ability/assess/?$", views.AIProgrammingAbilityAPI.as_view(), name="ai_programming_ability_assess"),
    url(r"^ai/ability/report/?$", views.AIProgrammingAbilityAPI.as_view(), name="ai_programming_ability_report"),
    url(r"^ai/ability/compare/?$", views.AIAbilityComparisonAPI.as_view(), name="ai_ability_comparison"),

    
    url(r"^ai/code/explain/?$", views.AICodeExplanationAPI.as_view(), name="ai_code_explanation_api"),
    url(r"^ai/problem/solution/?$", views.AIProblemSolutionAPI.as_view(), name="ai_problem_solution_api"),
    url(r"^ai/code/review/?$", views.AICodeReviewAPI.as_view(), name="ai_code_review_api"),
    url(r"^ai/submission/diagnose/?$", views.AIDiagnoseSubmissionAPI.as_view(), name="ai_submission_diagnosis_api"),
    url(r"^ai/problems/recommend/?$", views.AIRecommendProblemsAPI.as_view(), name="ai_problem_recommendation_api"),
    url(r"^ai/recommendation/feedback/?$", views.AIRecommendationFeedbackAPI.as_view(), name="ai_recommendation_feedback_api"),
    url(r"^ai/next_problem/?$", views.AINextProblemRecommendationAPI.as_view(), name="ai_next_problem_recommendation_api"),
    url(r"^ai/code/suggestion/?$", views.AIRealTimeSuggestionAPI.as_view(), name="ai_real_time_suggestion_api"),
    url(r"^ai/code/autocomplete/?$", views.AICodeAutoCompleteAPI.as_view(), name="ai_code_autocomplete_api"),
    url(r"^ai/code/realtime_diagnosis/?$", views.AIRealTimeDiagnosisAPI.as_view(), name="ai_real_time_diagnosis_api"),

    url(r"^ai/feedback/?$", views.AIFeedbackAPI.as_view(), name="ai_feedback_api"),
    url(r"^ai/problem/generate/?$", views.AIProblemGenerationAPI.as_view(), name="ai_problem_generation_api"),
    url(r"^ai/nlp_analysis/?$", views.AINLPAnalysisAPI.as_view(), name="ai_nlp_analysis_api"),

    url(r"^ai/user-ability-trend/?$", views.AIUserAbilityTrendAPI.as_view(), name="user_ability_trend_api"),

    url(r"^ollama/", include("ai.ollama.urls")),
]