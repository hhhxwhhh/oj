from django.core.management.base import BaseCommand
from ai.models import (
    KnowledgePoint, 
    AIUserKnowledgeState, 
    Problem, 
    AIUserLearningPath,
    AIProgrammingAbility,
    AIUserLearningPathNode,
    AIModel,
    AIConversation,
    AIMessage
)
from account.models import User

class Command(BaseCommand):
    help = '检查所有AI模型对象的数量'

    def handle(self, *args, **options):
        self.stdout.write('=== AI模型对象数量统计 ===\n')
        
        # 统计用户数量
        user_count = User.objects.count()
        self.stdout.write(f'用户总数: {user_count}')
        
        # 统计问题数量
        problem_count = Problem.objects.count()
        self.stdout.write(f'问题总数: {problem_count}')
        
        # 统计知识点数量
        knowledge_point_count = KnowledgePoint.objects.count()
        self.stdout.write(f'知识点总数: {knowledge_point_count}')
        
        # 统计用户知识点状态数量
        user_knowledge_state_count = AIUserKnowledgeState.objects.count()
        self.stdout.write(f'用户知识点状态记录数: {user_knowledge_state_count}')
        
        # 统计学习路径数量
        learning_path_count = AIUserLearningPath.objects.count()
        self.stdout.write(f'用户学习路径数: {learning_path_count}')
        
        # 统计学习路径节点数量
        learning_path_node_count = AIUserLearningPathNode.objects.count()
        self.stdout.write(f'学习路径节点数: {learning_path_node_count}')
        
        # 统计编程能力评估数量
        programming_ability_count = AIProgrammingAbility.objects.count()
        self.stdout.write(f'编程能力评估记录数: {programming_ability_count}')
        
        # 统计AI模型数量
        ai_model_count = AIModel.objects.count()
        self.stdout.write(f'AI模型配置数: {ai_model_count}')
        
        # 统计对话和消息数量
        conversation_count = AIConversation.objects.count()
        message_count = AIMessage.objects.count()
        self.stdout.write(f'AI对话数: {conversation_count}')
        self.stdout.write(f'AI消息数: {message_count}')
        
        # 显示详细统计信息
        self.stdout.write('\n=== 详细统计信息 ===')
        
        # 知识点相关统计
        self.stdout.write('\n知识点统计:')
        kps_with_embedding = KnowledgePoint.objects.exclude(embedding='').count()
        self.stdout.write(f'  有向量表示的知识点: {kps_with_embedding}/{knowledge_point_count} ({kps_with_embedding/knowledge_point_count*100:.1f}%)' if knowledge_point_count > 0 else '  有向量表示的知识点: 0/0 (0.0%)')
        
        kps_with_problems = KnowledgePoint.objects.filter(related_problems__isnull=False).distinct().count()
        self.stdout.write(f'  有关联题目的知识点: {kps_with_problems}/{knowledge_point_count} ({kps_with_problems/knowledge_point_count*100:.1f}%)' if knowledge_point_count > 0 else '  有关联题目的知识点: 0/0 (0.0%)')
        
        kps_with_parents = KnowledgePoint.objects.filter(parent_points__isnull=False).distinct().count()
        self.stdout.write(f'  有前置知识点的知识点: {kps_with_parents}/{knowledge_point_count} ({kps_with_parents/knowledge_point_count*100:.1f}%)' if knowledge_point_count > 0 else '  有前置知识点的知识点: 0/0 (0.0%)')
        
        # 用户知识点状态统计
        self.stdout.write('\n用户知识点状态统计:')
        users_with_knowledge_state = AIUserKnowledgeState.objects.values('user').distinct().count()
        self.stdout.write(f'  有知识点状态的用户数: {users_with_knowledge_state}/{user_count} ({users_with_knowledge_state/user_count*100:.1f}%)' if user_count > 0 else '  有知识点状态的用户数: 0/0 (0.0%)')
        
        avg_knowledge_per_user = user_knowledge_state_count / users_with_knowledge_state if users_with_knowledge_state > 0 else 0
        self.stdout.write(f'  平均每个用户的知识点数: {avg_knowledge_per_user:.1f}')
        
        # 学习路径统计
        self.stdout.write('\n学习路径统计:')
        users_with_learning_path = AIUserLearningPath.objects.values('user').distinct().count()
        self.stdout.write(f'  有学习路径的用户数: {users_with_learning_path}/{user_count} ({users_with_learning_path/user_count*100:.1f}%)' if user_count > 0 else '  有学习路径的用户数: 0/0 (0.0%)')
        
        avg_nodes_per_path = learning_path_node_count / learning_path_count if learning_path_count > 0 else 0
        self.stdout.write(f'  平均每个学习路径的节点数: {avg_nodes_per_path:.1f}')
        
        # 能力评估统计
        self.stdout.write('\n编程能力评估统计:')
        users_with_ability_assessment = AIProgrammingAbility.objects.values('user').distinct().count()
        self.stdout.write(f'  有能力评估记录的用户数: {users_with_ability_assessment}/{user_count} ({users_with_ability_assessment/user_count*100:.1f}%)' if user_count > 0 else '  有能力评估记录的用户数: 0/0 (0.0%)')
        
        self.stdout.write('\n=== 统计完成 ===')
