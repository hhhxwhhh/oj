import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from account.models import User, UserProfile
from contest.models import Contest, ACMContestRank, OIContestRank
from problem.models import Problem
from submission.models import Submission
from utils.constants import JudgeStatus

UserModel = get_user_model()


class Command(BaseCommand):
    help = 'Generate test data for contest analytics'

    def add_arguments(self, parser):
        parser.add_argument('--contest-id', type=int, required=True, help='Contest ID to generate data for')
        parser.add_argument('--users', type=int, default=100, help='Number of users to generate (default: 100)')
        parser.add_argument('--clear', action='store_true', help='Clear existing data before generating')

    def handle(self, *args, **options):
        contest_id = options['contest_id']
        num_users = options['users']
        clear_existing = options['clear']

        try:
            contest = Contest.objects.get(id=contest_id)
        except Contest.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Contest with ID {contest_id} does not exist'))
            return

        # 如果指定了clear选项，则删除已有的参赛数据
        if clear_existing:
            self.stdout.write('Clearing existing contest data...')
            if contest.rule_type == 'ACM':
                ACMContestRank.objects.filter(contest=contest).delete()
            else:
                OIContestRank.objects.filter(contest=contest).delete()
            Submission.objects.filter(contest=contest).delete()

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
                    submission = Submission.objects.create(
                        problem=problem,
                        user=user,
                        contest=contest,
                        code=f"// Test code for problem {problem.title}\n// User: {user.username}\n// Attempt: {attempt+1}",
                        result=JudgeStatus.ACCEPTED if is_accepted else random.choice([
                            JudgeStatus.WRONG_ANSWER, 
                            JudgeStatus.TIME_LIMIT_EXCEEDED, 
                            JudgeStatus.MEMORY_LIMIT_EXCEEDED,
                            JudgeStatus.RUNTIME_ERROR
                        ]),
                        create_time=contest.start_time + (contest.end_time - contest.start_time) * random.random()
                    )
                    submissions.append(submission)
            
            # 为未解决的题目生成提交记录
            remaining_submissions = total_submissions - len(submissions)
            if remaining_submissions > 0 and unsolved_problems:
                # 从未解决的题目中随机选择
                additional_problems = random.choices(unsolved_problems, k=min(remaining_submissions, len(unsolved_problems)))
                for problem in additional_problems:
                    submission = Submission.objects.create(
                        problem=problem,
                        user=user,
                        contest=contest,
                        code=f"// Test code for problem {problem.title}\n// User: {user.username}\n// Not solved",
                        result=random.choice([
                            JudgeStatus.WRONG_ANSWER, 
                            JudgeStatus.TIME_LIMIT_EXCEEDED, 
                            JudgeStatus.MEMORY_LIMIT_EXCEEDED,
                            JudgeStatus.RUNTIME_ERROR
                        ]),
                        create_time=contest.start_time + (contest.end_time - contest.start_time) * random.random()
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