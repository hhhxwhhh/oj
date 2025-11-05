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
                       problem_context: str = "", context: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        # 构建专门用于代码补全的提示
        prompt = f"""你是一个专业的编程助手，擅长{language}语言编程。请为用户提供准确、现代化的代码自动补全建议。

语言: {language}
{f"题目上下文: {problem_context}" if problem_context else ""}
{f"代码上下文: {json.dumps(context, ensure_ascii=False, indent=2)}" if context else ""}

当前代码:
{code}

需要补全的文本: {prefix}

请提供以下信息：
1. 可能的补全选项列表（最多8个）
2. 每个选项的简要说明
3. 每个选项的类型（函数、变量、关键字等）

请严格按照以下JSON格式返回结果，不要包含任何额外的文字：
{{
    "completions": [
        {{"text": "补全文本1", "description": "说明1", "type": "function"}},
        {{"text": "补全文本2", "description": "说明2", "type": "variable"}}
    ]
}}

注意事项：
1. 优先提供与当前代码上下文相关的建议
2. 如果是函数调用，提供函数签名和参数说明
3. 如果是对象方法，提供方法说明
4. 补全建议应该准确且现代化
5. 避免提供过时或不推荐使用的API"""

        # 设置更适合代码补全的参数
        options = {
            "temperature": kwargs.get("temperature", 0.1),  # 更低的随机性以获得更准确的结果
            "top_p": kwargs.get("top_p", 0.9),
            "num_predict": kwargs.get("num_predict", 800)  # 增加预测长度以容纳更多补全选项
        }

        try:
            response = self.generate_completion(prompt, **options)
            
            # 尝试解析JSON响应
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                response_json = json_match.group()
                result = json.loads(response_json)
                
                # 验证结果格式
                if "completions" in result and isinstance(result["completions"], list):
                    # 过滤掉不合适的补全建议
                    filtered_completions = [
                        comp for comp in result["completions"] 
                        if comp.get("text") and len(comp.get("text", "")) > 0
                    ]
                    result["completions"] = filtered_completions[:8]  # 限制最多8个建议
                    return result
            
            # 如果无法解析JSON或格式不正确，返回默认补全
            return self._intelligent_completions(prefix, language, context)
                
        except Exception as e:
            logger.error(f"Code completion failed: {str(e)}")
            # 出错时返回智能补全
            return self._intelligent_completions(prefix, language, context)

    def _intelligent_completions(self, prefix: str, language: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        基于语言和上下文的智能默认补全
        """
        completions = []
        
        # 根据语言提供特定的补全建议
        if language.lower() in ['python', 'python3']:
            completions = self._python_completions(prefix, context)
        elif language.lower() in ['javascript', 'js']:
            completions = self._javascript_completions(prefix, context)
        elif language.lower() in ['java']:
            completions = self._java_completions(prefix, context)
        elif language.lower() in ['c++', 'cpp']:
            completions = self._cpp_completions(prefix, context)
        else:
            # 默认补全
            completions = [
                {"text": prefix + "print()", "description": "打印输出函数", "type": "function"},
                {"text": prefix + "if ", "description": "条件语句", "type": "keyword"},
                {"text": prefix + "for ", "description": "循环语句", "type": "keyword"},
                {"text": prefix + "while ", "description": "while循环", "type": "keyword"},
                {"text": prefix + "def ", "description": "函数定义", "type": "keyword"}
            ]
        
        return {"completions": completions[:5]}  # 限制最多5个建议

    def _python_completions(self, prefix: str, context: Dict[str, Any] = None) -> List[Dict[str, str]]:
        """
        Python语言的智能补全建议
        """
        # 基础Python补全
        completions = [
            {"text": "print()", "description": "打印输出函数", "type": "function"},
            {"text": "len()", "description": "获取对象长度", "type": "function"},
            {"text": "range()", "description": "生成数字序列", "type": "function"},
            {"text": "str()", "description": "转换为字符串", "type": "function"},
            {"text": "int()", "description": "转换为整数", "type": "function"},
            {"text": "list()", "description": "创建列表", "type": "function"},
            {"text": "dict()", "description": "创建字典", "type": "function"},
            {"text": "if ", "description": "条件语句", "type": "keyword"},
            {"text": "for ", "description": "循环语句", "type": "keyword"},
            {"text": "while ", "description": "while循环", "type": "keyword"},
            {"text": "def ", "description": "函数定义", "type": "keyword"},
            {"text": "class ", "description": "类定义", "type": "keyword"},
            {"text": "import ", "description": "导入模块", "type": "keyword"},
            {"text": "with ", "description": "上下文管理器", "type": "keyword"},
            {"text": "try:", "description": "异常处理", "type": "keyword"}
        ]
        
        # 根据上下文提供更多相关建议
        if context:
            if context.get("isInFunction"):
                completions.extend([
                    {"text": "return ", "description": "返回值", "type": "keyword"},
                    {"text": "pass", "description": "空操作语句", "type": "keyword"}
                ])
            
            if context.get("isInClass"):
                completions.extend([
                    {"text": "self.", "description": "类实例引用", "type": "variable"},
                    {"text": "__init__", "description": "构造函数", "type": "function"}
                ])
            
            # 根据最后的关键字提供更多相关建议
            last_keyword = context.get("lastKeyword", "")
            if last_keyword == "if":
                completions.extend([
                    {"text": "elif ", "description": "else if条件", "type": "keyword"},
                    {"text": "else:", "description": "否则条件", "type": "keyword"}
                ])
            elif last_keyword == "for":
                completions.extend([
                    {"text": "in ", "description": "迭代器", "type": "keyword"},
                    {"text": "range()", "description": "数字范围", "type": "function"}
                ])
            elif last_keyword == "try":
                completions.extend([
                    {"text": "except ", "description": "异常捕获", "type": "keyword"},
                    {"text": "finally:", "description": "最终执行块", "type": "keyword"}
                ])
        
        # 过滤与prefix匹配的建议
        if prefix:
            completions = [comp for comp in completions if comp["text"].startswith(prefix)]
        
        return completions[:8]  # 限制最多8个建议

    def _javascript_completions(self, prefix: str, context: Dict[str, Any] = None) -> List[Dict[str, str]]:
        """
        JavaScript语言的智能补全建议
        """
        completions = [
            {"text": "console.log()", "description": "控制台输出", "type": "function"},
            {"text": "let ", "description": "声明变量", "type": "keyword"},
            {"text": "const ", "description": "声明常量", "type": "keyword"},
            {"text": "var ", "description": "声明变量(不推荐)", "type": "keyword"},
            {"text": "function ", "description": "函数声明", "type": "keyword"},
            {"text": "if ", "description": "条件语句", "type": "keyword"},
            {"text": "for ", "description": "循环语句", "type": "keyword"},
            {"text": "while ", "description": "while循环", "type": "keyword"},
            {"text": "class ", "description": "类定义", "type": "keyword"},
            {"text": "import ", "description": "导入模块", "type": "keyword"},
            {"text": "export ", "description": "导出模块", "type": "keyword"},
            {"text": "try {", "description": "异常处理", "type": "keyword"}
        ]
        
        return completions[:8]

    def _java_completions(self, prefix: str, context: Dict[str, Any] = None) -> List[Dict[str, str]]:
        """
        Java语言的智能补全建议
        """
        completions = [
            {"text": "System.out.println()", "description": "控制台输出", "type": "function"},
            {"text": "int ", "description": "整型变量", "type": "keyword"},
            {"text": "String ", "description": "字符串类型", "type": "keyword"},
            {"text": "public ", "description": "公共访问修饰符", "type": "keyword"},
            {"text": "private ", "description": "私有访问修饰符", "type": "keyword"},
            {"text": "static ", "description": "静态修饰符", "type": "keyword"},
            {"text": "void ", "description": "无返回值", "type": "keyword"},
            {"text": "class ", "description": "类定义", "type": "keyword"},
            {"text": "if ", "description": "条件语句", "type": "keyword"},
            {"text": "for ", "description": "循环语句", "type": "keyword"},
            {"text": "while ", "description": "while循环", "type": "keyword"},
            {"text": "try {", "description": "异常处理", "type": "keyword"}
        ]
        
        return completions[:8]

    def _cpp_completions(self, prefix: str, context: Dict[str, Any] = None) -> List[Dict[str, str]]:
        """
        C++语言的智能补全建议
        """
        completions = [
            {"text": "std::cout << ", "description": "控制台输出", "type": "function"},
            {"text": "int ", "description": "整型变量", "type": "keyword"},
            {"text": "std::string ", "description": "字符串类型", "type": "keyword"},
            {"text": "public:", "description": "公共访问修饰符", "type": "keyword"},
            {"text": "private:", "description": "私有访问修饰符", "type": "keyword"},
            {"text": "void ", "description": "无返回值", "type": "keyword"},
            {"text": "class ", "description": "类定义", "type": "keyword"},
            {"text": "if ", "description": "条件语句", "type": "keyword"},
            {"text": "for ", "description": "循环语句", "type": "keyword"},
            {"text": "while ", "description": "while循环", "type": "keyword"},
            {"text": "try {", "description": "异常处理", "type": "keyword"}
        ]
        
        return completions[:8]


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