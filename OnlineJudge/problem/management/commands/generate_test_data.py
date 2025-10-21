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

    def handle(self, *args, **options):
        user_count = options['users']
        problem_count = options['problems']
        submission_count = options['submissions']

        # 创建标签
        self.create_tags()
        
        # 创建用户
        self.create_users(user_count)
        
        # 创建题目
        self.create_problems(problem_count)
        
        # 创建提交记录
        self.create_submissions(submission_count)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'成功创建 {user_count} 个用户, {problem_count} 个题目, {submission_count} 条提交记录'
            )
        )

    def create_tags(self):
        """创建测试标签"""
        tags_data = [
            '数组', '链表', '栈', '队列', '树', '图', '哈希表', '堆', 
            '排序', '搜索', '动态规划', '贪心算法', '回溯', '分治',
            '位运算', '数学', '字符串', '模拟', '递归', '滑动窗口'
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
        
        for i in range(count):
            username = f'testuser_{i}'
            email = f'testuser_{i}@example.com'
            
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
        
        self.stdout.write(f'创建了 {len(self.users)} 个用户')

    def create_problems(self, count):
        """创建测试题目"""
        self.problems = []
        
        difficulties = [0, 1, 2]  # 低、中、高难度
        
        for i in range(count):
            problem_id = 1000 + i  # 避免与现有题目冲突
            
            try:
                problem = Problem.objects.create(
                    _id=problem_id,
                    title=f'测试题目 {i}: 算法练习',
                    description=f'这是第 {i} 个测试题目的详细描述。题目要求解决一个典型的算法问题，涉及数据结构和算法设计。',
                    input_description='输入包含多个测试用例...',
                    output_description='输出应该按照指定格式返回结果...',
                    hint='提示：可以考虑使用特定的数据结构来优化算法复杂度。',
                    difficulty=random.choice(difficulties),
                    source='测试来源',
                    time_limit=1000,
                    memory_limit=256,
                    accepted_number=random.randint(0, 500),
                    submission_number=random.randint(0, 1000),
                    visible=True
                )
                
                # 为题目分配随机标签 (1-4个)
                num_tags = random.randint(1, 4)
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

    def create_submissions(self, count):
        """创建测试提交记录"""
        if not self.users or not self.problems:
            self.stdout.write(self.style.ERROR('没有可用的用户或题目来创建提交记录'))
            return
            
        results = [-2, -1, 0, 1, 2, 3, 4, 5]  # 各种判题结果
        
        created_count = 0
        for i in range(count):
            try:
                user = random.choice(self.users)
                problem = random.choice(self.problems)
                
                # 生成随机代码
                code = self.generate_sample_code(problem)
                
                # 随机结果，提高AC率以便测试推荐系统
                result = random.choices(
                    results, 
                    weights=[0.05, 0.1, 0.5, 0.05, 0.05, 0.05, 0.1, 0.1],  # 提高AC(0)的概率
                    k=1
                )[0]
                
                submission = Submission.objects.create(
                    problem=problem,
                    user_id=user.id,
                    username=user.username,
                    code=code,
                    result=result,
                    info={},
                    language=random.choice(['Python3', 'C++', 'Java']),
                    shared=random.choice([True, False]),
                    statistic_info={
                        "time_cost": random.randint(100, 2000),
                        "memory_cost": random.randint(1000, 100000)
                    },
                    ip='127.0.0.1'
                )
                
                created_count += 1
                
                # 每100条记录输出一次进度
                if (i + 1) % 100 == 0:
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
    n = int(input())
    arr = list(map(int, input().split()))
    
    # Process data
    result = 0
    for i in range(n):
        result += arr[i]
    
    # Output result
    print(result)

if __name__ == "__main__":
    solve()
'''
        elif language == 'C++':
            return f'''// Solution for problem {problem.title}
#include <iostream>
#include <vector>
using namespace std;

int main() {{
    int n;
    cin >> n;
    vector<int> arr(n);
    
    for (int i = 0; i < n; i++) {{
        cin >> arr[i];
    }}
    
    int result = 0;
    for (int i = 0; i < n; i++) {{
        result += arr[i];
    }}
    
    cout << result << endl;
    return 0;
}}'''
        else:  # Java
            return f'''// Solution for problem {problem.title}
import java.util.*;

public class Solution {{
    public static void main(String[] args) {{
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[] arr = new int[n];
        
        for (int i = 0; i < n; i++) {{
            arr[i] = sc.nextInt();
        }}
        
        int result = 0;
        for (int i = 0; i < n; i++) {{
            result += arr[i];
        }}
        
        System.out.println(result);
        sc.close();
    }}
}}'''
