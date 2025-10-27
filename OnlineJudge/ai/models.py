from django.db import models
from utils.models import JSONField
from account.models import User
from problem.models import Problem

class AIModel(models.Model):
    PROVIDER_CHOICES = [
        ('openai', 'OpenAI'),
        ('azure', 'Azure OpenAI'),
        ('openkey', 'OpenKey'),
        ('deepseek', 'DeepSeek'),
        ('ollama', 'Ollama'),
    ]
    name=models.TextField()
    provider=models.TextField(choices=PROVIDER_CHOICES)
    api_key=models.TextField()
    model=models.TextField()
    is_active=models.BooleanField(default=True)
    config=JSONField(default=dict)
    create_time=models.DateTimeField(auto_now_add=True)
    update_time=models.DateTimeField(auto_now=True)

    class Meta:
        db_table='ai_model'

class AIConversation(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    title=models.TextField(max_length=256)
    create_time=models.DateTimeField(auto_now_add=True)
    update_time=models.DateTimeField(auto_now=True)

    class Meta:
        db_table='ai_conversation'

class AIMessage(models.Model):
    conversation=models.ForeignKey(AIConversation,on_delete=models.CASCADE)
    role=models.TextField()
    content=models.TextField()
    create_time=models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table='ai_message'


class AICodeReview(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    problem_id=models.IntegerField()
    code=models.TextField()
    language=models.TextField()
    review_result=JSONField(default=dict)
    create_time=models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table='ai_code_review'

class AIFeedback(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    message=models.ForeignKey(AIMessage,on_delete=models.CASCADE)
    rating=models.IntegerField()
    comment=models.TextField(blank=True)
    create_time=models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table='ai_feedback'
    
class AICodeExplanationCache(models.Model):
    code_hash = models.TextField(unique=True)  
    language = models.TextField()
    explanation = models.TextField()
    create_time = models.DateTimeField(auto_now_add=True)
    usage_count = models.IntegerField(default=1) 

    class Meta:
        db_table = 'ai_code_explanation_cache'
        indexes = [
            models.Index(fields=['code_hash']),
            models.Index(fields=['create_time']),
        ]


class AIRecommendation(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    problem=models.ForeignKey(Problem,on_delete=models.CASCADE)
    score=models.FloatField()
    reason=models.TextField()
    created_at=models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table='ai_recommendation'
        unique_together=('user', 'problem')


class AIRecommendationFeedback(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    problem=models.ForeignKey(Problem,on_delete=models.CASCADE)
    recommendation=models.ForeignKey(AIRecommendation,on_delete=models.CASCADE)
    accepted=models.BooleanField(default=False)
    solved=models.BooleanField(default=False)
    feedback=models.TextField(blank=True)
    created_at=models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table='ai_recommendation_feedback'


class AIUserLearningPath(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.TextField()
    description = models.TextField()
    estimated_duration = models.IntegerField(help_text="预计完成时间(小时)")
    path_data = JSONField(default=dict)  
    is_active = models.BooleanField(default=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ai_user_learning_path'




class KnowledgePoint(models.Model):
    """
    知识点模型
    """
    name = models.TextField(unique=True, help_text="知识点名称")
    description = models.TextField(help_text="知识点描述")
    category = models.TextField(help_text="知识点分类")
    difficulty = models.IntegerField(help_text="难度等级(1-5)")
    parent_points = models.ManyToManyField('self', symmetrical=False, blank=True, help_text="前置知识点")
    related_problems = models.ManyToManyField('problem.Problem', blank=True, help_text="相关题目")
    create_time = models.DateTimeField(auto_now_add=True)
    # 推荐权重字段，默认为1.0
    weight = models.FloatField(default=1.0, help_text="推荐权重")
    
    class Meta:
        db_table = 'ai_knowledge_point'
        verbose_name = '知识点'
        verbose_name_plural = '知识点'

    def __str__(self):
        return self.name



class AIUserKnowledgeState(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    knowledge_point = models.ForeignKey(KnowledgePoint, on_delete=models.CASCADE, help_text="知识点")
    proficiency_level = models.FloatField(default=0.0, help_text="掌握程度(0-1)")
    last_updated = models.DateTimeField(auto_now=True)
    correct_attempts = models.IntegerField(default=0)
    total_attempts = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'ai_user_knowledge_state'
        unique_together = ('user', 'knowledge_point')

    def update_proficiency(self, is_correct):
        """
        更新知识点掌握程度
        """
        self.total_attempts += 1
        if is_correct:
            self.correct_attempts += 1
        
        # 计算掌握程度：正确率 + 时间衰减因子
        accuracy = self.correct_attempts / self.total_attempts if self.total_attempts > 0 else 0
        
        # 简单的掌握程度计算算法
        self.proficiency_level = min(1.0, accuracy * 0.7 + self.proficiency_level * 0.3)
        
        self.proficiency_level = round(self.proficiency_level, 4)
        
        self.save()

class AIUserLearningPathNode(models.Model):
    learning_path = models.ForeignKey(AIUserLearningPath, on_delete=models.CASCADE)
    node_type = models.TextField(help_text="节点类型: concept, problem, project")  # 概念、题目、项目
    title = models.TextField()
    description = models.TextField()
    content_id = models.IntegerField(help_text="关联的内容ID(如题目ID、概念ID等)")
    order = models.IntegerField()
    estimated_time = models.IntegerField(help_text="预计完成时间(分钟)")
    prerequisites = JSONField(default=list, help_text="前置知识点")
    status = models.TextField(default="pending", help_text="状态: pending, in_progress, completed")
    create_time = models.DateTimeField(auto_now_add=True)
    knowledge_point = models.ForeignKey(KnowledgePoint, on_delete=models.SET_NULL, null=True, blank=True, help_text="关联的知识点")

    class Meta:
        db_table = 'ai_user_learning_path_node'


class AIProgrammingAbility(models.Model):
    """
    用户编程能力评估模型
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    overall_score = models.FloatField(default=0.0)  # 总体能力评分 (
    
    # 各维度评分
    basic_programming_score = models.FloatField(default=0.0)  # 基础编程能力
    data_structure_score = models.FloatField(default=0.0)     # 数据结构能力
    algorithm_design_score = models.FloatField(default=0.0)   # 算法设计能力
    problem_solving_score = models.FloatField(default=0.0)    # 解题能力
    
    # 能力等级
    LEVEL_CHOICES = [
        ('beginner', '入门'),
        ('intermediate', '中级'),
        ('advanced', '高级'),
        ('expert', '专家'),
    ]
    level = models.TextField(choices=LEVEL_CHOICES, default='beginner')
    
    # 详细分析报告
    analysis_report = JSONField(default=dict)  # 存储详细的分析报告
    
    # 时间戳
    last_assessed = models.DateTimeField(auto_now=True)
    create_time = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_programming_ability'
        unique_together = ('user',)

class AIAbilityDimension(models.Model):
    """
    能力维度定义
    """
    name = models.TextField(unique=True)  
    description = models.TextField()       
    weight = models.FloatField(default=1.0)  
    create_time = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_ability_dimension'

class AIUserAbilityDetail(models.Model):
    """
    用户各项能力详情
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dimension = models.ForeignKey(AIAbilityDimension, on_delete=models.CASCADE)
    score = models.FloatField(default=0.0)  
    proficiency_level = models.TextField(default='beginner')  #
    evidence = JSONField(default=dict)  
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_user_ability_detail'
        unique_together = ('user', 'dimension')