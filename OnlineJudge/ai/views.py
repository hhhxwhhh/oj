from django.shortcuts import render
import openai 
import requests
from django.db import transaction
# Create your views here.
from utils.api import APIView,validate_serializer
from account.decorators import login_required
from .models import AIModel,AIConversation,AIMessage,AICodeReview,AIFeedback,KnowledgePoint
from .serializers import (
    AIModelSerializer, CreateAIModelSerializer,
    AIConversationSerializer, CreateAIConversationSerializer,
    AIMessageSerializer, CreateAIMessageSerializer,
    AICodeReviewSerializer, CreateAICodeReviewSerializer,
    AIFeedbackSerializer, CreateAIFeedbackSerializer,
    CreateAIRecommendationFeedbackSerializer,AIRecommendationFeedbackSerializer
)
from .service import AIService,AIRecommendationService,AILearningPathService,AICodeDiagnosisService,KnowledgePointService   
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
    def post(self,request):
        data=request.data
        user=request.user
        try:
            feedback=AIFeedback.objects.create(
                user=user,
                recommendation_id=data["recommendation_id"],
                accepted=data['accepted'],
                solved=data.get("solved",False),
                feedback=data.get("feedback",""),
            )
            return self.success(AIRecommendationFeedbackSerializer(feedback).data)
        except Exception as e:
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
            data = AIUserLearningPathDetailSerializer(path).data
            data['nodes'] = [
                {
                    'id': node.id,
                    'node_type': node.node_type,
                    'title': node.title,
                    'description': node.description,
                    'content_id': node.content_id,
                    'order': node.order,
                    'estimated_time': node.estimated_time,
                    'prerequisites': node.prerequisites,
                    'status': node.status,
                    'create_time': node.create_time
                }
                for node in nodes
            ]
            return self.success(data)
        except Exception as e:
            logger.error(f"Get learning path detail failed: {str(e)}")
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
        logger.info("KnowledgePointAPI GET request received")
        try:
            user = request.user
            knowledge_states = KnowledgePointService.get_user_knowledge_state(user.id)
            
            result = []
            for name, state in knowledge_states.items():
                result.append({
                    'knowledge_point': name,
                    'proficiency_level': state.proficiency_level,
                    'correct_attempts': state.correct_attempts,
                    'total_attempts': state.total_attempts,
                    'last_updated': state.last_updated.isoformat() if state.last_updated else None
                })
            
            logger.info(f"Returning knowledge states for user {user.id}")
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
            return self.success(recommendations)
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
            return self.success(recommendations)
        except Exception as e:
            logger.error(f"Failed to get knowledge recommendations: {str(e)}")
            return self.error("Failed to get recommendations")
