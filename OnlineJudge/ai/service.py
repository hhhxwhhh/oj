import openai
import requests
from django.db import transaction
from .models import AIModel, AIMessage
from problem.models import Problem
from submission.models import Submission
import logging


logger=logging.getLogger(__name__)

class AIService:
    @staticmethod
    def get_active_ai_model():
        try:
            # 获取所有激活的AI模型
            active_models = AIModel.objects.filter(is_active=True)
            if not active_models.exists():
                raise Exception("No active AI model found")
            # 返回第一个激活的模型
            return active_models.first()
        except Exception as e:
            raise Exception(f"Error getting active AI model: {str(e)}")
    @staticmethod
    def call_ai_model(messages, ai_model=None):
        if ai_model is None:
            ai_model = AIService.get_active_ai_model()
        if not ai_model:
            raise Exception("No active AI model found")
        
        if ai_model.provider == "openai":
            return AIService._call_openai(messages, ai_model)
        elif ai_model.provider == "openkey":
            return AIService._call_openkey(messages, ai_model)
        else:
            raise Exception(f"Unsupported AI provider: {ai_model.provider}")

    @staticmethod
    def _call_openkey(messages, ai_model):
        import openai
        openai.api_base = "https://openkey.cloud/v1"
        openai.api_key = ai_model.api_key
        
        try:
            response = openai.ChatCompletion.create(
                model=ai_model.model,
                messages=messages
            )
            return response.choices[0].message.content
        except openai.error.APIConnectionError as e:
            logger.error(f"OpenKey API connection error: {str(e)}")
            raise Exception(f"无法连接到AI服务: {str(e)}")
        except openai.error.AuthenticationError as e:
            logger.error(f"OpenKey API authentication error: {str(e)}")
            raise Exception(f"AI服务认证失败: {str(e)}")
        except openai.error.RateLimitError as e:
            logger.error(f"OpenKey API rate limit error: {str(e)}")
            raise Exception(f"AI服务请求超限: {str(e)}")
        except Exception as e:
            logger.error(f"OpenKey API error: {str(e)}")
            raise Exception(f"AI服务调用失败: {str(e)}")

    
    @staticmethod
    def _call_openai(messages,ai_model):
        import openai
        # 检查是否使用OpenKey服务
        if "openkey.cloud" in ai_model.api_key:
            openai.api_base = "https://api.openkey.cloud/v1"
            openai.api_key = ai_model.api_key
        else:
            # 标准OpenAI配置
            openai.api_key = ai_model.api_key
        
        response = openai.ChatCompletion.create(
            model=ai_model.model,
            messages=messages
        )
        return response.choices[0].message.content
    
    @staticmethod
    def get_chat_history(conversation_id):
        messages=AIMessage.objects.filter(conversation_id=conversation_id).order_by("create_time")
        return [{"role":message.role,"content":message.content} for message in messages]
    
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
    
    @staticmethod
    def diagnose_submission(submission_id):
        try:
            submission=Submission.objects.select_related("problem").get(id=submission_id)
        except Submission.DoesNotExist:
            raise Exception("Submission not found")
        problem=submission.problem
        code=submission.code  
        result=submission.result 
        info=submission.info 
        language=submission.language

        result_text_map = {
            -1: "答案错误(Wrong Answer)",
            1: "CPU时间限制 exceeded",
            2: "运行时间超限(Real Time Limit Exceeded)",
            3: "内存超限(Memory Limit Exceeded)",
            4: "运行时错误(Runtime Error)",
            5: "系统错误(System Error)"
        }
        result_text = result_text_map.get(result, "未知错误")
        
        prompt = f"""
                    题目: {problem.title}
                    描述: {problem.description}

                    学生提交的{language}代码:
                    {code}

                    判题结果: {result_text}

                    详细信息: {info if info else "无"}

                    请分析这段代码可能存在的问题，并提供具体的修改建议。
                    如果可能，请给出修改后的代码示例。
                    """.strip()
        messages=[{"role":"user","content":prompt}]
        ai_model=AIService.get_active_ai_model()
        if not ai_model:
            raise Exception("No active AI model found")
        return AIService.call_ai_model(messages,ai_model)
    

    @staticmethod
    def recommend_problems(user_id,count=5):
        from django.db.models import Count
        from account.models import User
        try:
            user=User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise Exception("User not found")
        solved_submissions=Submission.objects.filter(
            user_id=user_id,
            result=0
        ).select_related("problem")
        solved_problems=[sub.problem for sub in solved_submissions]
        solved_tags=[]
        for problem in solved_problems:
            solved_tags.extend(problem.tags.all())

        from problem.models import Problem

        recommended_problems=Problem.objects.filter(
            tags__in=solved_tags,
            visible=True
        ).exclude(
            id__in=[problem.id for problem in solved_problems]
        ).distinct().order_by('?')[:count]

        problem_list = "\n".join([
            f"{i+1}. {problem.title}" for i, problem in enumerate(recommended_problems)
        ])

        prompt = f"""
                    根据用户已完成的题目和掌握的知识点，推荐{count}道适合练习的OJ题目。

                    用户已完成的题目涉及知识点包括：{', '.join([tag.name for tag in set(solved_tags)])}

                    推荐的题目列表：
                    {problem_list}

                    请为这些题目写一段推荐理由，说明为什么这些题目适合该用户进一步提升。
                    """.strip()
        
        messages = [{"role": "user", "content": prompt}]
        
        ai_model = AIService.get_active_ai_model()
        if not ai_model:
            raise Exception("No active AI model found")
            
        recommendation = AIService.call_ai_model(messages, ai_model)
        return {
            "problems": [{"id": p.id, "title": p.title} for p in recommended_problems],
            "recommendation": recommendation
        }
    @staticmethod
    def generate_code_explanation(code, language):
        try:
            prompt = f"请用中文详细解释以下{language}代码的功能和逻辑:\n\n{code}\n\n解释:"
            messages = [{"role": "user", "content": prompt}]
            
            ai_model = AIService.get_active_ai_model()
            if not ai_model:
                raise Exception("No active AI model found")
            
            return AIService.call_ai_model(messages, ai_model)
        except Exception as e:
            logger.error(f"Error in generate_code_explanation: {str(e)}")
            raise Exception(f"Failed to generate code explanation: {str(e)}")




