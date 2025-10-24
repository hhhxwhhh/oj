from django.shortcuts import render
from utils.api import serializers
import openai 
import requests
from django.db import transaction,models
# Create your views here.
from utils.api import APIView,validate_serializer
from account.decorators import login_required
from .models import AIModel,AIConversation,AIMessage,AICodeReview,AIFeedback,KnowledgePoint,AIUserLearningPath
from .serializers import (
    AIModelSerializer, CreateAIModelSerializer,
    AIConversationSerializer, CreateAIConversationSerializer,
    AIMessageSerializer, CreateAIMessageSerializer,
    AICodeReviewSerializer, CreateAICodeReviewSerializer,
    AIFeedbackSerializer, CreateAIFeedbackSerializer,
    CreateAIRecommendationFeedbackSerializer,
    AIRecommendationFeedbackSerializer,AIProblemGenerationSerializer,
    AIAbilityDimensionSerializer,AIUserAbilityDetailSerializer,AIProgrammingAbilitySerializer
)
from .service import( 
    AIService,AIRecommendationService,AILearningPathService,
    AICodeDiagnosisService,KnowledgePointService ,AIProblemGenerationService,
    AIProgrammingAbilityService,AIProgrammingAbility)
from submission.models import Submission
from problem.models import Problem
import logging
logger = logging.getLogger(__name__)
class AIModelAdminAPI(APIView):
    def get(self,request):
        model_id=request.GET.get("id")
        if not model_id:
            return self.error("Parameter error")
        try:
            ai_model=AIModel.objects.get(id=model_id)
            return self.success(AIModelSerializer(ai_model).data)
        except AIModel.DoesNotExist:
            return self.error("Model not found")
        except Exception as e:
            return self.error(str(e))
        
    @validate_serializer(CreateAIModelSerializer)
    def post(self,request):
        data=request.data
        try:
            ai_model = AIModel.objects.create(
                name=data["name"],
                provider=data["provider"],
                api_key=data["api_key"],
                model=data["model"],
                is_active=data["is_active"],
                config=data["config"]
            )
            return self.success(AIModelSerializer(ai_model).data)
        except Exception as e:
            return self.error(str(e))
    
    def put(self,request):
        data=request.data
        model_id=data.get("id")
        if not model_id:
            return self.error("Parameter error")
        try:
            ai_model = AIModel.objects.get(id=model_id)
            ai_model.name = data["name"]
            ai_model.provider = data["provider"]
            ai_model.api_key = data["api_key"]
            ai_model.model = data["model"]
            ai_model.is_active = data["is_active"]
            ai_model.config = data["config"]
            ai_model.save()
            return self.success(AIModelSerializer(ai_model).data)
        except AIModel.DoesNotExist:
            return self.error("Model not found")
        except Exception as e:
            return self.error(str(e))
        
    def delete(self,request):
        model_id = request.GET.get("id")
        if not model_id:
            return self.error("Parameter error")
        
        try:
            ai_model = AIModel.objects.get(id=model_id)
            ai_model.delete()
            return self.success()
        except AIModel.DoesNotExist:
            return self.error("AI model does not exist")
        except Exception as e:
            return self.error(str(e))
        

class AIModelListAPI(APIView):
    @login_required
    def get(self,request):
        try:
            ai_models=AIModel.objects.filter(is_active=True)
            return self.success(AIModelSerializer(ai_models,many=True).data)
        except Exception as e:
            return self.error(str(e))
        

class AIModelListAdminAPI(APIView):
    def get(self,request):
        try:
            ai_models=AIModel.objects.all()
            return self.success(AIModelSerializer(ai_models,many=True).data)
        except Exception as e:
            return self.error(str(e))
    
class AIConversationAPI(APIView):
    @login_required
    @validate_serializer(CreateAIConversationSerializer)
    def post(self,request):
        data=request.data
        user=request.user
        try:
            conversation=AIConversation.objects.create(
                user=user,
                title=data['title']
            )
            return self.success(AIConversationSerializer(conversation).data)
        except Exception as e:
            return self.error(str(e))
    

class AIConversationListAPI(APIView):
    @login_required
    def get(self, request):
        user = request.user
        try:
            conversations = AIConversation.objects.filter(user=user).order_by("-update_time")
            return self.success(AIConversationSerializer(conversations, many=True).data)
        except Exception as e:
            return self.error(str(e))
    

class AIMessageAPI(APIView):
    @login_required
    def get(self,request):
        conversation_id = request.GET.get("conversation_id")
        if not conversation_id:
            return self.error("Parameter error")
        
        try:
            messages = AIMessage.objects.filter(conversation_id=conversation_id).order_by("create_time")
            return self.success(AIMessageSerializer(messages, many=True).data)
        except Exception as e:
            return self.error(str(e))
        
    @login_required
    @validate_serializer(CreateAIMessageSerializer)
    def post(self,request):
        data = request.data
        user = request.user
        try:
            user_message = AIMessage.objects.create(
                conversation_id=data["conversation_id"],
                role=data.get("role", "user"),
                content=data["content"]
            )
            active_model_exists = AIModel.objects.filter(is_active=True).exists()
            if active_model_exists:
                messages = AIService.get_chat_history(data["conversation_id"])
                if "model_id" in data and data['model_id']:
                    try:
                        ai_model=AIModel.objects.get(id=data['model_id'],is_active=True)
                        ai_response = AIService.call_ai_model(messages,ai_model)
                    except AIModel.DoesNotExist:
                        ai_response=AIService.call_ai_model(messages)
                else:
                    ai_response = AIService.call_ai_model(messages)
                ai_message = AIMessage.objects.create(
                    conversation_id=data["conversation_id"],
                    role="assistant",
                    content=ai_response
                )
                return self.success({
                    "user_message": AIMessageSerializer(user_message).data,
                    "ai_message": AIMessageSerializer(ai_message).data
                })
            else:
                # 如果没有激活的模型，返回只有用户消息的响应
                return self.success({
                    "user_message": AIMessageSerializer(user_message).data,
                    "ai_message": None
                })
        except Exception as e:
            return self.error(str(e))
        
class AICodeExplanationAPI(APIView):
    @login_required
    def post(self,request):
        code = request.data.get("code")
        language = request.data.get("language")
        logger.info(f"Received code explanation request: language={language}, code_length={len(code) if code else 0}")
        
        if not code or not language:
            logger.error("Code explanation failed: Missing code or language parameter")
            return self.error("Parameter error")
        try:
            # 检查是否有激活的AI模型
            active_model_exists = AIModel.objects.filter(is_active=True).exists()
            logger.info(f"Active model exists: {active_model_exists}")
            
            if not active_model_exists:
                logger.error("Code explanation failed: No active AI model found")
                return self.error("No active AI model found. Please configure an AI model first.")
            
            explanation = AIService.generate_code_explanation(code, language)
            logger.info(f"Code explanation generated successfully, length={len(explanation) if explanation else 0}")
            return self.success({"explanation": explanation})
        except Exception as e:
            logger.error(f"Code explanation failed with error: {str(e)}", exc_info=True)
            return self.error(f"Failed to generate code explanation: {str(e)}")
        

class AIProblemSolutionAPI(APIView):
    @login_required
    def post(self, request):
        problem_id = request.data.get("problem_id")
        if not problem_id:
            return self.error("Parameter error")
        try:
            # 检查是否有激活的AI模型
            active_model_exists = AIModel.objects.filter(is_active=True).exists()
            if not active_model_exists:
                return self.error("No active AI model found. Please configure an AI model first.")
            solution = AIService.generate_problem_solution(problem_id)
            return self.success({"solution": solution})
        except Exception as e:
            return self.error(str(e))

class AICodeReviewAPI(APIView):
    @login_required
    @validate_serializer(CreateAICodeReviewSerializer)
    def post(self, request):
        data = request.data
        user = request.user
        
        try:
            # 检查是否有激活的AI模型
            active_model_exists = AIModel.objects.filter(is_active=True).exists()
            if not active_model_exists:
                return self.error("No active AI model found. Please configure an AI model first.")
            review_result = AIService.review_code(data["problem_id"], data["code"], data["language"])
            code_review = AICodeReview.objects.create(
                user=user,
                problem_id=data["problem_id"],
                code=data["code"],
                language=data["language"],
                review_result={"review": review_result}
            )
            return self.success({
                "review_result": review_result,
                "review_id": code_review.id
            })
        except Exception as e:
            return self.error(str(e))
        
class AIFeedbackAPI(APIView):
    @login_required
    @validate_serializer(CreateAIFeedbackSerializer)
    def post(self, request):
        data = request.data
        user = request.user
        try:
            feedback = AIFeedback.objects.create(
                user=user,
                message_id=data["message_id"],
                rating=data["rating"],
                comment=data["comment"]
            )
            return self.success(AIFeedbackSerializer(feedback).data)
        except Exception as e:
            return self.error(str(e))
        
class AIDiagnoseSubmissionAPI(APIView):
    @login_required
    def post(self,request):
        submission_id=request.data.get("submission_id")
        if not submission_id:
            return self.error("Parameter error")
        try:
            # 检查是否有激活的AI模型
            active_model_exists = AIModel.objects.filter(is_active=True).exists()
            if not active_model_exists:
                return self.error("No active AI model found. Please configure an AI model first.")
            diagnosis=AIService.diagnose_submission(submission_id)
            return self.success({"diagnosis":diagnosis})
        except Exception as e:
            return self.error(str(e))
        

class AIRecommendProblemsAPI(APIView):
    @login_required
    def get(self, request):
        user = request.user
        count = int(request.GET.get("count", 10))
        
        try:
            active_model_exists = AIModel.objects.filter(is_active=True).exists()
            recommendations = AIRecommendationService.recommend_problems(user.id, count)
            result = []
            for problem_id, score, reason in recommendations:
                try:
                    problem = Problem.objects.prefetch_related('tags').get(id=problem_id)
                    tags = list(problem.tags.values_list('name', flat=True))
                    result.append({
                        "problem_id": problem.id,
                        "problem_display_id": problem._id,
                        "title": problem.title,
                        "difficulty": problem.difficulty,
                        "score": score,
                        "reason": reason,
                        "acceptance_rate": problem.accepted_number / problem.submission_number if problem.submission_number > 0 else 0,
                        "tags": tags
                    })
                except Problem.DoesNotExist:
                    continue
            
            return self.success(result)
        except Exception as e:
            logger.error(f"Recommendation failed: {str(e)}", exc_info=True)
            return self.error("推荐失败，请稍后重试")
        
class AIRecommendationFeedbackAPI(APIView):
    @login_required
    @validate_serializer(CreateAIRecommendationFeedbackSerializer)
    def post(self, request):
        data = request.data
        user = request.user
        try:
            from .models import AIRecommendation, AIRecommendationFeedback
            
            # 获取推荐记录
            try:
                recommendation = AIRecommendation.objects.get(id=data["recommendation_id"])
            except AIRecommendation.DoesNotExist:
                return self.error("Recommendation not found")
            
            # 创建反馈
            feedback = AIRecommendationFeedback.objects.create(
                user=user,
                problem=recommendation.problem,
                recommendation=recommendation,
                accepted=data['accepted'],
                solved=data.get("solved", False),
                feedback=data.get("feedback", ""),
            )
            
            # 处理反馈以优化推荐算法
            from .service import KnowledgePointService
            KnowledgePointService.process_recommendation_feedback(
                user_id=user.id,
                recommendation_id=data["recommendation_id"],
                accepted=data['accepted'],
                solved=data.get("solved", False),
                feedback_text=data.get("feedback", "")
            )
            
            return self.success(AIRecommendationFeedbackSerializer(feedback).data)
        except Exception as e:
            logger.error(f"Failed to create recommendation feedback: {str(e)}")
            return self.error(str(e))

class AICodeReviewAPI(APIView):
    @login_required
    def post(self,request):
        code=request.data.get("code")
        language=request.data.get("language")
        problem_id=request.data.get("problem_id")
        if not code or not language or not problem_id:
            return self.error("Parameter error")
        try:
            active_model_exists=AIModel.objects.filter(is_active=True).exists()
            if not active_model_exists:
                return self.error("No active AI model found. Please configure an AI model first.")
            
            review_result=AIService.review_code(problem_id,code,language)

            code_review=AICodeReview.objects.create(
                user=request.user,
                problem_id=problem_id,
                code=code,
                language=language,
                review_result={"review":review_result},
            )
            return self.success({
                "review_result":review_result,
                "review_id":code_review.id,
            })
        except Exception as e:
            return self.error(str(e))


class AINextProblemRecommendationAPI(APIView):
    @login_required
    def post(self, request):
        problem_id = request.data.get("problem_id")
        submission_result = request.data.get("submission_result", "")
        user = request.user
        
        try:
            # 检查是否有激活的AI模型
            active_model = AIModel.objects.filter(is_active=True).first()
            if not active_model:
                return self.error("No active AI model found. Please configure an AI model first.")
            
            # 检查AI模型配置是否有效
            if not active_model.api_key or not active_model.model:
                return self.error("AI model configuration is incomplete.")
            
            # 获取推荐题目（现在返回三个）
            recommendation_results = AIRecommendationService.recommend_next_problem(
                user.id, problem_id, submission_result
            )
            
            # 从推荐结果中随机选择一个，增加多样性
            import random
            if recommendation_results and len(recommendation_results) > 0:
                selected_recommendation = random.choice(recommendation_results)
                next_problem_id, score, reason = selected_recommendation
            else:
                return self.success([])
            
            # 格式化推荐结果
            result = []
            try:
                problem = Problem.objects.prefetch_related('tags').get(id=next_problem_id)
                # 获取题目的标签
                tags = list(problem.tags.values_list('name', flat=True))
                
                result.append({
                    "id": problem.id,
                    "_id": problem._id,
                    "title": problem.title,
                    "difficulty": problem.difficulty,
                    "score": score,
                    "reason": reason,
                    "description": problem.description,
                    "submission_number": problem.submission_number,
                    "accepted_number": problem.accepted_number,
                    "tags": tags
                })
            except Problem.DoesNotExist:
                pass
            
            return self.success(result)
        except Exception as e:
            logger.error(f"Next problem recommendation failed: {str(e)}", exc_info=True)
            return self.error("推荐失败，请稍后重试")

class AILearningPathAPI(APIView):
    @login_required
    def post(self, request):
        user = request.user
        goal = request.data.get("goal", "general")
        level = request.data.get("level", None)
        
        try:
            # 检查是否有激活的AI模型
            active_model_exists = AIModel.objects.filter(is_active=True).exists()
            if not active_model_exists:
                return self.error("No active AI model found. Please configure an AI model first.")
            
            # 生成学习路径
            path_data = AILearningPathService.generate_learning_path(
                user_id=user.id,
                goal=goal,
                current_level=level
            )
            
            # 保存学习路径到数据库
            learning_path = AILearningPathService.save_learning_path(user.id, path_data)
            
            # 返回结果
            from .serializers import AIUserLearningPathSerializer
            return self.success(AIUserLearningPathSerializer(learning_path).data)
        except Exception as e:
            logger.error(f"Generate learning path failed: {str(e)}")
            return self.error(f"Failed to generate learning path: {str(e)}")
    
    @login_required
    def get(self, request):
        user = request.user
        try:
            paths = AILearningPathService.get_user_learning_paths(user.id)
            from .serializers import AIUserLearningPathSerializer
            return self.success(AIUserLearningPathSerializer(paths, many=True).data)
        except Exception as e:
            logger.error(f"Get learning paths failed: {str(e)}")
            return self.error("Failed to get learning paths")
        
class AILearningPathDetailAPI(APIView):
    @login_required
    def get(self, request, path_id):
        user = request.user
        try:
            path, nodes = AILearningPathService.get_learning_path_detail(path_id, user.id)
            from .serializers import AIUserLearningPathDetailSerializer
            serializer = AIUserLearningPathDetailSerializer(path)
            data = serializer.data
            
            # 确保节点数据被正确序列化
            from .serializers import AIUserLearningPathNodeSerializer
            node_serializer = AIUserLearningPathNodeSerializer(nodes, many=True)
            data['nodes'] = node_serializer.data
            
            return self.success(data)
        except AIUserLearningPath.DoesNotExist:
            return self.error("Learning path not found")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Get learning path detail failed: {str(e)}", exc_info=True)
            return self.error("Failed to get learning path detail")

class AILearningPathNodeAPI(APIView):
    @login_required
    def put(self, request, node_id):
        user = request.user
        status = request.data.get("status")
        
        if not status or status not in ["pending", "in_progress", "completed"]:
            return self.error("Invalid status")
        
        try:
            node = AILearningPathService.update_node_status(node_id, user.id, status)
            from .serializers import AIUserLearningPathNodeSerializer
            return self.success(AIUserLearningPathNodeSerializer(node).data)
        except Exception as e:
            logger.error(f"Update node status failed: {str(e)}")
            return self.error("Failed to update node status")
class AICodeDiagnosisAPI(APIView):
    @login_required
    def post(self, request):
        """
        为失败的提交提供代码诊断和修复建议
        """
        user = request.user
        submission_id = request.data.get("submission_id")
        
        try:
            # 获取提交信息
            submission = Submission.objects.select_related('problem').get(id=submission_id)
            
            # 检查是否是当前用户的提交
            if submission.user_id != user.id:
                return self.error("Permission denied")
            
            # 检查提交结果
            if submission.result == 0:  # 0表示Accepted
                return self.error("Code is already accepted")
            
            # 获取激活的AI模型
            active_model = AIModel.objects.filter(is_active=True).first()
            if not active_model:
                return self.error("No active AI model found")
            
            # 生成诊断信息
            diagnosis_result = AICodeDiagnosisService.diagnose_submission(submission)
            
            return self.success(diagnosis_result)
        except Submission.DoesNotExist:
            return self.error("Submission not found")
        except Exception as e:
            logger.error(f"Code diagnosis failed: {str(e)}")
            return self.error(msg="Failed to diagnose code", err=str(e))
class KnowledgePointAPI(APIView):
    @login_required
    def get(self, request):
        """
        获取用户知识点掌握情况
        """
        try:
            user = request.user
            knowledge_states = KnowledgePointService.get_user_knowledge_state(user.id)
            
            result = []
            for name, state in knowledge_states.items():
                # 确保掌握程度值精度正确
                proficiency_level = state.proficiency_level
                if not isinstance(proficiency_level, (int, float)):
                    proficiency_level = 0.0
                else:
                    # 修复浮点数精度问题
                    proficiency_level = round(float(proficiency_level), 4)
                
                result.append({
                    'knowledge_point': name,
                    'proficiency_level': proficiency_level,
                    'correct_attempts': state.correct_attempts,
                    'total_attempts': state.total_attempts,
                    'last_updated': state.last_updated.isoformat() if state.last_updated else None
                })
            
            return self.success(result)
        except Exception as e:
            logger.error(f"Failed to get user knowledge state: {str(e)}")
            return self.error("Failed to get knowledge state")
    
    @login_required
    def post(self, request):
        """
        获取知识点学习建议
        """
        logger.info("KnowledgePointAPI POST request received")
        try:
            user = request.user
            count = request.data.get("count", 5)
            recommendations = KnowledgePointService.get_knowledge_recommendations(user.id, count)
            logger.info(f"Returning recommendations for user {user.id}")
            return self.success({"data": recommendations})
        except Exception as e:
            logger.error(f"Failed to get knowledge recommendations: {str(e)}")
            return self.error("Failed to get recommendations")

class KnowledgePointManagementAPI(APIView):
    def post(self, request):
        """
        从题目标签创建知识点
        """
        try:
            KnowledgePointService.create_knowledge_points_from_tags()
            return self.success("Knowledge points created successfully")
        except Exception as e:
            logger.error(f"Failed to create knowledge points: {str(e)}")
            return self.error("Failed to create knowledge points")
        
    def put(self, request):
        """
        更新知识点信息
        """
        try:
            knowledge_point_id = request.data.get("id")
            name = request.data.get("name")
            description = request.data.get("description")
            category = request.data.get("category")
            difficulty = request.data.get("difficulty")
            parent_points = request.data.get("parent_points", [])
            related_problems = request.data.get("related_problems", [])
            
            knowledge_point = KnowledgePoint.objects.get(id=knowledge_point_id)
            
            # 更新知识点信息
            if name:
                knowledge_point.name = name
            if description:
                knowledge_point.description = description
            if category:
                knowledge_point.category = category
            if difficulty:
                knowledge_point.difficulty = difficulty
                
            knowledge_point.save()
            
            # 更新前置知识点关联
            if parent_points:
                parent_kps = KnowledgePoint.objects.filter(name__in=parent_points)
                knowledge_point.parent_points.set(parent_kps)
            
            # 更新相关题目关联
            if related_problems:
                from problem.models import Problem
                problems = Problem.objects.filter(id__in=related_problems)
                knowledge_point.related_problems.set(problems)
            
            return self.success({
                "id": knowledge_point.id,
                "name": knowledge_point.name,
                "description": knowledge_point.description,
                "category": knowledge_point.category,
                "difficulty": knowledge_point.difficulty
            })
        except KnowledgePoint.DoesNotExist:
            return self.error("Knowledge point not found")
        except Exception as e:
            logger.error(f"Failed to update knowledge point: {str(e)}")
            return self.error("Failed to update knowledge point")

class KnowledgePointRecommendationAPI(APIView):
    @login_required
    def post(self, request):
        """
        获取知识点学习建议
        """
        logger.info("KnowledgePointRecommendationAPI POST request received")
        try:
            user = request.user
            count = request.data.get("count", 5)
            recommendations = KnowledgePointService.get_knowledge_recommendations(user.id, count)
            logger.info(f"Returning recommendations for user {user.id}")
            return self.success({"data": recommendations})
        except Exception as e:
            logger.error(f"Failed to get knowledge recommendations: {str(e)}")
            return self.error("Failed to get recommendations")
        
class AIRealTimeSuggestionAPI(APIView):
    @login_required
    def post(self, request):
        """
        生成实时编程建议
        """
        user = request.user
        code = request.data.get("code", "")
        language = request.data.get("language", "")
        cursor_position = request.data.get("cursor_position", 0)
        problem_id = request.data.get("problem_id")
        
        try:
            # 检查是否有激活的AI模型
            active_model_exists = AIModel.objects.filter(is_active=True).exists()
            if not active_model_exists:
                return self.error("No active AI model found. Please configure an AI model first.")
            
            # 生成实时建议
            suggestion_result = AIService.generate_real_time_suggestion(
                code, language, cursor_position, problem_id
            )
            
            return self.success(suggestion_result)
        except Exception as e:
            logger.error(f"Real-time suggestion failed: {str(e)}")
            return self.error("Failed to generate real-time suggestion")
        

class AICodeAutoCompleteAPI(APIView):
    @login_required
    def post(self, request):
        """
        生成代码自动补全建议
        """
        user = request.user
        code = request.data.get("code", "")
        language = request.data.get("language", "")
        prefix = request.data.get("prefix", "")
        problem_id = request.data.get("problem_id")
        
        try:
            # 检查是否有激活的AI模型
            active_model_exists = AIModel.objects.filter(is_active=True).exists()
            if not active_model_exists:
                return self.error("No active AI model found. Please configure an AI model first.")
            
            # 生成自动补全建议
            completion_result = AIService.auto_complete_code(
                code, language, prefix, problem_id
            )
            
            return self.success(completion_result)
        except Exception as e:
            logger.error(f"Code auto completion failed: {str(e)}")
            return self.error("Failed to generate code auto completion")
        

class AIRealTimeDiagnosisAPI(APIView):
    @login_required
    def post(self, request):
        """
        实时诊断代码中的潜在问题
        """
        user = request.user
        code = request.data.get("code", "")
        language = request.data.get("language", "")
        problem_id = request.data.get("problem_id")
        
        try:
            # 检查是否有激活的AI模型
            active_model_exists = AIModel.objects.filter(is_active=True).exists()
            if not active_model_exists:
                return self.error("No active AI model found. Please configure an AI model first.")
            
            # 实时诊断代码
            diagnosis_result = AICodeDiagnosisService.diagnose_code_in_real_time(
                code, language, problem_id
            )
            
            return self.success(diagnosis_result)
        except Exception as e:
            logger.error(f"Real-time diagnosis failed: {str(e)}")
            return self.error("Failed to diagnose code in real-time")
        
class KnowledgePointGraphAPI(APIView):
    @login_required
    def get(self, request):
        """
        获取知识点图谱数据
        """
        try:
            # 获取所有知识点
            knowledge_points = KnowledgePoint.objects.all()
            
            # 构建节点数据
            nodes = []
            # 构建边数据
            edges = []
            
            # 节点ID映射，用于构建边
            node_id_map = {}
            
            # 构建节点数据
            for i, kp in enumerate(knowledge_points):
                node_id_map[kp.id] = i
                nodes.append({
                    'id': i,
                    'name': kp.name,
                    'category': kp.category,
                    'difficulty': kp.difficulty,
                    'description': kp.description,
                    'size': 20 + kp.related_problems.count() * 2,  
                    'symbolSize': 20 + kp.related_problems.count() * 2,
                    'value': kp.weight  # 使用权重作为节点值
                })
            
            # 构建边数据（前置知识点关系）
            for kp in knowledge_points:
                source_id = node_id_map[kp.id]
                for parent_point in kp.parent_points.all():
                    if parent_point.id in node_id_map:
                        target_id = node_id_map[parent_point.id]
                        edges.append({
                            'source': source_id,
                            'target': target_id,
                            'relation': '依赖',
                            'lineStyle': {
                                'width': 2,
                                'type': 'solid'
                            }
                        })
            
            return self.success({
                'nodes': nodes,
                'edges': edges
            })
        except Exception as e:
            logger.error(f"Failed to get knowledge point graph data: {str(e)}")
            return self.error("Failed to get knowledge point graph data")

class SingleKnowledgePointAPI(APIView):
    @login_required
    def get(self, request):
        """
        获取知识点详情
        """
        knowledge_point_id = request.GET.get("id")
        if not knowledge_point_id:
            return self.error("参数错误")
        
        try:
            knowledge_point = KnowledgePoint.objects.get(id=knowledge_point_id)
            from .serializers import KnowledgePointSerializer
            return self.success(KnowledgePointSerializer(knowledge_point).data)
        except KnowledgePoint.DoesNotExist:
            return self.error("知识点不存在")
        except Exception as e:
            return self.error(str(e))



class KnowledgePointProblemsAPI(APIView):
    @login_required
    def get(self, request):
        """
        获取知识点相关的题目列表
        """
        knowledge_point_id = request.GET.get("knowledge_point_id")
        offset = int(request.GET.get("offset", 0))
        limit = int(request.GET.get("limit", 10))
        
        if not knowledge_point_id:
            return self.error("参数错误")
        
        try:
            knowledge_point = KnowledgePoint.objects.get(id=knowledge_point_id)
            problems = knowledge_point.related_problems.all()
            
            # 分页处理
            total = problems.count()
            problems = problems[offset:offset + limit]
            
            # 序列化题目数据
            from problem.serializers import ProblemSerializer
            problem_data = []
            for problem in problems:
                problem_data.append({
                    '_id': problem._id,
                    'title': problem.title,
                    'difficulty': problem.difficulty,
                    'submission_number': problem.submission_number,
                    'accepted_number': problem.accepted_number
                })
            
            return self.success({
                'results': problem_data,
                'total': total
            })
        except KnowledgePoint.DoesNotExist:
            return self.error("知识点不存在")
        except Exception as e:
            return self.error(str(e))
        
class AIProblemGenerationAPI(APIView):
    """
    AI驱动的题目生成API
    """
    @validate_serializer(AIProblemGenerationSerializer)
    def post(self, request):
        # 获取请求参数
        knowledge_point = request.data.get("knowledge_point")
        difficulty = request.data.get("difficulty", "Mid")
        auto_adjust = request.data.get("auto_adjust", True)
        generate_test_cases = request.data.get("generate_test_cases", True)
        test_case_count = request.data.get("test_case_count", 5)
        
        
        # 更严格的验证逻辑
        if not knowledge_point or not isinstance(knowledge_point, str) or len(knowledge_point.strip()) == 0:
            logger.warning(f"Knowledge point validation failed - knowledge_point: {knowledge_point}, "
                          f"type: {type(knowledge_point)}, length: {len(knowledge_point) if knowledge_point else 0}")
            return self.error("知识点不能为空")
        
        try:
            # 检查是否有激活的AI模型
            active_model_exists = AIModel.objects.filter(is_active=True).exists()
            if not active_model_exists:
                return self.error("没有激活的AI模型，请先在AI模型管理中配置并激活一个AI模型")
            
            # 生成题目
            problem_data = AIProblemGenerationService.generate_problem_by_knowledge_point(
                knowledge_point_name=knowledge_point.strip(),
                difficulty=difficulty
            )
            
            # 验证并调整题目
            problem_data = AIProblemGenerationService.validate_and_adjust_problem(
                problem_data, knowledge_point
            )
            
            # 如果需要自动调整难度
            if auto_adjust:
                problem_data = AIProblemGenerationService.auto_adjust_difficulty(
                    problem_data, difficulty
                )
            
            # 如果需要生成测试用例
            if generate_test_cases:
                test_cases = AIProblemGenerationService.generate_test_cases(
                    problem_data, test_case_count
                )
                problem_data["test_cases"] = test_cases
            
            return self.success(problem_data)
        except Exception as e:
            logger.error(f"Generate problem failed: {str(e)}")
            return self.error(f"题目生成失败: {str(e)}")
        

class AIProgrammingAbilityAPI(APIView):
    """
    编程能力评估API
    """
    
    @login_required
    def post(self, request):
        """
        触发用户能力评估
        """
        try:
            user_id = request.user.id
            ability_record = AIProgrammingAbilityService.assess_user_ability(user_id)
            
            # 序列化返回结果
            result = {
                'overall_score': ability_record.overall_score,
                'level': ability_record.get_level_display(),
                'basic_programming_score': ability_record.basic_programming_score,
                'data_structure_score': ability_record.data_structure_score,
                'algorithm_design_score': ability_record.algorithm_design_score,
                'problem_solving_score': ability_record.problem_solving_score,
                'analysis_report': ability_record.analysis_report,
                'last_assessed': ability_record.last_assessed
            }
            
            return self.success(result)
        except Exception as e:
            logger.error(f"Failed to assess programming ability: {str(e)}")
            return self.error("能力评估失败，请稍后重试")

    @login_required
    def get(self, request):
        """
        获取用户能力评估报告
        """
        try:
            user_id = request.user.id
            ability_record = AIProgrammingAbilityService.get_user_ability_report(user_id)
            
            result = {
                'overall_score': ability_record.overall_score,
                'level': ability_record.get_level_display(),
                'basic_programming_score': ability_record.basic_programming_score,
                'data_structure_score': ability_record.data_structure_score,
                'algorithm_design_score': ability_record.algorithm_design_score,
                'problem_solving_score': ability_record.problem_solving_score,
                'analysis_report': ability_record.analysis_report,
                'last_assessed': ability_record.last_assessed
            }
            
            return self.success(result)
        except Exception as e:
            logger.error(f"Failed to get programming ability report: {str(e)}")
            return self.error("获取能力评估报告失败")
class AIAbilityComparisonAPI(APIView):
    """
    能力对比API
    """
    
    @login_required
    def get(self, request):
        """
        与平均水平或其他用户进行能力对比
        """
        try:
            user_id = request.user.id
            
            # 获取当前用户能力
            user_ability = AIProgrammingAbilityService.get_user_ability_report(user_id)
            
            # 计算所有用户的平均能力
            avg_scores = AIProgrammingAbility.objects.aggregate(
                avg_overall=models.Avg('overall_score'),
                avg_basic=models.Avg('basic_programming_score'),
                avg_ds=models.Avg('data_structure_score'),
                avg_algo=models.Avg('algorithm_design_score'),
                avg_ps=models.Avg('problem_solving_score')
            )
            
            comparison = {
                'user': {
                    'overall_score': user_ability.overall_score,
                    'level': user_ability.get_level_display(),
                    'basic_programming_score': user_ability.basic_programming_score,
                    'data_structure_score': user_ability.data_structure_score,
                    'algorithm_design_score': user_ability.algorithm_design_score,
                    'problem_solving_score': user_ability.problem_solving_score
                },
                'average': {
                    'overall_score': avg_scores['avg_overall'] or 0,
                    'basic_programming_score': avg_scores['avg_basic'] or 0,
                    'data_structure_score': avg_scores['avg_ds'] or 0,
                    'algorithm_design_score': avg_scores['avg_algo'] or 0,
                    'problem_solving_score': avg_scores['avg_ps'] or 0
                },
                'comparison': {
                    'overall_diff': user_ability.overall_score - (avg_scores['avg_overall'] or 0),
                    'basic_diff': user_ability.basic_programming_score - (avg_scores['avg_basic'] or 0),
                    'ds_diff': user_ability.data_structure_score - (avg_scores['avg_ds'] or 0),
                    'algo_diff': user_ability.algorithm_design_score - (avg_scores['avg_algo'] or 0),
                    'ps_diff': user_ability.problem_solving_score - (avg_scores['avg_ps'] or 0)
                }
            }
            
            return self.success(comparison)
        except Exception as e:
            logger.error(f"Failed to compare abilities: {str(e)}")
            return self.error("能力对比失败")