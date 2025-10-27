import requests
import json
import logging
from typing import List, Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class OllamaService:
    """
    Ollama服务类，专门用于与Ollama本地大模型交互
    """

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "codellama:7b"):
        self.base_url = base_url.rstrip('/')
        self.model = model

    def generate_completion(self, prompt: str, **kwargs) -> str:
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": kwargs
        }
        
        try:
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
            result = response.json()
            return result["response"]
        except Exception as e:
            logger.error(f"Ollama generate completion failed: {str(e)}")
            raise Exception(f"Ollama generate completion failed: {str(e)}")

    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": kwargs
        }
        
        try:
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
            
            result = response.json()
            return result["message"]["content"]
        except Exception as e:
            logger.error(f"Ollama chat completion failed: {str(e)}")
            raise Exception(f"Ollama chat completion failed: {str(e)}")

    def code_completion(self, code: str, prefix: str, language: str = "python", 
                       problem_context: str = "", **kwargs) -> Dict[str, Any]:
        # 构建专门用于代码补全的提示
        prompt = f"""你是一个专业的编程助手，请为用户提供代码自动补全建议。

                    语言: {language}
                    {f"题目上下文: {problem_context}" if problem_context else ""}

                    当前代码:
                    {code}

                    需要补全的文本: {prefix}

                    请提供以下信息：
                    1. 可能的补全选项列表（最多5个）
                    2. 每个选项的简要说明

                    严格按照以下JSON格式返回结果，不要包含任何额外的文字：
                    {{
                        "completions": [
                            {{"text": "补全文本1", "description": "说明1"}},
                            {{"text": "补全文本2", "description": "说明2"}}
                        ]
                    }}"""

        # 设置更适合代码补全的参数
        options = {
            "temperature": kwargs.get("temperature", 0.2),
            "top_p": kwargs.get("top_p", 0.9),
            "num_predict": kwargs.get("num_predict", 500)
        }

        try:
            response = self.generate_completion(prompt, **options)
            
            # 尝试解析JSON响应
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                response_json = json_match.group()
                return json.loads(response_json)
            else:
                # 如果无法解析JSON，返回默认补全
                return self._default_completions(prefix)
                
        except Exception as e:
            logger.error(f"Code completion failed: {str(e)}")
            # 出错时返回默认补全
            return self._default_completions(prefix)

    def _default_completions(self, prefix: str) -> Dict[str, Any]:
        return {
            "completions": [
                {"text": prefix + "print()", "description": "打印输出函数"},
                {"text": prefix + "if ", "description": "条件语句"},
                {"text": prefix + "for ", "description": "循环语句"},
                {"text": prefix + "while ", "description": "while循环"},
                {"text": prefix + "def ", "description": "函数定义"}
            ]
        }


class OllamaModelManager:
    """
    Ollama模型管理器
    """
    
    @staticmethod
    def list_models(base_url: str = "http://localhost:11434") -> List[Dict[str, Any]]:
        url = f"{base_url.rstrip('/')}/api/tags"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json().get("models", [])
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {str(e)}")
            return []

    @staticmethod
    def pull_model(model_name: str, base_url: str = "http://localhost:11434") -> bool:
        url = f"{base_url.rstrip('/')}/api/pull"
        
        payload = {
            "name": model_name
        }
        
        try:
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to pull Ollama model {model_name}: {str(e)}")
            return False