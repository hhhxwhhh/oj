import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from account.models import User, UserProfile, AdminType
from contest.models import Contest,ACMContestRank,OIContestRank
from problem.models import Problem
from submission.models import Submission, JudgeStatus

UserModel = get_user_model()


class Command(BaseCommand):
    help = 'Create a complete test contest with problems and generate test data for analytics'

    def add_arguments(self, parser):
        parser.add_argument('--title', type=str, default='Test Contest for Analytics', help='Contest title')
        parser.add_argument('--rule-type', type=str, choices=['ACM', 'OI'], default='ACM', help='Contest rule type')
        parser.add_argument('--problems', type=int, default=5, help='Number of problems to create (default: 5)')
        parser.add_argument('--users', type=int, default=100, help='Number of users to generate (default: 100)')

    def handle(self, *args, **options):
        # 获取管理员用户
        try:
            # 修复：使用正确的字段admin_type来查询超级管理员
            admin_user = User.objects.filter(admin_type=AdminType.SUPER_ADMIN).first()
            if not admin_user:
                self.stdout.write(self.style.ERROR('No admin user found. Please create an admin user first.'))
                return
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('No admin user found. Please create an admin user first.'))
            return

        # 创建竞赛
        start_time = timezone.now() - timedelta(hours=2)  # 开始2小时前
        end_time = timezone.now() + timedelta(hours=22)   # 还有22小时结束

        contest = Contest.objects.create(
            title=options['title'],
            description='This is a test contest created for analytics development and testing.',
            start_time=start_time,
            end_time=end_time,
            rule_type=options['rule_type'],
            created_by=admin_user,
            visible=True,
            real_time_rank=True
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created contest "{contest.title}" with ID {contest.id}'
            )
        )

        # 创建题目
        self.stdout.write(f'Creating {options["problems"]} problems...')
        for i in range(options['problems']):
            problem = Problem.objects.create(
                _id=f'TEST{i+1:02d}',
                contest=contest,
                is_public=True,
                title=f'Test Problem {i+1}',
                description=f'This is the description for test problem {i+1}.',
                input_description='Sample input description',
                output_description='Sample output description',
                samples=[{"input": "1 2", "output": "3"}],
                test_case_id="test_case_id",
                test_case_score=[],
                hint="This is a hint",
                languages=["C", "C++", "Java", "Python2"],
                template={},
                created_by=admin_user,
                time_limit=1000,
                memory_limit=256,
                spj=False,
                rule_type=options['rule_type'],
                visible=True,
                difficulty="Low",
                source="Test Source",
                total_score=100,
                submission_number=0,
                accepted_number=0,
                statistic_info={},
                share_submission=False
            )
            self.stdout.write(f'  Created problem: {problem.title} (ID: {problem.id})')

        # 生成用户和提交数据
        self.stdout.write(f'Generating {options["users"]} users and test data...')
        self.generate_test_data(contest.id, options['users'])

    def generate_test_data(self, contest_id, num_users):
        try:
            contest = Contest.objects.get(id=contest_id)
        except Contest.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Contest with ID {contest_id} does not exist'))
            return

        # 获取竞赛中的题目
        problems = list(contest.problem_set.all())
        if not problems:
            self.stdout.write(self.style.ERROR('No problems found in this contest'))
            return

        # 创建用户
        self.stdout.write(f'Generating {num_users} users...')
        users = []
        for i in range(num_users):
            username = f'testuser_{i+1:03d}'
            email = f'testuser_{i+1:03d}@example.com'
            
            # 创建用户
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='123456'
                )
                UserProfile.objects.create(user=user)
            
            users.append(user)

        # 为用户生成排名数据和提交记录
        self.stdout.write(f'Generating contest data for {len(users)} users...')
        
        # 预先计算时间点，确保提交时间按小时分布
        contest_duration_hours = int((contest.end_time - contest.start_time).total_seconds() / 3600)
        time_points = []
        for hour in range(contest_duration_hours + 1):
            time_point = contest.start_time + timedelta(hours=hour)
            time_points.append(time_point)
        
        for i, user in enumerate(users):
            # 模拟不同的用户表现
            # 前10%是高手，中间60%是普通用户，后30%是新手
            user_percentile = i / len(users)
            
            if user_percentile < 0.1:  # 前10% - 高手
                solved_count = random.randint(int(len(problems)*0.8), len(problems))
                total_submissions = random.randint(solved_count, solved_count + 3)
            elif user_percentile < 0.7:  # 中间60% - 普通用户
                solved_count = random.randint(int(len(problems)*0.3), int(len(problems)*0.8))
                total_submissions = random.randint(solved_count, max(solved_count + 5, int(len(problems)*1.2)))
            else:  # 后30% - 新手
                solved_count = random.randint(0, int(len(problems)*0.3))
                total_submissions = random.randint(max(1, solved_count), max(solved_count + 10, int(len(problems)*0.8)))
            
            # 确保解决题目数不超过总题目数
            solved_count = min(solved_count, len(problems))
            
            # 随机选择解决的题目
            solved_problems = random.sample(problems, solved_count)
            unsolved_problems = [p for p in problems if p not in solved_problems]
            
            # 生成提交记录
            submissions = []
            for problem in solved_problems:
                # 每个解决的题目有1-3次提交
                attempts = random.randint(1, 3)
                for attempt in range(attempts):
                    is_accepted = (attempt == attempts - 1)  # 最后一次提交是AC
                    # 按小时分布提交时间，而不是完全随机
                    hour_offset = random.randint(0, contest_duration_hours)
                    create_time = contest.start_time + timedelta(hours=hour_offset, 
                                                                minutes=random.randint(0, 59),
                                                                seconds=random.randint(0, 59))
                    
                    submission = Submission.objects.create(
                        problem=problem,
                        user_id=user.id,
                        contest=contest,
                        code=f"// Test code for problem {problem.title}\n// User: {user.username}\n// Attempt: {attempt+1}",
                        result=JudgeStatus.ACCEPTED if is_accepted else random.choice([
                            JudgeStatus.WRONG_ANSWER, 
                            JudgeStatus.CPU_TIME_LIMIT_EXCEEDED, 
                            JudgeStatus.MEMORY_LIMIT_EXCEEDED,
                            JudgeStatus.RUNTIME_ERROR
                        ]),
                        create_time=create_time
                    )
                    submissions.append(submission)
            
            # 为未解决的题目生成提交记录
            remaining_submissions = total_submissions - len(submissions)
            if remaining_submissions > 0 and unsolved_problems:
                # 从未解决的题目中随机选择
                additional_problems = random.choices(unsolved_problems, k=min(remaining_submissions, len(unsolved_problems)))
                for problem in additional_problems:
                    # 按小时分布提交时间
                    hour_offset = random.randint(0, contest_duration_hours)
                    create_time = contest.start_time + timedelta(hours=hour_offset, 
                                                                minutes=random.randint(0, 59),
                                                                seconds=random.randint(0, 59))
                    
                    submission = Submission.objects.create(
                        problem=problem,
                        user_id=user.id,
                        contest=contest,
                        code=f"// Test code for problem {problem.title}\n// User: {user.username}\n// Not solved",
                        result=random.choice([
                            JudgeStatus.WRONG_ANSWER, 
                            JudgeStatus.CPU_TIME_LIMIT_EXCEEDED, 
                            JudgeStatus.MEMORY_LIMIT_EXCEEDED,
                            JudgeStatus.RUNTIME_ERROR
                        ]),
                        create_time=create_time
                    )
                    submissions.append(submission)
            
            # 生成排名数据
            if contest.rule_type == 'ACM':
                # ACM规则：计算AC数量和总时间
                accepted_count = sum(1 for s in submissions if s.result == JudgeStatus.ACCEPTED)
                total_time = 0
                submission_info = {}
                
                # 计算每道题的时间
                problem_submissions = {}
                for submission in submissions:
                    pid = str(submission.problem.id)
                    if pid not in problem_submissions:
                        problem_submissions[pid] = []
                    problem_submissions[pid].append(submission)
                
                for pid, subs in problem_submissions.items():
                    # 找到第一个AC的提交
                    ac_sub = next((s for s in subs if s.result == JudgeStatus.ACCEPTED), None)
                    if ac_sub:
                        # 计算从比赛开始到AC的时间（分钟）
                        time_minutes = int((ac_sub.create_time - contest.start_time).total_seconds() / 60)
                        # 计算错误次数
                        error_count = sum(1 for s in subs if s.result != JudgeStatus.ACCEPTED)
                        # 总时间 = AC时间 + 错误次数*20分钟
                        total_time += time_minutes + error_count * 20
                        
                        submission_info[pid] = {
                            "is_ac": True,
                            "ac_time": time_minutes,
                            "error_number": error_count,
                            "is_first_ac": False  # 简化处理
                        }
                
                # 创建ACM排名记录
                ACMContestRank.objects.create(
                    user=user,
                    contest=contest,
                    submission_number=len(submissions),
                    accepted_number=accepted_count,
                    total_time=total_time,
                    submission_info=submission_info
                )
            else:  # OI规则
                # OI规则：计算总分
                total_score = 0
                submission_info = {}
                
                # 按题目分组提交
                problem_scores = {}
                for submission in submissions:
                    pid = str(submission.problem.id)
                    # OI比赛中，每个题目可能有部分分数
                    if submission.result == JudgeStatus.ACCEPTED:
                        score = 100  # 满分
                    else:
                        score = random.randint(0, 60)  # 部分分数
                    
                    # 取每个题目的最高分
                    if pid not in problem_scores or problem_scores[pid] < score:
                        problem_scores[pid] = score
                
                total_score = sum(problem_scores.values())
                
                # 转换为submission_info格式
                for pid, score in problem_scores.items():
                    submission_info[pid] = score
                
                # 创建OI排名记录
                OIContestRank.objects.create(
                    user=user,
                    contest=contest,
                    submission_number=len(submissions),
                    total_score=total_score,
                    submission_info=submission_info
                )
            
            # 显示进度
            if (i + 1) % 10 == 0 or i == len(users) - 1:
                self.stdout.write(f'Progress: {i+1}/{len(users)} users processed')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully generated test data for {len(users)} users in contest "{contest.title}"'
            )
        )