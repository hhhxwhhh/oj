from utils.api import serializers
from .models import AIModel,AIMessage,AICodeReview,AIConversation,AIFeedback,AIRecommendation,AIRecommendationFeedback,AIUserLearningPathNode
from .models import AIUserLearningPath,AIUserLearningPathNode,AIUserKnowledgeState,KnowledgePoint,AIProgrammingAbility,AIAbilityDimension,AIUserAbilityDetail


class AIModelSerializer(serializers.ModelSerializer):
    provider_display=serializers.CharField(source="get_provider_display",read_only=True)
    class Meta:
        model=AIModel
        fields="__all__"

class CreateAIModelSerializer(serializers.ModelSerializer):
    name=serializers.CharField(max_length=128)
    provider=serializers.ChoiceField(choices=AIModel.PROVIDER_CHOICES)
    api_key=serializers.CharField(max_length=128,required=False,allow_blank=True)
    model=serializers.CharField(max_length=128)
    is_active=serializers.BooleanField()
    config=serializers.DictField()

    class Meta:
        model=AIModel
        fields=["name","provider","api_key","model","is_active","config"]

    def validate(self, data):
        provider = data.get('provider')
        api_key = data.get('api_key')
        
        if provider != 'ollama' and not api_key:
            raise serializers.ValidationError("API Key is required for this provider")
            
        return data



class AIConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model=AIConversation
        fields="__all__"

class CreateAIConversationSerializer(serializers.ModelSerializer):
    title=serializers.CharField(max_length=256,required=False,allow_blank=True)

    class Meta:
        model=AIConversation
        fields=["title"]

class AIMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model=AIMessage
        fields="__all__"

class CreateAIMessageSerializer(serializers.ModelSerializer):
    conversation_id=serializers.IntegerField()
    role=serializers.CharField(max_length=128,required=False)
    content=serializers.CharField(max_length=4096)
    model_id=serializers.IntegerField(required=False)

    class Meta:
        model=AIMessage
        fields=["conversation_id","role","content","model_id"]



class AICodeReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model=AICodeReview
        fields="__all__"

class CreateAICodeReviewSerializer(serializers.ModelSerializer):
    problem_id = serializers.IntegerField()
    code = serializers.CharField(max_length=65535)
    language = serializers.CharField(max_length=32)

    class Meta:
        model=AICodeReview
        fields=["problem_id","code","language"]


class AIFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIFeedback
        fields = "__all__"


class CreateAIFeedbackSerializer(serializers.Serializer):
    message_id = serializers.IntegerField()
    rating = serializers.IntegerField()
    comment = serializers.CharField(max_length=1024, allow_blank=True)

class AIRecommendationSerializer(serializers.ModelSerializer):
    problem_title=serializers.SerializerMethodField()
    problem_difficulty=serializers.SerializerMethodField()

    class Meta:
        model=AIRecommendation
        fields="__all__"

    def get_problem_title(self,obj):
        return obj.problem.title
    def get_problem_difficulty(self,obj):
        return obj.problem.difficulty
    
class CreateAIRecommendationFeedbackSerializer(serializers.Serializer):
    recommendation_id = serializers.IntegerField()
    accepted = serializers.BooleanField()
    solved = serializers.BooleanField(required=False)
    feedback = serializers.CharField(required=False, allow_blank=True)

class AIRecommendationFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIRecommendationFeedback
        fields = "__all__"


class AIUserLearningPathSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIUserLearningPath
        fields = "__all__"


class AIUserLearningPathNodeSerializer(serializers.ModelSerializer):
    knowledge_point_name = serializers.SerializerMethodField()
    
    class Meta:
        model = AIUserLearningPathNode
        fields = [
            'id', 'learning_path', 'node_type', 'title', 'description', 
            'content_id', 'order', 'estimated_time', 'prerequisites', 
            'status', 'create_time', 'start_time', 'completion_time',
            'knowledge_point', 'knowledge_point_name'
        ]
        
    def get_knowledge_point_name(self, obj):
        return obj.knowledge_point.name if obj.knowledge_point else None



class AIUserLearningPathDetailSerializer(serializers.ModelSerializer):
    nodes = serializers.SerializerMethodField()
    
    class Meta:
        model = AIUserLearningPath
        fields = "__all__"
    
    def get_nodes(self, obj):
        from .models import AIUserLearningPathNode
        nodes = AIUserLearningPathNode.objects.filter(learning_path=obj).order_by('order')
        from .serializers import AIUserLearningPathNodeSerializer
        return AIUserLearningPathNodeSerializer(nodes, many=True).data
    

class KnowledgePointSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgePoint
        fields = "__all__"

class AIProblemGenerationSerializer(serializers.Serializer):
    knowledge_point = serializers.CharField(max_length=128, help_text="知识点名称")
    difficulty = serializers.ChoiceField(
        choices=[("Low", "简单"), ("Mid", "中等"), ("High", "困难")],
        default="Mid",
        help_text="题目难度"
    )
    auto_adjust = serializers.BooleanField(default=True, help_text="是否自动调整难度")
    generate_test_cases = serializers.BooleanField(default=True, help_text="是否生成测试用例")
    test_case_count = serializers.IntegerField(default=5, min_value=1, max_value=20, help_text="测试用例数量")

class AIProgrammingAbilitySerializer(serializers.ModelSerializer):
    level_display = serializers.SerializerMethodField()
    ability_breakdown = serializers.SerializerMethodField()
    
    class Meta:
        model = AIProgrammingAbility
        fields = [
            'id', 'user', 'overall_score', 'basic_programming_score', 
            'data_structure_score', 'algorithm_design_score', 
            'problem_solving_score', 'level', 'level_display',
            'analysis_report', 'last_assessed', 'create_time',
            'ability_breakdown'
        ]
        
    def get_level_display(self, obj):
        return obj.get_level_display()
        
    def get_ability_breakdown(self, obj):
        return obj.get_ability_breakdown()

    

class AIAbilityDimensionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIAbilityDimension
        fields = '__all__'

class AIUserAbilityDetailSerializer(serializers.ModelSerializer):
    dimension_name = serializers.SerializerMethodField()
    proficiency_level_display = serializers.SerializerMethodField()
    
    class Meta:
        model = AIUserAbilityDetail
        fields = '__all__'
        
    def get_dimension_name(self, obj):
        return obj.dimension.name
        
    def get_proficiency_level_display(self, obj):
        level_map = {
            'beginner': '入门',
            'intermediate': '中级',
            'advanced': '高级',
            'expert': '专家'
        }
        return level_map.get(obj.proficiency_level, obj.proficiency_level)
