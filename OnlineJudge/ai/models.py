from django.db import models
from utils.models import JSONField
from account.models import User
from problem.models import Problem

class AIModel(models.Model):
    name=models.TextField()
    provider=models.TextField()
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