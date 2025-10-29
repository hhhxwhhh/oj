from django.db import models
from account.models import User
from problem.models import Problem
import json
# Create your models here.
class Assignment(models.Model):
    RULE_CHOICES = [
        ('ACM', 'ACM'),
        ('OI', 'OI'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_assignments')
    is_personalized = models.BooleanField(default=False)
    rule_type = models.CharField(max_length=10, choices=RULE_CHOICES, default='ACM')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'assignment'
        ordering = ['-create_time']
    
    def __str__(self):
        return self.title

class AssignmentProblem(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='assignment_problems')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)  # 仅用于OI模式
    
    class Meta:
        db_table = 'assignment_problem'
        unique_together = ('assignment', 'problem')

class StudentAssignment(models.Model):
    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='student_assignments')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_assignments')
    personalized_problems = models.TextField(blank=True, null=True)  
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='assigned')
    assigned_time = models.DateTimeField(auto_now_add=True)
    completed_time = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'student_assignment'
        unique_together = ('assignment', 'student')
    
    def get_personalized_problems(self):
        if self.personalized_problems:
            return json.loads(self.personalized_problems)
        return []
    
    def set_personalized_problems(self, problems):
        self.personalized_problems = json.dumps(problems)


class AssignmentStatistics(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    submission_count = models.IntegerField(default=0)
    accepted_count = models.IntegerField(default=0)
    best_score = models.IntegerField(default=0)  # 仅用于OI模式
    first_ac_time = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'assignment_statistics'
        unique_together = ('assignment', 'student', 'problem')
