import random
from django.core.management.base import BaseCommand
from django.db.models import Count
from account.models import User, UserProfile
from problem.models import Problem
from submission.models import Submission, JudgeStatus


class Command(BaseCommand):
    help = '为系统中所有现有用户和题目生成测试提交记录，并更新统计信息'

    def add_arguments(self, parser):
        parser.add_argument('--submissions-per-user', type=int, default=5,
                            help='每个用户每个题目的平均提交次数')
        parser.add_argument('--ac-rate', type=float, default=0.3,
                            help='通过率 (0.0-1.0)')

    def handle(self, *args, **options):
        submissions_per_user = options['submissions_per_user']
        ac_rate = options['ac_rate']

        # 获取所有用户和题目
        users = list(User.objects.all())
        problems = list(Problem.objects.filter(visible=True))

        if not users or not problems:
            self.stdout.write(self.style.ERROR('没有找到用户或可见题目'))
            return

        self.stdout.write(f'找到 {len(users)} 个用户和 {len(problems)} 个可见题目')

        # 确保所有用户都有UserProfile
        users_without_profile = []
        for user in users:
            try:
                profile = user.userprofile
            except UserProfile.DoesNotExist:
                users_without_profile.append(user)
        
        if users_without_profile:
            self.stdout.write(f'发现 {len(users_without_profile)} 个用户没有UserProfile，正在创建...')
            for user in users_without_profile:
                UserProfile.objects.create(user=user)
        
        total_submissions = 0
        # 为每个用户和每个题目生成提交记录
        for user in users:
            user_submissions_count = 0
            for problem in problems:
                # 为每个用户-题目对生成随机数量的提交记录
                num_submissions = max(0, int(random.gauss(submissions_per_user, submissions_per_user/3)))
                
                for i in range(num_submissions):
                    # 根据设定的通过率决定结果
                    if random.random() < ac_rate:
                        result = JudgeStatus.ACCEPTED
                    else:
                        result = random.choice([
                            JudgeStatus.WRONG_ANSWER,
                            JudgeStatus.CPU_TIME_LIMIT_EXCEEDED,
                            JudgeStatus.MEMORY_LIMIT_EXCEEDED,
                            JudgeStatus.RUNTIME_ERROR,
                            JudgeStatus.COMPILE_ERROR
                        ])
                    
                    # 创建提交记录
                    submission = Submission.objects.create(
                        problem=problem,
                        user_id=user.id,
                        username=user.username,
                        code=self.generate_sample_code(problem),
                        result=result,
                        info={},
                        language=random.choice(['C++', 'Java', 'Python3']),
                        statistic_info={
                            "time_cost": random.randint(100, 3000),
                            "memory_cost": random.randint(5000, 128000)
                        },
                        ip='127.0.0.1'
                    )
                    
                    # 更新题目统计信息
                    problem.submission_number += 1
                    if result == JudgeStatus.ACCEPTED:
                        problem.accepted_number += 1
                    
                    # 更新题目的statistic_info
                    result_str = str(result)
                    if result_str in problem.statistic_info:
                        problem.statistic_info[result_str] += 1
                    else:
                        problem.statistic_info[result_str] = 1
                    
                    problem.save(update_fields=["submission_number", "accepted_number", "statistic_info"])
                    
                    user_submissions_count += 1
                    total_submissions += 1
            
            # 更新用户统计信息
            user_profile = user.userprofile
            user_submissions = Submission.objects.filter(user_id=user.id)
            user_profile.submission_number = user_submissions.count()
            user_profile.accepted_number = user_submissions.filter(result=JudgeStatus.ACCEPTED).count()
            user_profile.save(update_fields=["submission_number", "accepted_number"])
            
            self.stdout.write(f'为用户 {user.username} 创建了 {user_submissions_count} 条提交记录')

        self.stdout.write(
            self.style.SUCCESS(
                f'成功创建 {total_submissions} 条提交记录，涉及 {len(users)} 个用户和 {len(problems)} 个题目'
            )
        )

    def generate_sample_code(self, problem):
        """生成示例代码"""
        language = random.choice(['C++', 'Java', 'Python3'])
        
        if language == 'Python3':
            return f'''# Solution for problem {problem.title}
def solve():
    # Read input
    n = int(input())
    arr = list(map(int, input().split()))
    
    # Process data
    result = sum(arr)
    
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
    
    long long result = 0;
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
    }}
}}'''