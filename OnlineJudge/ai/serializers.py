from utils.api import serializers
from .models import AIModel,AIMessage,AICodeReview,AIConversation,AIFeedback

class AIModelSerializer(serializers.ModelSerializer):
    class Meta:
        model=AIModel
        fields="__all__"

class CreateAIModelSerializer(serializers.ModelSerializer):
    name=serializers.CharField(max_length=128)
    provider=serializers.CharField(max_length=128)
    api_key=serializers.CharField(max_length=128)
    model=serializers.CharField(max_length=128)
    is_active=serializers.BooleanField()
    config=serializers.DictField()


class AIConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model=AIConversation
        fields="__all__"

class CreateAIConversationSerializer(serializers.ModelSerializer):
    title=serializers.CharField(max_length=256)

class AIMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model=AIMessage
        fields="__all__"

class CreateAIMessageSerializer(serializers.ModelSerializer):
    conversation_id=serializers.IntegerField()
    role=serializers.CharField(max_length=128)
    content=serializers.CharField(max_length=4096)

class AICodeReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model=AICodeReview
        fields="__all__"

class CreateAICodeReviewSerializer(serializers.ModelSerializer):
    problem_id = serializers.IntegerField()
    code = serializers.CharField(max_length=65535)
    language = serializers.CharField(max_length=32)


class AIFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIFeedback
        fields = "__all__"


class CreateAIFeedbackSerializer(serializers.Serializer):
    message_id = serializers.IntegerField()
    rating = serializers.IntegerField()
    comment = serializers.CharField(max_length=1024, allow_blank=True)