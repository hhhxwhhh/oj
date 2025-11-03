from django.core.management.base import BaseCommand
from ai.dl_models.deep_learning import EnhancedQLearningRecommender
from account.models import User
from submission.models import Submission
import logging
import numpy as np

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '训练强化学习推荐模型'

    def add_arguments(self, parser):
        parser.add_argument('--episodes', type=int, default=100,
                           help='每个用户的训练回合数')
        parser.add_argument('--users', type=int, default=50,
                           help='训练的用户数量')
        parser.add_argument('--batch-size', type=int, default=32,
                           help='经验回放批次大小')

    def handle(self, *args, **options):
        episodes = options['episodes']
        users = options['users']
        batch_size = options['batch_size']
        
        self.stdout.write(f'开始训练强化学习推荐模型，用户数: {users}，每用户回合数: {episodes}，批次大小: {batch_size}...')
        
        try:
            # 初始化强化学习推荐器
            recommender = EnhancedQLearningRecommender(state_size=16, action_size=7)
            
            # 获取训练用户
            user_ids = list(Submission.objects.values_list('user_id', flat=True).distinct()[:users])
            
            if not user_ids:
                self.stdout.write(self.style.WARNING('未找到真实用户，创建虚拟用户进行训练'))
                user_ids = list(range(1, users + 1))
            
            self.stdout.write(f'开始训练 {len(user_ids)} 个用户的强化学习模型...')
            
            # 为每个用户进行训练
            avg_rewards = []
            for i, user_id in enumerate(user_ids):
                try:
                    # 检查用户是否存在（如果是真实用户）
                    if User.objects.filter(id=user_id).exists():
                        avg_reward = self.train_user(recommender, user_id, episodes)
                        avg_rewards.append(avg_reward)
                        self.stdout.write(f'进度: {i+1}/{len(user_ids)} 用户 {user_id} 完成，平均奖励: {avg_reward:.4f}')
                    else:
                        # 虚拟用户训练
                        avg_reward = self.train_virtual_user(recommender, user_id, episodes)
                        avg_rewards.append(avg_reward)
                        self.stdout.write(f'进度: {i+1}/{len(user_ids)} 虚拟用户 {user_id} 完成，平均奖励: {avg_reward:.4f}')
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'训练用户 {user_id} 时出错: {str(e)}'))
                    continue
            
            # 计算整体平均奖励
            overall_avg_reward = np.mean(avg_rewards) if avg_rewards else 0
            
            # 保存模型
            recommender.save_model()
            
            self.stdout.write(
                self.style.SUCCESS(f'强化学习模型训练完成，整体平均奖励: {overall_avg_reward:.4f}，模型已保存')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'训练过程中出现错误: {str(e)}')
            )
    
    def calculate_reward(self, user_id, algorithm):
        """
        计算用户使用特定算法的奖励
        """
        try:
            # 获取用户提交历史
            submissions = Submission.objects.filter(user_id=user_id).order_by('-create_time')
            recent_submissions_list = list(submissions[:20])  # 最近20次提交
            
            if not recent_submissions_list:
                # 新用户，给予中等奖励以鼓励探索
                return 0.5
            
            # 计算最近通过率
            recent_accepted = sum(1 for s in recent_submissions_list if s.result == 0)
            recent_acceptance_rate = recent_accepted / len(recent_submissions_list)
            
            # 根据算法类型设定基础奖励
            algorithm_rewards = {
                'online_learning': 1.0,    # 在线学习算法最高奖励
                'deep_learning': 0.9,      # 深度学习算法高奖励
                'ml_enhanced': 0.8,        # 机器学习增强算法中高奖励
                'collaborative': 0.7,      # 协同过滤中等奖励
                'hybrid': 0.75,            # 混合算法中等奖励
                'content': 0.65,           # 内容基础算法中低奖励
                'popularity': 0.5          # 热门推荐最低奖励
            }
            
            base_reward = algorithm_rewards.get(algorithm, 0.5)
            
            # 添加一些噪声以增加探索性
            noise = np.random.normal(0, 0.1)
            final_reward = max(0, min(1, base_reward + noise))  # 限制在[0,1]范围
            
            return final_reward
            
        except Exception as e:
            logger.error(f"计算用户 {user_id} 奖励时出错: {str(e)}")
            return 0.5
    
    def train_user(self, recommender, user_id, episodes):
        """
        训练真实用户
        """
        rewards = []
        
        for episode in range(episodes):
            # 选择动作
            action = recommender.select_action(user_id, training=True)
            algorithm = recommender.action_space[action]
            
            # 计算奖励
            reward = self.calculate_reward(user_id, algorithm)
            
            # 更新模型
            recommender.update(user_id, algorithm, reward)
            
            rewards.append(reward)
        
        return np.mean(rewards) if rewards else 0
    
    def train_virtual_user(self, recommender, user_id, episodes):
        """
        训练虚拟用户（用于测试或数据不足时）
        """
        # 为虚拟用户设置一些随机特征
        rewards = []
        
        for episode in range(episodes):
            # 使用固定的状态表示虚拟用户
            # 在实际实现中，这可能基于用户ID生成一些固定的特征
            
            # 选择动作
            # 为了训练，我们随机选择一个用户ID进行状态获取
            dummy_user_id = (user_id % 10) + 1
            action = recommender.select_action(dummy_user_id, training=True)
            algorithm = recommender.action_space[action]
            
            # 计算奖励
            reward = 0.5 + np.random.normal(0, 0.2)  # 虚拟奖励
            reward = max(0, min(1, reward))  # 限制在[0,1]范围
            
            # 更新模型
            recommender.update(dummy_user_id, algorithm, reward)
            
            rewards.append(reward)
        
        return np.mean(rewards) if rewards else 0