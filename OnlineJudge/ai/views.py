from django.shortcuts import render
import openai 
import requests
from django.db import transaction
# Create your views here.
from utils.api import APIView,validate_serializer
from account.decorators import login_required
from .models import AIModel,AIConversation,AIMessage,AICodeReview,AIFeedback
from .serializers import (
    AIModelSerializer, CreateAIModelSerializer,
    AIConversationSerializer, CreateAIConversationSerializer,
    AIMessageSerializer, CreateAIMessageSerializer,
    AICodeReviewSerializer, CreateAICodeReviewSerializer,
    AIFeedbackSerializer, CreateAIFeedbackSerializer,
    CreateAIRecommendationFeedbackSerializer,AIRecommendationFeedbackSerializer
)
from .service import AIService,AIRecommendationService
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
            active_model_exists = AIModel.objects.filter(is_active=True).exists()
            if not active_model_exists:
                return self.error("No active AI model found. Please configure an AI model first.")
            
            # 获取推荐题目
            recommendation_result = AIRecommendationService.recommend_next_problem(
                user.id, problem_id, submission_result
            )
            
            # 格式化推荐结果
            result = []
            if recommendation_result and recommendation_result[0] is not None:
                next_problem_id, score, reason = recommendation_result
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