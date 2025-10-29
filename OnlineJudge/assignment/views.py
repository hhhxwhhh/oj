from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import BasePermission
from django.utils import timezone
from django.db.models import Count, Avg, Q
from .models import Assignment, AssignmentProblem, StudentAssignment, AssignmentStatistics
from account.models import User
from problem.models import Problem
from submission.models import Submission
from .serializers import (
    AssignmentSerializer, 
    AssignmentProblemSerializer, 
    StudentAssignmentSerializer,
    AssignmentStatisticsSerializer
)
from utils.api import APIView, validate_serializer
from account.decorators import super_admin_required, admin_role_required
import random
import json


class IsAdminOrSuperAdmin(BasePermission):
    """
    自定义权限类，允许管理员或超级管理员访问
    """
    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and (user.is_super_admin() or user.is_admin_role())


class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    permission_classes = [IsAdminOrSuperAdmin]
    
    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)
    
    @action(detail=True, methods=['post'], url_path='assign')
    def assign_to_students(self, request, pk=None):
        assignment = self.get_object()
        student_ids = request.data.get('student_ids', [])
        all_students = request.data.get('all_students', False)
        
        if all_students:
            # 分配给所有学生
            students = User.objects.filter(admin_type=User.REGULAR_USER)
        else:
            # 分配给指定学生
            students = User.objects.filter(id__in=student_ids)
        
        created_count = 0
        for student in students:
            student_assignment, created = StudentAssignment.objects.get_or_create(
                assignment=assignment,
                student=student,
                defaults={'status': 'assigned'}
            )
            
            # 如果是个性化作业，为每个学生生成个性化题目
            if assignment.is_personalized and created:
                personalized_problems = self._generate_personalized_problems(student, assignment.rule_type)
                student_assignment.set_personalized_problems(personalized_problems)
                student_assignment.save()
            
            if created:
                created_count += 1
        
        return Response({
            'message': f'成功分配给{created_count}名学生',
            'assigned_count': created_count
        })
    
    def _generate_personalized_problems(self, student, rule_type):
        solved_submissions = Submission.objects.filter(
            user=student, 
            result=0  # Accepted
        ).values_list('problem__id', flat=True)
        attempted_problems = Submission.objects.filter(
            user=student
        ).exclude(
            problem__id__in=solved_submissions
        ).values_list('problem__id', flat=True).distinct()
        
        personalized_problems = []
        
        # 从尝试过但未解决的题目中选择
        attempted_but_unsolved = list(Problem.objects.filter(
            id__in=attempted_problems
        ).exclude(
            id__in=solved_submissions
        )[:3])
        
        # 从未解决且难度适中的题目中选择
        medium_problems = list(Problem.objects.filter(
            difficulty='Mid'
        ).exclude(
            id__in=solved_submissions
        ).exclude(
            id__in=attempted_problems
        )[:5])
        
        # 从未解决且难度较高的题目中选择
        hard_problems = list(Problem.objects.filter(
            difficulty='High'
        ).exclude(
            id__in=solved_submissions
        ).exclude(
            id__in=attempted_problems
        )[:2])
        
        all_problems = attempted_but_unsolved + medium_problems + hard_problems
        problem_ids = [p._id for p in all_problems]
        
        return problem_ids
    
    @action(detail=True, methods=['get'], url_path='students')
    def get_assigned_students(self, request, pk=None):
        assignment = self.get_object()
        students = StudentAssignment.objects.filter(assignment=assignment)
        serializer = StudentAssignmentSerializer(students, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='statistics')
    def get_statistics(self, request, pk=None):
        assignment = self.get_object()
        statistics = AssignmentStatistics.objects.filter(assignment=assignment)
        serializer = AssignmentStatisticsSerializer(statistics, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='detailed-statistics')
    def get_detailed_statistics(self, request, pk=None):
        """
        获取详细统计信息
        """
        assignment = self.get_object()
        
        # 获取所有分配给学生的作业
        student_assignments = StudentAssignment.objects.filter(assignment=assignment)
        total_students = student_assignments.count()
        
        # 获取已提交的学生数
        submitted_students = student_assignments.filter(
            assignmentstatistics__submission_count__gt=0
        ).distinct().count()
        
        # 获取已完成的学生数 (所有题目都已通过)
        assignment_problems = AssignmentProblem.objects.filter(assignment=assignment)
        completed_students = 0
        if assignment_problems.exists():
            completed_students = student_assignments.filter(
                assignmentstatistics__accepted_count__gt=0
            ).annotate(
                solved_problems=Count(
                    'assignmentstatistics', 
                    filter=Q(assignmentstatistics__accepted_count__gt=0)
                )
            ).filter(solved_problems=assignment_problems.count()).count()
        
        # 平均分计算
        avg_score = AssignmentStatistics.objects.filter(
            assignment=assignment
        ).aggregate(avg_score=Avg('best_score'))['avg_score'] or 0
        
        detailed_stats = {
            'total_students': total_students,
            'submitted_students': submitted_students,
            'completion_rate': (submitted_students / total_students * 100) if total_students > 0 else 0,
            'completed_students': completed_students,
            'completion_percentage': (completed_students / total_students * 100) if total_students > 0 else 0,
            'average_score': round(avg_score, 2),
        }
        
        return Response(detailed_stats)
    
    @action(detail=True, methods=['get'], url_path='problems')
    def get_problems(self, request, pk=None):
        assignment = self.get_object()
        problems = AssignmentProblem.objects.filter(assignment=assignment)
        serializer = AssignmentProblemSerializer(problems, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='problems')
    def add_problem(self, request, pk=None):
        assignment = self.get_object()
        problem_id = request.data.get('problem_id')
        score = request.data.get('score', 0)
        
        try:
            problem = Problem.objects.get(_id=problem_id)
            assignment_problem, created = AssignmentProblem.objects.get_or_create(
                assignment=assignment,
                problem=problem,
                defaults={'score': score}
            )
            
            if not created:
                return Response({'error': '题目已存在'}, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = AssignmentProblemSerializer(assignment_problem)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Problem.DoesNotExist:
            return Response({'error': '题目不存在'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['delete'], url_path='problems/(?P<problem_id>[^/.]+)')
    def remove_problem(self, request, pk=None, problem_id=None):
        assignment = self.get_object()
        try:
            assignment_problem = AssignmentProblem.objects.get(
                assignment=assignment,
                problem__id=problem_id
            )
            assignment_problem.delete()
            return Response({'message': '删除成功'})
        except AssignmentProblem.DoesNotExist:
            return Response({'error': '题目不存在于作业中'}, status=status.HTTP_404_NOT_FOUND)


class StudentAssignmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StudentAssignment.objects.all()
    serializer_class = StudentAssignmentSerializer
    
    @action(detail=True, methods=['get'], url_path='progress')
    def get_progress(self, request, pk=None):
        student_assignment = self.get_object()
        assignment = student_assignment.assignment
        
        # 获取题目列表
        if assignment.is_personalized:
            problem_ids = student_assignment.get_personalized_problems()
            problems = Problem.objects.filter(_id__in=problem_ids)
        else:
            assignment_problems = AssignmentProblem.objects.filter(assignment=assignment)
            problem_ids = [ap.problem._id for ap in assignment_problems]
            problems = [ap.problem for ap in assignment_problems]
        
        # 获取统计数据
        statistics = AssignmentStatistics.objects.filter(
            assignment=assignment,
            student=student_assignment.student,
            problem__id__in=problem_ids
        )
        
        # 计算进度
        total_problems = len(problem_ids)
        solved_problems = statistics.filter(accepted_count__gt=0).count()
        
        progress_data = {
            'total_problems': total_problems,
            'solved_problems': solved_problems,
            'completion_rate': (solved_problems / total_problems * 100) if total_problems > 0 else 0,
            'problems': []
        }
        
        for problem in problems:
            stat = next((s for s in statistics if s.problem._id == problem._id), None)
            problem_data = {
                'id': problem._id,
                'title': problem.title,
                'submission_count': stat.submission_count if stat else 0,
                'accepted_count': stat.accepted_count if stat else 0,
                'best_score': stat.best_score if stat else 0,
                'is_solved': stat.accepted_count > 0 if stat else False
            }
            progress_data['problems'].append(problem_data)
        
        return Response(progress_data)
    
    def retrieve(self, request, *args, **kwargs):
        """
        获取单个学生作业详情
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)