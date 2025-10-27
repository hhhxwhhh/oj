import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from problem.models import Problem, ProblemTag
from submission.models import Submission
from account.models import User
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '生成大量测试数据用于AI推荐系统测试'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=50, help='要创建的用户数量')
        parser.add_argument('--problems', type=int, default=100, help='要创建的题目数量')
        parser.add_argument('--submissions', type=int, default=1000, help='要创建的提交记录数量')
        parser.add_argument('--contests', type=int, default=10, help='要创建的比赛数量')
        parser.add_argument('--complexity', type=str, default='medium', 
                           choices=['simple', 'medium', 'complex'],
                           help='数据复杂度级别')

    def handle(self, *args, **options):
        user_count = options['users']
        problem_count = options['problems']
        submission_count = options['submissions']
        contest_count = options['contests']
        complexity = options['complexity']

        # 根据复杂度调整参数
        if complexity == 'complex':
            user_count *= 2
            problem_count *= 3
            submission_count *= 5
        elif complexity == 'simple':
            user_count //= 2
            problem_count //= 2
            submission_count //= 5

        # 创建标签
        self.create_tags()
        
        # 创建用户
        self.create_users(user_count)
        
        # 创建题目
        self.create_problems(problem_count)
        
        # 创建比赛
        self.create_contests(contest_count)
        
        # 创建提交记录
        self.create_submissions(submission_count)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'成功创建 {len(self.users)} 个用户, {len(self.problems)} 个题目, '
                f'{contest_count} 场比赛, {self.submission_count} 条提交记录'
            )
        )

    def create_tags(self):
        """创建测试标签"""
        tags_data = [
            '数组', '链表', '栈', '队列', '树', '图', '哈希表', '堆', 
            '排序', '搜索', '动态规划', '贪心算法', '回溯', '分治',
            '位运算', '数学', '字符串', '模拟', '递归', '滑动窗口',
            '并查集', '线段树', '字典树', '几何', '博弈论', '数论',
            '计算几何', '网络流', '字符串匹配', '概率论'
        ]
        
        tags = []
        for tag_name in tags_data:
            tag, created = ProblemTag.objects.get_or_create(name=tag_name)
            tags.append(tag)
        
        self.tags = tags
        self.stdout.write(f'创建了 {len(tags)} 个标签')

    def create_users(self, count):
        """创建测试用户"""
        User = get_user_model()
        self.users = []
        
        # 创建不同类型的用户
        admin_count = max(1, count // 20)
        regular_count = count - admin_count
        
        # 创建普通用户
        for i in range(regular_count):
            username = f'user_{i}'
            email = f'user_{i}@example.com'
            
            try:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='testpassword123'
                )
                self.users.append(user)
            except Exception as e:
                # 用户可能已存在
                try:
                    user = User.objects.get(username=username)
                    self.users.append(user)
                except User.DoesNotExist:
                    continue
        
        # 创建管理员用户
        for i in range(admin_count):
            username = f'admin_{i}'
            email = f'admin_{i}@example.com'
            
            try:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='adminpassword123',
                    admin_type='Admin',
                    problem_permission='All'
                )
                self.users.append(user)
            except Exception as e:
                try:
                    user = User.objects.get(username=username)
                    self.users.append(user)
                except User.DoesNotExist:
                    continue
        
        self.stdout.write(f'创建了 {len(self.users)} 个用户 ({regular_count} 普通用户, {admin_count} 管理员)')

    def create_problems(self, count):
        """创建测试题目"""
        self.problems = []
        
        difficulties = [0, 1, 2]  # 低、中、高难度
        rule_types = ['ACM', 'OI']
        
        for i in range(count):
            problem_id = 1000 + i  # 避免与现有题目冲突
            
            try:
                problem = Problem.objects.create(
                    _id=problem_id,
                    title=f'测试题目 {i}: 算法练习',
                    description=f'<p>这是第 {i} 个测试题目的详细描述。题目要求解决一个典型的算法问题，涉及数据结构和算法设计。</p><p>请仔细阅读题目要求并实现正确的解决方案。</p>',
                    input_description='<p>输入包含多个测试用例。第一行是一个整数T，表示测试用例的数量。每个测试用例的第一行是...</p>',
                    output_description='<p>对于每个测试用例，输出一行包含一个整数的结果。</p>',
                    hint='<p>提示：可以考虑使用特定的数据结构来优化算法复杂度。注意边界条件处理。</p>',
                    difficulty=random.choice(difficulties),
                    source='测试来源',
                    time_limit=random.choice([1000, 2000, 3000, 5000]),
                    memory_limit=random.choice([64, 128, 256, 512]),
                    accepted_number=random.randint(0, 500),
                    submission_number=random.randint(0, 1000),
                    visible=True,
                    rule_type=random.choice(rule_types),
                    spj=random.choice([True, False]),
                    total_score=random.choice([100, 150, 200]) if 'OI' else 0,
                    languages=["C", "C++", "Java", "Python2", "Python3"],
                    samples=[
                        {"input": "3\n1 2 3", "output": "6"},
                        {"input": "5\n1 1 1 1 1", "output": "5"}
                    ],
                    test_case_id=f"test_case_{problem_id}",
                    test_case_score=[{"output_name": "1.out", "input_name": "1.in", "score": 50},
                                   {"output_name": "2.out", "input_name": "2.in", "score": 50}] if 'OI' else [],
                    template={}
                )
                
                # 为题目分配随机标签 (1-5个)
                num_tags = random.randint(1, 5)
                selected_tags = random.sample(self.tags, min(num_tags, len(self.tags)))
                problem.tags.set(selected_tags)
                
                self.problems.append(problem)
            except Exception as e:
                # 题目可能已存在，尝试获取
                try:
                    problem = Problem.objects.get(_id=problem_id)
                    self.problems.append(problem)
                except Problem.DoesNotExist:
                    continue
        
        self.stdout.write(f'创建了 {len(self.problems)} 个题目')

    def create_contests(self, count):
        """创建测试比赛"""
        from contest.models import Contest
        
        self.contests = []
        
        if count == 0:
            return
            
        # 获取一些题目用于比赛
        contest_problems = random.sample(self.problems, min(len(self.problems), max(5, count*2)))
        
        contest_statuses = [0, 1, 2]  # 未开始、进行中、已结束
        
        for i in range(count):
            try:
                owner = random.choice(self.users)
                contest = Contest.objects.create(
                    title=f'测试比赛 {i}',
                    description=f'<p>这是一个测试比赛，包含多道算法题目供参赛者练习。</p>',
                    created_by=owner,
                    start_time='2025-01-01T00:00:00Z',
                    end_time='2025-12-31T23:59:59Z',
                    rule_type=random.choice(['ACM', 'OI']),
                    password=f'test{i}',
                    visible=True,
                    real_time_rank=True,
                    allowed_ip_ranges=[]
                )
                
                # 为比赛添加题目
                for j, problem in enumerate(contest_problems[:random.randint(3, len(contest_problems))]):
                    # 这里简化处理，实际应该通过ContestProblem关联
                    pass
                    
                self.contests.append(contest)
            except Exception as e:
                logger.warning(f'创建比赛时出错: {str(e)}')
                continue
        
        self.stdout.write(f'创建了 {len(self.contests)} 场比赛')

    def create_submissions(self, count):
        """创建测试提交记录"""
        if not self.users or not self.problems:
            self.stdout.write(self.style.ERROR('没有可用的用户或题目来创建提交记录'))
            return
            
        results = [-2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8]  # 各种判题结果
        
        created_count = 0
        self.submission_count = 0
        
        # 创建不同类型的提交模式
        for i in range(count):
            try:
                user = random.choice(self.users)
                problem = random.choice(self.problems)
                
                # 生成随机代码
                code = self.generate_sample_code(problem)
                
                # 根据用户能力调整结果分布
                # 管理员用户有更高的AC率
                is_admin = getattr(user, 'admin_type', '') in ['Admin', 'Super Admin']
                
                if is_admin:
                    result = random.choices(
                        results, 
                        weights=[0.02, 0.03, 0.7, 0.02, 0.03, 0.03, 0.05, 0.05, 0.05, 0.02,0],  
                        k=1
                    )[0]
                else:
                    result = random.choices(
                        results, 
                        weights=[0.05, 0.1, 0.5, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05,0],  # 提高AC(0)的概率
                        k=1
                    )[0]
                
                submission = Submission.objects.create(
                    problem=problem,
                    user_id=user.id,
                    username=user.username,
                    code=code,
                    result=result,
                    info={},
                    language=random.choice(['Python3', 'C++', 'Java', 'Python2']),
                    shared=random.choice([True, False]),
                    statistic_info={
                        "time_cost": random.randint(10, 2000),
                        "memory_cost": random.randint(1000, 100000)
                    },
                    ip=f'192.168.{random.randint(0, 255)}.{random.randint(0, 255)}'
                )
                
                created_count += 1
                self.submission_count = created_count
                
                # 每批记录输出一次进度
                if (i + 1) % max(1, count//10) == 0:
                    self.stdout.write(f'已创建 {i + 1} 条提交记录')
                    
            except Exception as e:
                logger.warning(f'创建提交记录时出错: {str(e)}')
                continue
        
        self.stdout.write(f'总共创建了 {created_count} 条提交记录')

    def generate_sample_code(self, problem):
        """生成示例代码"""
        languages = ['Python3', 'C++', 'Java']
        language = random.choice(languages)
        
        if language == 'Python3':
            return f'''# Solution for problem {problem.title}
def solve():
    # Read input
    try:
        n = int(input())
        arr = list(map(int, input().split()))
        
        # Process data
        result = 0
        for i in range(n):
            result += arr[i]
        
        # Output result
        print(result)
    except:
        pass

if __name__ == "__main__":
    solve()
'''
        elif language == 'C++':
            return f'''// Solution for problem {problem.title}
#include <iostream>
#include <vector>
using namespace std;

int main() {{
    try {{
        int n;
        cin >> n;
        vector<int> arr(n);
        
        for (int i = 0; i < n; i++) {{
            cin >> arr[i];
        }}
        
        long long result = 0;
        for (int i = 0; i < n; i++) {{
            result += arr[i];
        }}
        
        cout << result << endl;
    }} catch (...) {{
        return 1;
    }}
    return 0;
}}'''
        else:  # Java
            return f'''// Solution for problem {problem.title}
import java.util.*;

public class Solution {{
    public static void main(String[] args) {{
        try {{
            Scanner sc = new Scanner(System.in);
            int n = sc.nextInt();
            long[] arr = new long[n];
            
            for (int i = 0; i < n; i++) {{
                arr[i] = sc.nextLong();
            }}
            
            long result = 0;
            for (int i = 0; i < n; i++) {{
                result += arr[i];
            }}
            
            System.out.println(result);
            sc.close();
        }} catch (Exception e) {{
            System.exit(1);
        }}
    }}
}}'''
