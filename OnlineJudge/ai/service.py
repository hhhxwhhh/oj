import openai
import requests
from django.db import transaction
from .models import AIModel, AIMessage
from problem.models import Problem
from submission.models import Submission

class AIService:
    @staticmethod
    def get_active_ai_model():
        try:
            return AIModel.objects.get(is_active=True)
        except AIModel.DoesNotExist:
            raise Exception("No active AI model found")
    
    @staticmethod
    def call_ai_model(messages,ai_model=None):
        if ai_model is None:
            ai_model =AIService.get_active_ai_model()
        if not ai_model:
            raise Exception("No active AI model found")
        if ai_model.provider =="openai":
            return AIService._call_openai(messages,ai_model)
        else:
            raise Exception(f"Unsupported AI provider: {ai_model.provider}")
        
    @staticmethod
    def _call_openai(messages,ai_model):
        openai.api_key=ai_model.api_key
        response=openai.ChatCompletion.create(
            model=ai_model.model,
            messages=messages
        )
        return response.choices[0].message.content
    
    @staticmethod
    def get_chat_history(conversation_id):
        messages=AIMessage.objects.filter(conversation_id=conversation_id).order_by("create_time")
        return [{"role":message.role,"content":message.content} for message in messages]
    
    @staticmethod
    def generate_code_explanation(code,language):
        prompt = f"请解释以下{language}代码:\n\n{code}\n\n解释:"
        messages = [{"role": "user", "content": prompt}]
        
        ai_model = AIService.get_active_ai_model()
        if not ai_model:
            raise Exception("No active AI model found")
        
        return AIService.call_ai_model(messages, ai_model)
    
    @staticmethod
    def generate_problem_solution(problem_id):
        try:
            problem = Problem.objects.get(id=problem_id)
        except Problem.DoesNotExist:
            raise Exception("Problem not found")
        
        prompt = f"题目: {problem.title}\n描述: {problem.description}\n\n请提供解题思路和要点:"
        messages = [{"role": "user", "content": prompt}]
        
        ai_model = AIService.get_active_ai_model()
        if not ai_model:
            raise Exception("No active AI model found")
        
        return AIService.call_ai_model(messages, ai_model)
    
    @staticmethod
    def review_code(problem_id,code,language):
        try:
            problem = Problem.objects.get(id=problem_id)
        except Problem.DoesNotExist:
            raise Exception("Problem not found")
        
        prompt = f"题目: {problem.title}\n描述: {problem.description}\n\n请审查以下{language}代码并提供改进建议:\n\n{code}\n\n审查结果:"
        messages = [{"role": "user", "content": prompt}]
        
        ai_model = AIService.get_active_ai_model()
        if not ai_model:
            raise Exception("No active AI model found")
        
        return AIService.call_ai_model(messages, ai_model)


