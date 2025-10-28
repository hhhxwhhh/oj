import random
from django.core.management.base import BaseCommand
from django.db import transaction
from account.models import User, UserProfile, AdminType
from problem.models import Problem
from submission.models import Submission, JudgeStatus
from contest.models import ContestRuleType
from utils.shortcuts import rand_str


class Command(BaseCommand):
    help = '生成OI排名测试数据'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=50, help='要生成的普通用户数量')
        parser.add_argument('--problems', type=int, default=20, help='要生成的题目数量')
        parser.add_argument('--submissions', type=int, default=1000, help='要生成的提交记录总数')

    def handle(self, *args, **options):
        users_count = options['users']
        problems_count = options['problems']
        submissions_count = options['submissions']

        self.stdout.write(f'开始生成OI排名测试数据...')
        self.stdout.write(f'用户数量: {users_count}, 题目数量: {problems_count}, 提交记录: {submissions_count}')

        # 获取或创建普通用户
        regular_users = User.objects.filter(admin_type=AdminType.REGULAR_USER, is_disabled=False)
        if regular_users.count() < users_count:
            self.stdout.write(f'现有普通用户不足，创建 {users_count - regular_users.count()} 个新用户...')
            for i in range(users_count - regular_users.count()):
                username = f'oi_test_user_{rand_str(6)}'
                user = User.objects.create(
                    username=username,
                    email=f'{username}@test.com',
                    admin_type=AdminType.REGULAR_USER
                )
                user.set_password('123456')
                user.save()
                UserProfile.objects.create(user=user, real_name=f'OI测试用户{i+1}')

        # 确保所有普通用户都有UserProfile
        regular_users = User.objects.filter(admin_type=AdminType.REGULAR_USER, is_disabled=False)
        users_without_profile = []
        for user in regular_users:
            try:
                profile = user.userprofile
            except UserProfile.DoesNotExist:
                users_without_profile.append(user)
        
        if users_without_profile:
            self.stdout.write(f'发现 {len(users_without_profile)} 个用户没有UserProfile，正在创建...')
            for user in users_without_profile:
                UserProfile.objects.create(user=user, real_name=f'自动创建用户{user.id}')
        
        regular_users = User.objects.filter(admin_type=AdminType.REGULAR_USER, is_disabled=False)
        self.stdout.write(f'可用普通用户数量: {regular_users.count()}')

        # 获取或创建OI题目
        oi_problems = Problem.objects.filter(visible=True, contest_id__isnull=True)
        if oi_problems.count() < problems_count:
            self.stdout.write(f'现有题目不足，创建 {problems_count - oi_problems.count()} 个新题目...')
            for i in range(problems_count - oi_problems.count()):
                problem = Problem.objects.create(
                    _id=f'OI{rand_str(4)}',
                    title=f'OI测试题目{i+1}',
                    description=f'这是第{i+1}个OI测试题目',
                    input_description='输入描述',
                    output_description='输出描述',
                    samples=[],
                    test_case_id=rand_str(10),
                    test_case_score=[{"score": 100, "input_name": "1.in", "output_name": "1.out"}],
                    hint='',
                    time_limit=1000,
                    memory_limit=256,
                    difficulty='Low',
                    created_by=User.objects.filter(admin_type=AdminType.SUPER_ADMIN).first(),
                    rule_type=ContestRuleType.OI,
                    total_score=100,
                    submission_number=0,
                    accepted_number=0,
                    statistic_info={}
                )
                problem.save()

        oi_problems = Problem.objects.filter(visible=True, contest_id__isnull=True)
        self.stdout.write(f'可用题目数量: {oi_problems.count()}')

        # 生成提交记录
        self.stdout.write('开始生成提交记录...')
        created_count = 0
        
        with transaction.atomic():
            for i in range(submissions_count):
                user = random.choice(list(regular_users))
                problem = random.choice(list(oi_problems))
                
                # OI模式下，随机生成分数（0-100）
                score = random.randint(0, 100)
                # 根据分数决定结果状态
                if score == 100:
                    result = JudgeStatus.ACCEPTED
                elif score >= 60:
                    result = random.choice([JudgeStatus.WRONG_ANSWER, JudgeStatus.CPU_TIME_LIMIT_EXCEEDED, 
                                          JudgeStatus.MEMORY_LIMIT_EXCEEDED, JudgeStatus.RUNTIME_ERROR])
                else:
                    result = random.choice([JudgeStatus.WRONG_ANSWER, JudgeStatus.COMPILE_ERROR, 
                                          JudgeStatus.SYSTEM_ERROR, JudgeStatus.PARTIALLY_ACCEPTED])
                
                submission = Submission.objects.create(
                    user_id=user.id,
                    username=user.username,
                    code=rand_str(100),
                    result=result,
                    info={},
                    language='C++',
                    problem_id=problem.id,
                    ip='127.0.0.1',
                    contest_id=None,
                    statistic_info={'score': score, 'time_cost': random.randint(100, 5000), 
                                  'memory_cost': random.randint(1000, 256000)}
                )
                
                # 更新用户统计信息
                profile = user.userprofile
                profile.submission_number += 1
                if result == JudgeStatus.ACCEPTED:
                    profile.accepted_number += 1
                profile.total_score += score
                profile.save(update_fields=['submission_number', 'accepted_number', 'total_score'])
                
                # 更新题目统计信息
                problem.submission_number += 1
                if result == JudgeStatus.ACCEPTED:
                    problem.accepted_number += 1
                problem.save(update_fields=['submission_number', 'accepted_number'])
                
                created_count += 1
                if created_count % 100 == 0:
                    self.stdout.write(f'已生成 {created_count} 条提交记录...')

        self.stdout.write(
            self.style.SUCCESS(
                f'成功生成OI排名测试数据！\n'
                f'用户数量: {regular_users.count()}\n'
                f'题目数量: {oi_problems.count()}\n'
                f'提交记录: {created_count}\n'
                f'现在可以在OI排名页面查看效果。'
            )
        )
