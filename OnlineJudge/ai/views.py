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
    AIFeedbackSerializer, CreateAIFeedbackSerializer
)
from .service import AIService


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
        
    @validate_serializer(CreateAIModelSerializer)
    def post(self,request):
        data=request.data
        ai_model = AIModel.objects.create(
            name=data["name"],
            provider=data["provider"],
            api_key=data["api_key"],
            model=data["model"],
            is_active=data["is_active"],
            config=data["config"]
        )
        return self.success(AIModelSerializer(ai_model).data)
    
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
        
class AIModelListAdminAPI(APIView):
    def get(self,request):
        ai_models=AIModel.objects.all()
        return self.success(AIModelSerializer(ai_models,many=True).data)
    
class AIConversationAPI(APIView):
    @login_required
    @validate_serializer(CreateAIConversationSerializer)
    def post(self,request):
        data=request.data
        user=request.user        
        conversation=AIConversation.objects.create(
            user=user,
            title=data['title']
        )
        return self.success(AIConversationSerializer(conversation).data)
    

class AIConversationListAPI(APIView):
    @login_required
    def get(self, request):
        user = request.user
        conversations = AIConversation.objects.filter(user=user).order_by("-update_time")
        return self.success(AIConversationSerializer(conversations, many=True).data)
    

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
        user_message = AIMessage.objects.create(
            conversation_id=data["conversation_id"],
            role="user",
            content=data["content"]
        )
        messages = AIService.get_chat_history(data["conversation_id"])
        try:
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
        except Exception as e:
            return self.error(str(e))
        
class AICodeExplanationAPI(APIView):
    @login_required
    def post(self,request):
        code=request.data.get("code")
        language=request.data.get("language")
        if not code or not language:
            return self.error("Parameter error")
        try:
            explanation=AIService.generate_code_explanation(code,language)
            return self.success({"explanation":explanation})
        except Exception as e:
            return self.error(str(e))
        

class AIProblemSolutionAPI(APIView):
    @login_required
    def post(self, request):
        problem_id = request.data.get("problem_id")
        if not problem_id:
            return self.error("Parameter error")
        try:
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



