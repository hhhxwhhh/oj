以下是需要手动调用的函数列表
用于为AI推荐系统生成测试数据：
# 生成测试数据（默认：50用户，100题目，1000提交）
python manage.py generate_test_data

# 自定义参数
python manage.py generate_test_data --users 100 --problems 200 --submissions 2000

创建管理员和测试用户：
# 初始化用户（创建管理员账户）
python manage.py inituser
为所有题目自动生成AI标签：
# 为题目生成标签（分批处理）
python manage.py generate_problem_tags --batch-size 10

# 强制重新生成所有标签
python manage.py generate_problem_tags --force

python manage.py shell
from ai.service import KnowledgePointService

# 从现有题目标签创建知识点
KnowledgePointService.create_knowledge_points_from_tags()
print("知识点创建完成")