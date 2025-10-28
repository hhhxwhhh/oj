# 在Django shell中执行
from account.models import User, UserProfile
from problem.models import Problem
from submission.models import Submission
from account.models import AdminType
import random

def create_test_submissions():
    # 获取测试用户（排除管理员）- 使用admin_type字段
    test_users = User.objects.filter(admin_type=AdminType.REGULAR_USER, is_disabled=False)[:50]  # 取前50个普通用户
    problems = Problem.objects.filter(visible=True)[:20]  # 取前20个可见题目
    
    print(f"为 {len(test_users)} 个测试用户创建提交记录...")
    
    for i, user in enumerate(test_users):
        # 为每个用户创建3-10个提交记录
        num_submissions = random.randint(3, 10)
        print(f"为用户 {user.username} 创建 {num_submissions} 个提交记录")
        
        for j in range(num_submissions):
            problem = random.choice(problems)
            # 随机选择结果（0=AC, 1-6=其他状态）
            result = random.choices(
                [0, 1, 2, 3, 4, 5, 6],
                weights=[0.3, 0.1, 0.1, 0.1, 0.1, 0.1, 0.2]  # 30%概率AC
            )[0]
            
            # 创建提交记录
            submission = Submission.objects.create(
                user_id=user.id,
                problem=problem,
                contest=None,
                result=result,
                code="print('Hello World')",  # 简单代码
                language="C++",
                statistic_info={"time_cost": random.randint(10, 1000), "memory_cost": random.randint(1000, 100000)}
            )
            
            # 如果是AC状态，更新用户统计
            if result == 0:
                profile = user.userprofile
                profile.accepted_number += 1
                profile.submission_number += 1
                
                # 更新ACM题目状态
                acm_status = profile.acm_problems_status.get("problems", {})
                acm_status[str(problem.id)] = {"status": 0, "_id": problem._id}
                profile.acm_problems_status["problems"] = acm_status
                profile.save()
            else:
                # 非AC状态只更新提交数
                profile = user.userprofile
                profile.submission_number += 1
                profile.save()
    
    print("测试用户提交记录创建完成！")

# 执行函数
create_test_submissions()
