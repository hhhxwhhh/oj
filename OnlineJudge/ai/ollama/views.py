from django.shortcuts import render
from utils.api import APIView
from account.decorators import login_required
from .service import OllamaService
from ai.models import AIModel
import logging

logger = logging.getLogger(__name__)


class OllamaCodeCompletionAPI(APIView):
    @login_required
    def post(self, request):
        """
        使用Ollama提供代码自动补全建议
        """
        user = request.user
        code = request.data.get("code", "")
        language = request.data.get("language", "python")
        prefix = request.data.get("prefix", "")
        problem_id = request.data.get("problem_id")
        model_id = request.data.get("model_id")
        
        try:
            # 获取Ollama模型配置
            ollama_config = self._get_ollama_config(model_id)
            if not ollama_config:
                return self.error("No valid Ollama model configuration found")
            
            # 初始化Ollama服务
            ollama_service = OllamaService(
                base_url=ollama_config["base_url"],
                model=ollama_config["model"]
            )
            
            # 获取题目上下文（如果有）
            problem_context = ""
            if problem_id:
                problem_context = self._get_problem_context(problem_id)
            
            # 生成代码补全建议
            completion_result = ollama_service.code_completion(
                code=code,
                prefix=prefix,
                language=language,
                problem_context=problem_context
            )
            
            return self.success(completion_result)
        except Exception as e:
            logger.error(f"Ollama code completion failed: {str(e)}")
            return self.error(f"Failed to generate code completion: {str(e)}")
    
    def _get_ollama_config(self, model_id=None):
        try:
            # 如果指定了model_id，尝试获取对应模型
            if model_id:
                ai_model = AIModel.objects.get(id=model_id, provider="ollama")
            else:
                # 否则获取第一个激活的Ollama模型
                ai_model = AIModel.objects.filter(provider="ollama", is_active=True).first()
                if not ai_model:
                    # 如果没有激活的Ollama模型，获取任意一个Ollama模型
                    ai_model = AIModel.objects.filter(provider="ollama").first()
            
            if not ai_model:
                return None
            
            return {
                "base_url": ai_model.config.get("base_url", "http://localhost:11434"),
                "model": ai_model.model
            }
        except AIModel.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Failed to get Ollama config: {str(e)}")
            return None
    
    def _get_problem_context(self, problem_id):
        try:
            from problem.models import Problem
            problem = Problem.objects.get(id=problem_id)
            return f"题目: {problem.title}\n题目描述: {problem.description}"
        except Problem.DoesNotExist:
            return ""
        except Exception as e:
            logger.error(f"Failed to get problem context: {str(e)}")
            return ""


class OllamaModelListAPI(APIView):
    @login_required
    def get(self, request):
        try:
            # 获取激活的Ollama模型
            ollama_models = AIModel.objects.filter(provider="ollama")
            
            result = []
            for model in ollama_models:
                result.append({
                    "id": model.id,
                    "name": model.name,
                    "model": model.model,
                    "is_active": model.is_active,
                    "config": model.config,
                    "create_time": model.create_time,
                    "update_time": model.update_time
                })
            
            return self.success(result)
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {str(e)}")
            return self.error("Failed to retrieve Ollama models")


class OllamaChatAPI(APIView):
    @login_required
    def post(self, request):
        """
        与Ollama模型进行对话
        """
        user = request.user
        messages = request.data.get("messages", [])
        model_id = request.data.get("model_id")
        
        try:
            # 获取Ollama模型配置
            ollama_config = self._get_ollama_config(model_id)
            if not ollama_config:
                return self.error("No valid Ollama model configuration found")
            
            # 初始化Ollama服务
            ollama_service = OllamaService(
                base_url=ollama_config["base_url"],
                model=ollama_config["model"]
            )
            
            # 进行对话
            response = ollama_service.chat_completion(messages)
            
            return self.success({"response": response})
        except Exception as e:
            logger.error(f"Ollama chat failed: {str(e)}")
            return self.error(f"Failed to chat with Ollama: {str(e)}")
    
    def _get_ollama_config(self, model_id=None):
        try:
            # 如果指定了model_id，尝试获取对应模型
            if model_id:
                ai_model = AIModel.objects.get(id=model_id, provider="ollama")
            else:
                # 否则获取第一个激活的Ollama模型
                ai_model = AIModel.objects.filter(provider="ollama", is_active=True).first()
                if not ai_model:
                    # 如果没有激活的Ollama模型，获取任意一个Ollama模型
                    ai_model = AIModel.objects.filter(provider="ollama").first()
            
            if not ai_model:
                return None
            
            return {
                "base_url": ai_model.config.get("base_url", "http://localhost:11434"),
                "model": ai_model.model
            }
        except AIModel.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Failed to get Ollama config: {str(e)}")
            return None