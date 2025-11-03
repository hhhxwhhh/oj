import logging
from django.core.management.base import BaseCommand
from ai.dl_models.autoencoder import UserBehaviorAnalyzer
from account.models import User
from submission.models import Submission
import logging
import numpy as np

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '训练用户行为自编码器模型'

    def add_arguments(self, parser):
        parser.add_argument('--epochs', type=int, default=100,
                           help='训练轮数')
        parser.add_argument('--users', type=int, default=100,
                           help='训练的用户数量')
        parser.add_argument('--batch-size', type=int, default=32,
                           help='批次大小')
        parser.add_argument('--learning-rate', type=float, default=0.001,
                           help='学习率')
        parser.add_argument('--encoding-dim', type=int, default=16,
                           help='编码维度')

    def handle(self, *args, **options):
        epochs = options['epochs']
        users = options['users']
        batch_size = options['batch_size']
        learning_rate = options['learning_rate']
        encoding_dim = options['encoding_dim']
        
        self.stdout.write(f'开始训练用户行为自编码器模型...')
        self.stdout.write(f'参数: 轮数={epochs}, 用户数={users}, 批次大小={batch_size}, 编码维度={encoding_dim}, 学习率={learning_rate}')
        
        try:
            # 获取训练用户
            user_ids = list(Submission.objects.values_list('user_id', flat=True).distinct()[:users])
            
            if not user_ids:
                self.stdout.write(self.style.WARNING('未找到真实用户，创建虚拟用户进行训练'))
                user_ids = list(range(1, users + 1))
            
            self.stdout.write(f'开始训练 {len(user_ids)} 个用户的行为分析模型...')
            
            # 初始化自编码器
            analyzer = UserBehaviorAnalyzer(encoding_dim=encoding_dim, learning_rate=learning_rate)
            
            # 准备训练数据
            self.stdout.write('准备训练数据...')
            training_data = self.prepare_training_data(user_ids)
            
            # 修复 NumPy 数组条件判断问题
            if training_data is None or len(training_data) == 0:
                self.stdout.write(self.style.ERROR('没有可用的训练数据'))
                return
            
            # 训练模型
            analyzer.train(training_data, epochs=epochs, batch_size=batch_size)
            
            self.stdout.write(
                self.style.SUCCESS('用户行为自编码器模型训练完成')
            )
            
        except Exception as e:
            logger.error(f"训练用户行为自编码器模型失败: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f'训练用户行为自编码器模型失败: {str(e)}')
            )

    def prepare_training_data(self, user_ids):
        """
        准备自编码器训练数据
        """
        try:
            behavior_vectors = []
            
            # 为每个用户构建行为向量
            for user_id in user_ids:
                behavior_vector = self.extract_user_behavior_features(user_id)
                behavior_vectors.append(behavior_vector)
            
            return np.array(behavior_vectors)
            
        except Exception as e:
            logger.error(f"准备训练数据失败: {str(e)}")
            return np.array([])  # 返回空的 NumPy 数组而不是空列表

    def extract_user_behavior_features(self, user_id):
        """
        提取用户行为特征向量
        """
        try:
            # 获取用户提交记录
            submissions = Submission.objects.filter(user_id=user_id)
            total_submissions = submissions.count()
            
            if total_submissions == 0:
                # 返回默认特征向量
                return [0.0] * 50
            
            # 计算各种行为特征
            accepted_submissions = submissions.filter(result=0).count()
            acceptance_rate = accepted_submissions / total_submissions if total_submissions > 0 else 0
            
            # 计算平均尝试次数
            problems_submitted = submissions.values('problem_id').distinct().count()
            avg_attempts = total_submissions / problems_submitted if problems_submitted > 0 else 1
            
            # 计算不同难度题目的通过情况
            from problem.models import Problem
            low_difficulty_accepted = submissions.filter(
                result=0, problem__difficulty='Low').count()
            mid_difficulty_accepted = submissions.filter(
                result=0, problem__difficulty='Mid').count()
            high_difficulty_accepted = submissions.filter(
                result=0, problem__difficulty='High').count()
            
            total_low = submissions.filter(problem__difficulty='Low').count()
            total_mid = submissions.filter(problem__difficulty='Mid').count()
            total_high = submissions.filter(problem__difficulty='High').count()
            
            low_pass_rate = low_difficulty_accepted / total_low if total_low > 0 else 0
            mid_pass_rate = mid_difficulty_accepted / total_mid if total_mid > 0 else 0
            high_pass_rate = high_difficulty_accepted / total_high if total_high > 0 else 0
            
            # 构建特征向量
            features = [
                total_submissions / 100.0,  # 归一化总提交数
                acceptance_rate,
                avg_attempts / 10.0,  # 归一化平均尝试次数
                low_pass_rate,
                mid_pass_rate,
                high_pass_rate,
                low_difficulty_accepted / 20.0,  # 归一化低难度通过数
                mid_difficulty_accepted / 20.0,  # 归一化中难度通过数
                high_difficulty_accepted / 20.0,  # 归一化高难度通过数
            ]
            
            # 补充到50维
            while len(features) < 50:
                features.append(0.0)
            
            return features[:50]  # 确保是50维
            
        except Exception as e:
            logger.error(f"提取用户 {user_id} 行为特征失败: {str(e)}")
            return [0.0] * 50
