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
from django.db.models import Count,Sum,Avg,Q,Max
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from utils.shortcuts import datetime2str
from django.db import models
from django.contrib.contenttypes.models import ContentType


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
        total_students = StudentAssignment.objects.filter(assignment=assignment).count()
        
        # 获取已提交的学生数
        submitted_students = AssignmentStatistics.objects.filter(
            assignment=assignment,
            submission_count__gt=0
        ).values('student').distinct().count()
        
        # 获取已完成的学生数 (所有题目都已通过)
        assignment_problems = AssignmentProblem.objects.filter(assignment=assignment)
        completed_students = 0
        if assignment_problems.exists():
            completed_students = AssignmentStatistics.objects.filter(
                assignment=assignment,
                accepted_count__gt=0
            ).values('student').annotate(
                solved_problems=Count('id')
            ).filter(solved_problems=assignment_problems.count()).count()
        
        # 平均分计算
        avg_score_result = AssignmentStatistics.objects.filter(
            assignment=assignment
        ).aggregate(avg_score=Avg('best_score'))
        avg_score = avg_score_result['avg_score'] or 0 if avg_score_result['avg_score'] is not None else 0
        
        detailed_stats = {
            'total_students': total_students,
            'submitted_students': submitted_students,
            'completion_rate': round((submitted_students / total_students * 100) if total_students > 0 else 0, 2),
            'completed_students': completed_students,
            'completion_percentage': round((completed_students / total_students * 100) if total_students > 0 else 0, 2),
            'average_score': round(avg_score, 2),
        }
        
        return Response(detailed_stats)

    

    @action(detail=True, methods=['get'], url_path='problem-difficulty-statistics')
    def get_problem_difficulty_statistics(self, request, pk=None):
        """
        按题目难度获取统计信息
        """
        assignment = self.get_object()
        
        # 获取作业中的所有题目及其难度
        assignment_problems = AssignmentProblem.objects.filter(assignment=assignment).select_related('problem')
        
        difficulty_stats = {}
        for ap in assignment_problems:
            problem = ap.problem
            difficulty = problem.difficulty if problem.difficulty else 'Unknown'
            
            if difficulty not in difficulty_stats:
                difficulty_stats[difficulty] = {
                    'difficulty': difficulty,
                    'total_problems': 0,
                    'total_submissions': 0,
                    'accepted_submissions': 0,
                    'average_score': 0,
                    'acceptance_rate': 0
                }
            
            difficulty_stats[difficulty]['total_problems'] += 1
            
            # 获取该题目的统计数据
            stats = AssignmentStatistics.objects.filter(
                assignment=assignment,
                problem=problem
            )
            
            total_submissions = stats.count()
            accepted_submissions = stats.filter(accepted_count__gt=0).count()
            
            difficulty_stats[difficulty]['total_submissions'] += total_submissions
            difficulty_stats[difficulty]['accepted_submissions'] += accepted_submissions
            
            # 计算平均分
            avg_score = stats.aggregate(avg=Avg('best_score'))['avg'] or 0
            difficulty_stats[difficulty]['average_score'] += avg_score
        
        # 计算整体统计数据
        result = []
        for difficulty, stats in difficulty_stats.items():
            if stats['total_problems'] > 0:
                stats['average_score'] = round(stats['average_score'] / stats['total_problems'], 2)
            if stats['total_submissions'] > 0:
                stats['acceptance_rate'] = round(
                    (stats['accepted_submissions'] / stats['total_submissions']) * 100, 2
                )
            result.append(stats)
        
        return Response(result)

    @action(detail=True, methods=['get'], url_path='student-performance-trend')
    def get_student_performance_trend(self, request, pk=None):
        """
        获取学生表现趋势（按时间）
        """
        assignment = self.get_object()
        
        # 获取最近一段时间内的统计数据
        recent_stats = AssignmentStatistics.objects.filter(
            assignment=assignment,
            create_time__gte=timezone.now() - timezone.timedelta(days=30)
        ).extra(select={'date': 'DATE(create_time)'}).values('date').annotate(
            daily_submissions=Count('id'),
            daily_accepted=Count('id', filter=Q(accepted_count__gt=0)),
            avg_score=Avg('best_score')
        ).order_by('date')
        
        trend_data = []
        for stat in recent_stats:
            trend_data.append({
                'date': stat['date'],
                'submissions': stat['daily_submissions'],
                'accepted': stat['daily_accepted'],
                'acceptance_rate': round(
                    (stat['daily_accepted'] / stat['daily_submissions'] * 100) if stat['daily_submissions'] > 0 else 0, 2
                ),
                'average_score': round(stat['avg_score'] or 0, 2)
            })
        
        return Response(trend_data)

    @action(detail=True, methods=['get'], url_path='top-performing-students')
    def get_top_performing_students(self, request, pk=None):
        """
        获取表现最好的学生
        """
        assignment = self.get_object()
        
        # 获取所有分配给学生的作业
        student_assignments = StudentAssignment.objects.filter(assignment=assignment)
        
        top_students = []
        for sa in student_assignments:
            student = sa.student
            
            # 获取该学生的统计数据
            stats = AssignmentStatistics.objects.filter(
                assignment=assignment,
                student=student
            )
            
            # 计算总分和解决的题目数
            total_score = stats.aggregate(total=Sum('best_score'))['total'] or 0
            solved_problems = stats.filter(accepted_count__gt=0).count()
            total_submissions = stats.count()
            
            # 计算平均分
            avg_score = stats.aggregate(avg=Avg('best_score'))['avg'] or 0
            
            top_students.append({
                'student_id': student.id,
                'student_username': student.username,
                'student_real_name': student.real_name or '',
                'total_score': round(total_score, 2),
                'solved_problems': solved_problems,
                'total_submissions': total_submissions,
                'average_score': round(avg_score, 2),
                'completion_rate': round(
                    (solved_problems / assignment.assignmentproblem_set.count() * 100) 
                    if assignment.assignmentproblem_set.count() > 0 else 0, 2
                )
            })
        
        # 按总分排序，取前10名
        top_students.sort(key=lambda x: x['total_score'], reverse=True)
        
        return Response(top_students[:10])

    @action(detail=True, methods=['get'], url_path='export-statistics')
    def export_statistics(self, request, pk=None):
        """
        导出作业统计信息（CSV格式）
        """
        assignment = self.get_object()
        
        try:
            # 获取详细统计信息
            detailed_stats_response = self.get_detailed_statistics(request, pk)
            detailed_stats = detailed_stats_response.data
            
            # 获取题目统计信息
            problem_stats_response = self.get_problem_statistics(request, pk)
            problem_stats = problem_stats_response.data if hasattr(problem_stats_response, 'data') else []
            
            # 获取学生排名
            student_rankings_response = self.get_student_ranking(request, pk)
            student_rankings = student_rankings_response.data if hasattr(student_rankings_response, 'data') else []
            
            # 组合导出数据
            export_data = {
                'assignment_info': {
                    'id': assignment.id,
                    'title': assignment.title,
                    'creator': assignment.creator.username,
                    'start_time': assignment.start_time,
                    'end_time': assignment.end_time
                },
                'summary': detailed_stats,
                'problem_statistics': problem_stats,
                'student_rankings': student_rankings
            }
            
            return Response(export_data)
        except Exception as e:
            # 记录错误日志
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"导出统计数据失败: {str(e)}")
            
            return Response(
                {'error': '导出统计数据失败'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'], url_path='problems')
    def get_problems(self, request, pk=None):
        assignment = self.get_object()
        problems = AssignmentProblem.objects.filter(assignment=assignment)
        serializer = AssignmentProblemSerializer(problems, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='problems/add')
    def add_problem(self, request, pk=None):
        assignment = self.get_object()
        problem_id = request.data.get('problem_id')
        score = request.data.get('score', 0)
        
        try:
            try:
                problem = Problem.objects.get(_id=problem_id, contest=None)
            except Problem.DoesNotExist:
                problems = Problem.objects.filter(_id=problem_id)
                if problems.count() == 0:
                    raise Problem.DoesNotExist
                elif problems.count() == 1:
                    problem = problems.first()
                else:
                    public_problems = problems.filter(contest=None)
                    if public_problems.exists():
                        problem = public_problems.first()
                    else:
                        # 如果没有公开题目，返回第一个
                        problem = problems.first()
            
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
        
    @action(detail=True, methods=['post'], url_path='send-reminder')
    def send_reminder(self, request, pk=None):
        """
        发送作业提醒给未提交的学生
        """
        assignment = self.get_object()
        
        # 获取已分配但未提交的学生
        student_assignments = StudentAssignment.objects.filter(assignment=assignment)
        submitted_students = student_assignments.filter(
            assignmentstatistics__submission_count__gt=0
        ).values_list('student_id', flat=True)
        
        # 找出未提交的学生
        unsubmitted_students = student_assignments.exclude(
            student_id__in=submitted_students
        ).select_related('student')
        
        reminder_count = 0
        failed_count = 0
        
        for student_assignment in unsubmitted_students:
            student = student_assignment.student
            try:
                # 发送邮件提醒
                if student.email:
                    subject = f"作业提醒: {assignment.title}"
                    message = render_to_string('assignment/reminder_email.html', {
                        'student': student,
                        'assignment': assignment,
                        'due_date': datetime2str(assignment.end_time) if assignment.end_time else "无截止日期"
                    })
                    
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [student.email],
                        fail_silently=False,
                    )
                    reminder_count += 1
            except Exception as e:
                failed_count += 1
                # 记录错误日志
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"发送提醒邮件失败: {str(e)}")
        
        return Response({
            'message': f'成功发送{reminder_count}份提醒，{failed_count}份发送失败',
            'success_count': reminder_count,
            'failed_count': failed_count
        })
    
    @action(detail=True, methods=['post'], url_path='extend-deadline')
    def extend_deadline(self, request, pk=None):
        """
        延长作业截止日期
        """
        assignment = self.get_object()
        new_end_time = request.data.get('new_end_time')
        
        if not new_end_time:
            return Response(
                {'error': '请提供新的截止日期'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 更新截止日期
            assignment.end_time = new_end_time
            assignment.save()
            
            # 获取所有分配的学生
            student_assignments = StudentAssignment.objects.filter(assignment=assignment)
            
            # 更新学生作业状态（如果之前是过期状态）
            for student_assignment in student_assignments:
                if student_assignment.status == 'expired':
                    student_assignment.status = 'assigned'
                    student_assignment.save()
            
            return Response({
                'message': '截止日期延长成功',
                'new_end_time': assignment.end_time
            })
        except Exception as e:
            return Response(
                {'error': f'更新截止日期失败: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
    @action(detail=True, methods=['get'], url_path='plagiarism-check')
    def plagiarism_check(self, request, pk=None):
        """
        作业抄袭检查
        """
        assignment = self.get_object()
        
        # 获取所有提交的代码
        statistics = AssignmentStatistics.objects.filter(
            assignment=assignment
        ).exclude(code='').select_related('student', 'problem')
        
        # 简化的抄袭检查逻辑
        # 在实际应用中，这里应该使用更复杂的算法
        plagiarism_results = []
        
        # 按题目分组检查
        problems = {}
        for stat in statistics:
            problem_id = stat.problem_id
            if problem_id not in problems:
                problems[problem_id] = []
            problems[problem_id].append(stat)
        
        # 检查每个题目的提交
        for problem_id, stats in problems.items():
            if len(stats) < 2:
                continue
                
            # 比较每对提交
            for i in range(len(stats)):
                for j in range(i + 1, len(stats)):
                    stat1 = stats[i]
                    stat2 = stats[j]
                    
                    # 简单的字符串相似度检查（实际应用中应使用更复杂的算法）
                    similarity = self._calculate_similarity(stat1.code, stat2.code)
                    
                    if similarity > 0.8:  # 相似度超过80%认为可能抄袭
                        plagiarism_results.append({
                            'problem_id': problem_id,
                            'problem_title': stat1.problem.title,
                            'student1': {
                                'id': stat1.student.id,
                                'username': stat1.student.username,
                                'real_name': stat1.student.real_name
                            },
                            'student2': {
                                'id': stat2.student.id,
                                'username': stat2.student.username,
                                'real_name': stat2.student.real_name
                            },
                            'similarity': round(similarity * 100, 2),
                            'code1_preview': stat1.code[:200] + '...' if len(stat1.code) > 200 else stat1.code,
                            'code2_preview': stat2.code[:200] + '...' if len(stat2.code) > 200 else stat2.code
                        })
        
        return Response({
            'assignment_id': assignment.id,
            'assignment_title': assignment.title,
            'total_submissions_checked': statistics.count(),
            'plagiarism_cases_found': len(plagiarism_results),
            'results': plagiarism_results
        })
    def _calculate_similarity(self, code1, code2):
        """
        计算两个代码字符串的相似度（简化实现）
        """
        # 移除空白字符和注释的简化版本
        def normalize_code(code):
            # 简单移除空白字符
            return ''.join(code.split())
        
        normalized_code1 = normalize_code(code1)
        normalized_code2 = normalize_code(code2)
        
        if not normalized_code1 and not normalized_code2:
            return 1.0
        if not normalized_code1 or not normalized_code2:
            return 0.0
            
        common_chars = 0
        total_chars = max(len(normalized_code1), len(normalized_code2))
        
        # 简单的字符匹配
        for i in range(min(len(normalized_code1), len(normalized_code2))):
            if normalized_code1[i] == normalized_code2[i]:
                common_chars += 1
                
        return common_chars / total_chars if total_chars > 0 else 0
    @action(detail=True, methods=['post'], url_path='auto-grade')
    def auto_grade(self, request, pk=None):
        """
        自动作业评分
        """
        assignment = self.get_object()
        
        # 获取所有已提交的学生作业
        student_assignments = StudentAssignment.objects.filter(assignment=assignment)
        
        graded_count = 0
        error_count = 0
        
        for student_assignment in student_assignments:
            try:
                # 获取该学生的统计数据
                stats = AssignmentStatistics.objects.filter(
                    assignment=assignment,
                    student=student_assignment.student
                )
                
                if not stats.exists():
                    continue
                
                # 计算总分
                total_score = 0
                max_possible_score = 0
                
                # 获取作业中所有题目的分数
                assignment_problems = AssignmentProblem.objects.filter(assignment=assignment)
                
                for ap in assignment_problems:
                    max_possible_score += ap.score or 0
                    
                    # 查找该学生该题的统计数据
                    problem_stat = stats.filter(problem=ap.problem).first()
                    if problem_stat and problem_stat.accepted_count > 0:
                        # 如果题目通过，给予满分
                        total_score += ap.score or 0
                    elif problem_stat:
                        # 如果有提交但未通过，根据测试用例通过率给部分分数
                        if problem_stat.total_testcases > 0:
                            pass_rate = problem_stat.accepted_testcases / problem_stat.total_testcases
                            total_score += (ap.score or 0) * pass_rate
                
                # 更新学生作业的总分
                student_assignment.score = round(total_score, 2)
                student_assignment.max_score = max_possible_score
                
                # 更新状态
                if total_score >= max_possible_score:
                    student_assignment.status = 'completed'
                elif total_score > 0:
                    student_assignment.status = 'in_progress'
                else:
                    student_assignment.status = 'assigned'
                
                student_assignment.save()
                graded_count += 1
                
            except Exception as e:
                error_count += 1
                # 记录错误日志
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"自动评分失败 (学生作业ID: {student_assignment.id}): {str(e)}")
        
        return Response({
            'message': f'自动评分完成：成功评分{graded_count}份作业，{error_count}份评分失败',
            'graded_count': graded_count,
            'error_count': error_count
        })
    @action(detail=True, methods=['get'], url_path='grade-distribution')
    def grade_distribution(self, request, pk=None):
        """
        获取成绩分布
        """
        assignment = self.get_object()
        
        # 获取所有学生作业
        student_assignments = StudentAssignment.objects.filter(assignment=assignment)
        
        # 计算成绩分布
        grade_ranges = {
            '90-100': 0,
            '80-89': 0,
            '70-79': 0,
            '60-69': 0,
            '0-59': 0
        }
        
        total_students = student_assignments.count()
        graded_students = 0
        average_score = 0
        
        for sa in student_assignments:
            if sa.max_score and sa.score is not None:
                graded_students += 1
                percentage = (sa.score / sa.max_score) * 100
                average_score += percentage
                
                if percentage >= 90:
                    grade_ranges['90-100'] += 1
                elif percentage >= 80:
                    grade_ranges['80-89'] += 1
                elif percentage >= 70:
                    grade_ranges['70-79'] += 1
                elif percentage >= 60:
                    grade_ranges['60-69'] += 1
                else:
                    grade_ranges['0-59'] += 1
        
        if graded_students > 0:
            average_score = round(average_score / graded_students, 2)
        
        return Response({
            'assignment_id': assignment.id,
            'assignment_title': assignment.title,
            'total_students': total_students,
            'graded_students': graded_students,
            'ungraded_students': total_students - graded_students,
            'average_percentage': average_score,
            'grade_distribution': grade_ranges
        })
    @action(detail=True, methods=['post'], url_path='send-feedback')
    def send_feedback(self, request, pk=None):
        """
        发送作业反馈给所有学生
        """
        assignment = self.get_object()
        feedback_message = request.data.get('feedback_message', '')
        send_to_all = request.data.get('send_to_all', False)
        student_ids = request.data.get('student_ids', [])
        
        if not feedback_message:
            return Response(
                {'error': '请提供反馈内容'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 确定发送对象
        if send_to_all:
            student_assignments = StudentAssignment.objects.filter(assignment=assignment)
        else:
            student_assignments = StudentAssignment.objects.filter(
                assignment=assignment,
                student_id__in=student_ids
            )
        
        success_count = 0
        failed_count = 0
        
        for student_assignment in student_assignments:
            student = student_assignment.student
            try:
                # 发送反馈邮件
                if student.email:
                    subject = f"作业反馈: {assignment.title}"
                    message = render_to_string('assignment/feedback_email.html', {
                        'student': student,
                        'assignment': assignment,
                        'feedback_message': feedback_message,
                        'score': student_assignment.score,
                        'max_score': student_assignment.max_score
                    })
                    
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [student.email],
                        fail_silently=False,
                    )
                    success_count += 1
            except Exception as e:
                failed_count += 1
                # 记录错误日志
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"发送反馈邮件失败: {str(e)}")
        
        return Response({
            'message': f'反馈发送完成：成功发送{success_count}份，失败{failed_count}份',
            'success_count': success_count,
            'failed_count': failed_count
        })
    @action(detail=True, methods=['get'], url_path='export-report')
    def export_report(self, request, pk=None):
        """
        导出详细的作业报告（Excel格式数据）
        """
        assignment = self.get_object()
        
        # 获取作业基本信息
        assignment_info = {
            'id': assignment.id,
            'title': assignment.title,
            'description': assignment.description,
            'creator': assignment.creator.username,
            'start_time': assignment.start_time,
            'end_time': assignment.end_time,
            'create_time': assignment.create_time
        }
        
        # 获取题目信息
        assignment_problems = AssignmentProblem.objects.filter(assignment=assignment).select_related('problem')
        problems_data = []
        for ap in assignment_problems:
            problems_data.append({
                'id': ap.problem._id,
                'title': ap.problem.title,
                'score': ap.score
            })
        
        # 获取学生作业信息
        student_assignments = StudentAssignment.objects.filter(assignment=assignment).select_related('student')
        students_data = []
        for sa in student_assignments:
            # 获取该学生的题目完成情况
            stats = AssignmentStatistics.objects.filter(
                assignment=assignment,
                student=sa.student
            )
            
            problem_details = []
            for stat in stats:
                problem_details.append({
                    'problem_id': stat.problem._id,
                    'problem_title': stat.problem.title,
                    'best_score': stat.best_score,
                    'submission_count': stat.submission_count,
                    'is_accepted': stat.accepted_count > 0
                })
            
            students_data.append({
                'student_id': sa.student.id,
                'username': sa.student.username,
                'real_name': sa.student.real_name,
                'status': sa.status,
                'score': sa.score,
                'max_score': sa.max_score,
                'problems': problem_details
            })
        
        # 组织导出数据
        export_data = {
            'assignment': assignment_info,
            'problems': problems_data,
            'students': students_data
        }
        
        return Response(export_data)

    @action(detail=True, methods=['get'], url_path='problem-statistics')
    def get_problem_statistics(self, request, pk=None):
        """
        获取题目的统计信息
        """
        assignment = self.get_object()
        
        # 获取作业中的所有题目
        assignment_problems = AssignmentProblem.objects.filter(assignment=assignment).select_related('problem')
        
        problem_stats = []
        for ap in assignment_problems:
            problem = ap.problem
            
            # 获取这道题的所有提交统计
            stats = AssignmentStatistics.objects.filter(
                assignment=assignment,
                problem=problem
            )
            
            total_submissions = stats.count()
            accepted_submissions = stats.filter(accepted_count__gt=0).count()
            
            # 计算平均分
            avg_score = stats.aggregate(avg=Avg('best_score'))['avg'] or 0
            
            acceptance_rate = (accepted_submissions / total_submissions * 100) if total_submissions > 0 else 0
            
            problem_stats.append({
                'problem_id': problem._id,
                'problem_title': problem.title,
                'total_submissions': total_submissions,
                'accepted_submissions': accepted_submissions,
                'acceptance_rate': round(acceptance_rate, 2),
                'average_score': round(avg_score, 2)
            })
        
        return Response(problem_stats)
    @action(detail=True, methods=['get'], url_path='student-ranking')
    def get_student_ranking(self, request, pk=None):
        """
        获取学生排名
        """
        assignment = self.get_object()
        
        # 获取所有学生作业
        student_assignments = StudentAssignment.objects.filter(
            assignment=assignment
        ).select_related('student').order_by('-score')
        
        rankings = []
        for i, sa in enumerate(student_assignments):
            # 只包含有分数的学生
            if sa.score is not None and sa.max_score is not None:
                rankings.append({
                    'rank': i + 1,
                    'student_id': sa.student.id,
                    'student_username': sa.student.username,
                    'student_real_name': sa.student.real_name or '',
                    'score': sa.score,
                    'max_score': sa.max_score,
                    'percentage': round((sa.score / sa.max_score) * 100, 2) if sa.max_score and sa.max_score > 0 else 0
                })
        
        return Response(rankings)



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