# python manage.py shell

# 2. 在Django shell中执行以下代码:

from ai.service import KnowledgePointService

# 调用函数将题目标签转换为知识点
result = KnowledgePointService.create_knowledge_points_from_tags_detailed()

# 查看结果
print(f"创建了 {result['created']} 个新知识点")
print(f"更新了 {result['updated']} 个知识点")
print(f"总共处理了 {result['total_tags']} 个标签")