from rest_framework import serializers
from .models import Assignment,AssignmentProblem,AssignmentStatistics,StudentAssignment
from problem.models import Problem
from problem.serializers import ProblemSerializer
from account.serializers import UserSerializer

class AssignmentSerializer(serializers.ModelSerializer):
    creator_username = serializers.SerializerMethodField()
    
    class Meta:
        model = Assignment
        fields = '__all__'
        read_only_fields = ('creator', 'create_time', 'update_time')
    
    def get_creator_username(self, obj):
        return obj.creator.username
    
class AssignmentProblemSerializer(serializers.ModelSerializer):
    problem_title = serializers.SerializerMethodField()
    
    class Meta:
        model = AssignmentProblem
        fields = '__all__'
        read_only_fields = ('assignment',)
    
    def get_problem_title(self, obj):
        return obj.problem.title
    
class StudentAssignmentSerializer(serializers.ModelSerializer):
    student_username = serializers.SerializerMethodField()
    student_realname = serializers.SerializerMethodField()
    personalized_problems_detail = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentAssignment
        fields = '__all__'
        read_only_fields = ('assignment', 'assigned_time')
    
    def get_student_username(self, obj):
        return obj.student.username
    
    def get_student_realname(self, obj):
        return obj.student.real_name
    
    def get_personalized_problems_detail(self, obj):
        if obj.personalized_problems:
            problem_ids = obj.get_personalized_problems()
            problems = Problem.objects.filter(_id__in=problem_ids)
            return ProblemSerializer(problems, many=True).data
        return []
    
class AssignmentStatisticsSerializer(serializers.ModelSerializer):
    student_username = serializers.SerializerMethodField()
    student_realname = serializers.SerializerMethodField()
    problem_title = serializers.SerializerMethodField()
    
    class Meta:
        model = AssignmentStatistics
        fields = '__all__'
    
    def get_student_username(self, obj):
        return obj.student.username
    
    def get_student_realname(self, obj):
        return obj.student.real_name
    
    def get_problem_title(self, obj):
        return obj.problem.title