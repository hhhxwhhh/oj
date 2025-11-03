import logging
from django.core.management.base import BaseCommand
from ai.dl_models.gnn_models import GNNBasedRecommender
from account.models import User
from submission.models import Submission
from problem.models import Problem
from ai.models import AIUserKnowledgeState
import logging
import numpy as np
import torch

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '训练增强版GNN推荐模型'

    def add_arguments(self, parser):
        parser.add_argument('--epochs', type=int, default=100,
                           help='训练轮数')
        parser.add_argument('--users', type=int, default=100,
                           help='训练的用户数量')
        parser.add_argument('--batch-size', type=int, default=32,
                           help='批次大小')
        parser.add_argument('--embedding-dim', type=int, default=64,
                           help='嵌入维度')
        parser.add_argument('--learning-rate', type=float, default=0.001,
                           help='学习率')

    def handle(self, *args, **options):
        epochs = options['epochs']
        users = options['users']
        batch_size = options['batch_size']
        embedding_dim = options['embedding_dim']
        learning_rate = options['learning_rate']
        
        self.stdout.write(f'开始训练增强版GNN推荐模型...')
        self.stdout.write(f'参数: 轮数={epochs}, 用户数={users}, 批次大小={batch_size}, 嵌入维度={embedding_dim}, 学习率={learning_rate}')
        
        try:
            # 获取训练用户
            user_ids = list(Submission.objects.values_list('user_id', flat=True).distinct()[:users])
            
            if not user_ids:
                self.stdout.write(self.style.WARNING('未找到真实用户，创建虚拟用户进行训练'))
                user_ids = list(range(1, users + 1))
            
            self.stdout.write(f'开始训练 {len(user_ids)} 个用户的GNN模型...')
            
            # 初始化GNN推荐器
            num_problems = Problem.objects.filter(visible=True).count()
            num_knowledge_points = AIUserKnowledgeState.objects.values_list(
                'knowledge_point_id', flat=True).distinct().count()
            
            # 确保不会出现0值
            num_problems = max(num_problems, 100)
            num_knowledge_points = max(num_knowledge_points, 10)
            
            recommender = GNNBasedRecommender(
                num_problems=num_problems,
                num_knowledge_points=num_knowledge_points,
                embedding_dim=embedding_dim
            )
            
            # 准备训练数据
            self.stdout.write('准备训练数据...')
            training_data = self.prepare_training_data(user_ids, num_problems, num_knowledge_points)
            
            if not training_data:
                self.stdout.write(self.style.ERROR('没有可用的训练数据'))
                return
            
            # 训练模型
            problem_indices, knowledge_indices, edge_index, labels = training_data
            recommender.train(problem_indices, knowledge_indices, edge_index, labels, epochs=epochs)
            
            self.stdout.write(
                self.style.SUCCESS('GNN推荐模型训练完成')
            )
            
        except Exception as e:
            logger.error(f"训练GNN推荐模型失败: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f'训练GNN推荐模型失败: {str(e)}')
            )

    def prepare_training_data(self, user_ids, num_problems, num_knowledge_points):
        """
        准备GNN训练数据
        """
        try:
            problem_indices = []
            knowledge_indices = []
            labels = []
            
            # 构建边索引
            edge_index = [[], []]
            
            # 为每个用户构建训练数据
            for user_id in user_ids:
                # 获取用户已解决的题目
                solved_problems = Submission.objects.filter(
                    user_id=user_id, result=0
                ).values_list('problem_id', flat=True)
                
                # 获取用户知识点状态
                user_knowledge_states = AIUserKnowledgeState.objects.filter(user_id=user_id)
                
                if not user_knowledge_states.exists():
                    continue
                
                # 为每个已解决的题目添加正样本
                for problem_id in solved_problems:
                    # 确保问题ID在有效范围内
                    if problem_id < num_problems:
                        problem_indices.append(problem_id)
                        # 添加用户知识点
                        for state in user_knowledge_states:
                            # 确保知识点ID在有效范围内
                            if state.knowledge_point_id < num_knowledge_points:
                                knowledge_indices.append(state.knowledge_point_id)
                        labels.append(1.0)  # 正样本
                
                # 为每个未解决的题目添加负样本（采样）
                unsolved_problems = Problem.objects.filter(visible=True).exclude(
                    id__in=solved_problems
                )[:len(solved_problems)]  # 保持正负样本平衡
                
                for problem in unsolved_problems:
                    # 确保问题ID在有效范围内
                    if problem.id < num_problems:
                        problem_indices.append(problem.id)
                        # 添加用户知识点
                        for state in user_knowledge_states:
                            # 确保知识点ID在有效范围内
                            if state.knowledge_point_id < num_knowledge_points:
                                knowledge_indices.append(state.knowledge_point_id)
                        labels.append(0.0)  # 负样本
            
            # 构建正确的边索引（知识点与题目之间的连接）
            # 确保索引不会超出范围
            valid_knowledge_count = len(knowledge_indices)
            valid_problem_count = len(problem_indices)
            
            if valid_knowledge_count > 0 and valid_problem_count > 0:
                # 构建二分图结构：知识点索引从0开始，题目索引从知识点数量开始
                for i in range(valid_knowledge_count):
                    edge_index[0].append(i)  # 知识点索引
                    # 将题目索引映射到正确的范围（知识点数量 + 题目索引）
                    edge_index[1].append(valid_knowledge_count + (i % valid_problem_count))  # 题目索引
            
            if not problem_indices:
                return None
                
            edge_index_tensor = torch.LongTensor(edge_index)
            return problem_indices, knowledge_indices, edge_index_tensor, labels
            
        except Exception as e:
            logger.error(f"准备训练数据失败: {str(e)}")
            return None
