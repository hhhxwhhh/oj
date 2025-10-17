import openai
from .models import AIModel


def get_openai_client():
    ai_model = AIModel.objects.filter(is_active=True, provider='openai').first()
    if not ai_model:
        return None
    
    openai.api_key = ai_model.api_key
    return openai


def format_ai_response(response):
    # 移除可能的多余空白字符
    return response.strip()


def validate_ai_model_config(provider, config):
    if provider == "openai":
        # 检查OpenAI配置
        required_fields = ['api_key', 'model']
        for field in required_fields:
            if field not in config or not config[field]:
                return False, f"Missing required field: {field}"
        return True, "Valid configuration"
    else:
        return False, f"Unsupported provider: {provider}"