import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from collections import deque
import random
import numpy as np
from torch.utils.data import Dataset, DataLoader
import logging
from .recommendation_model import ProblemRecommendationNet
import json
import os
from collections import defaultdict
from ai.models import AIProgrammingAbility
logger = logging.getLogger(__name__)

class UserAbilityDataset(Dataset):
    """用户能力评估数据集"""
    def __init__(self, features, labels=None):
        self.features = torch.FloatTensor(features)
        self.labels = torch.FloatTensor(labels) if labels is not None else None
        
    def __len__(self):
        return len(self.features)
    
    def __getitem__(self, idx):
        if self.labels is not None:
            return self.features[idx], self.labels[idx]
        return self.features[idx]

class UserAbilityNet(nn.Module):
    """用户编程能力评估神经网络"""
    def __init__(self, input_dim=20, hidden_dim=128, output_dim=5):
        super(UserAbilityNet, self).__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, hidden_dim // 2)
        self.fc4 = nn.Linear(hidden_dim // 2, output_dim)
        self.dropout = nn.Dropout(0.3)
        self.batch_norm1 = nn.BatchNorm1d(hidden_dim)
        self.batch_norm2 = nn.BatchNorm1d(hidden_dim)
        self.batch_norm3 = nn.BatchNorm1d(hidden_dim // 2)
        
    def forward(self, x):
        x = F.relu(self.batch_norm1(self.fc1(x)))
        x = self.dropout(x)
        x = F.relu(self.batch_norm2(self.fc2(x)))
        x = self.dropout(x)
        x = F.relu(self.batch_norm3(self.fc3(x)))
        x = self.dropout(x)
        x = self.fc4(x)  
        return x

class DeepLearningAbilityAssessor:
    """深度学习能力评估器"""
    
    def __init__(self, model_path=None):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = UserAbilityNet().to(self.device)
        self.criterion = nn.MSELoss()
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001, weight_decay=1e-5)
        
        if model_path and torch.load(model_path, map_location=self.device):
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            logger.info("Loaded pre-trained model from %s", model_path)
    
    def train(self, X_train, y_train, X_val=None, y_val=None, epochs=100, batch_size=32):
        """训练模型"""
        train_dataset = UserAbilityDataset(X_train, y_train)
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        
        val_loader = None
        if X_val is not None and y_val is not None:
            val_dataset = UserAbilityDataset(X_val, y_val)
            val_loader = DataLoader(val_dataset, batch_size=batch_size)
        
        best_val_loss = float('inf')
        patience_counter = 0
        patience = 10
        
        for epoch in range(epochs):
            # 训练阶段
            self.model.train()
            train_loss = 0.0
            for features, labels in train_loader:
                features, labels = features.to(self.device), labels.to(self.device)
                
                self.optimizer.zero_grad()
                outputs = self.model(features)
                loss = self.criterion(outputs, labels)
                loss.backward()
                self.optimizer.step()
                
                train_loss += loss.item()
            
            avg_train_loss = train_loss / len(train_loader)
            
            # 验证阶段
            if val_loader:
                self.model.eval()
                val_loss = 0.0
                with torch.no_grad():
                    for features, labels in val_loader:
                        features, labels = features.to(self.device), labels.to(self.device)
                        outputs = self.model(features)
                        loss = self.criterion(outputs, labels)
                        val_loss += loss.item()
                
                avg_val_loss = val_loss / len(val_loader)
                logger.info(f'Epoch [{epoch+1}/{epochs}], Train Loss: {avg_train_loss:.4f}, Val Loss: {avg_val_loss:.4f}')
                
                # 早停机制
                if avg_val_loss < best_val_loss:
                    best_val_loss = avg_val_loss
                    patience_counter = 0
                    # 保存最佳模型
                    torch.save(self.model.state_dict(), 'ai/models/deep_learning/best_ability_model.pth')
                else:
                    patience_counter += 1
                    if patience_counter >= patience:
                        logger.info("Early stopping triggered")
                        break
            else:
                logger.info(f'Epoch [{epoch+1}/{epochs}], Train Loss: {avg_train_loss:.4f}')
        
        # 保存最终模型
        torch.save(self.model.state_dict(), 'ai/models/deep_learning/final_ability_model.pth')
    
    def predict(self, features):
        """预测用户能力"""
        self.model.eval()
        with torch.no_grad():
            features_tensor = torch.FloatTensor(features).to(self.device)
            if len(features_tensor.shape) == 1:
                features_tensor = features_tensor.unsqueeze(0)
            
            outputs = self.model(features_tensor)
            # 限制输出范围在0-40之间
            outputs = torch.clamp(outputs, 0, 40)
            return outputs.cpu().numpy()

# 使用Transformer的增强版本
class TransformerAbilityNet(nn.Module):
    """基于Transformer的用户能力评估模型"""
    def __init__(self, input_dim=20, d_model=64, nhead=4, num_layers=3, output_dim=5):
        super(TransformerAbilityNet, self).__init__()
        self.input_projection = nn.Linear(input_dim, d_model)
        self.pos_encoding = nn.Parameter(torch.randn(1, 1, d_model))
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, 
            nhead=nhead, 
            dim_feedforward=d_model*2,
            dropout=0.1,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.output_layer = nn.Linear(d_model, output_dim)
        self.dropout = nn.Dropout(0.1)
        
    def forward(self, x):
        if len(x.shape) == 2:
            x = x.unsqueeze(1)  # 添加序列维度
            
        x = self.input_projection(x)
        x = x + self.pos_encoding[:, :x.size(1), :]
        x = self.dropout(x)
        
        x = self.transformer(x)
        x = x.mean(dim=1)  # 全局平均池化
        x = self.output_layer(x)
        return x
    
class OnlineLearningRecommender:
    """在线学习推荐器 - 基于用户反馈实时更新模型"""
    
    def __init__(self, model_path=None):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = ProblemRecommendationNet().to(self.device)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        self.criterion = nn.BCELoss()
        
        self.replay_buffer = deque(maxlen=10000)
        self.batch_size = 32
        
        # 在线学习参数
        self.learning_rate = 0.001
        self.epsilon = 0.1  
        self.update_frequency = 10 
        
        if model_path and torch.load(model_path, map_location=self.device):
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            logger.info("Loaded pre-trained recommendation model from %s", model_path)
    
    def update_from_feedback(self, user_features, problem_features, reward):
        # 将经验存储到回放缓冲区
        self.replay_buffer.append((user_features, problem_features, reward))
        
        # 当缓冲区足够大时进行训练
        if len(self.replay_buffer) >= self.batch_size:
            self._train_on_batch()
    
    def _train_on_batch(self):
        """从经验回放缓冲区中采样并训练"""
        # 随机采样一批经验
        batch = random.sample(self.replay_buffer, min(self.batch_size, len(self.replay_buffer)))
        
        user_features_batch = torch.FloatTensor([exp[0] for exp in batch]).to(self.device)
        problem_features_batch = torch.FloatTensor([exp[1] for exp in batch]).to(self.device)
        rewards_batch = torch.FloatTensor([exp[2] for exp in batch]).to(self.device)
        
        # 训练模型
        self.model.train()
        self.optimizer.zero_grad()
        
        predictions = self.model(user_features_batch, problem_features_batch).squeeze()
        loss = self.criterion(predictions, rewards_batch)
        
        loss.backward()
        self.optimizer.step()
        
        self.model.eval()
        logger.info(f"Online learning update completed. Loss: {loss.item():.4f}")
    
    def predict_score(self, user_features, problem_features):
        """预测用户对题目的兴趣分数"""
        self.model.eval()
        with torch.no_grad():
            user_tensor = torch.FloatTensor(user_features).to(self.device)
            problem_tensor = torch.FloatTensor(problem_features).to(self.device)
            
            if len(user_tensor.shape) == 1:
                user_tensor = user_tensor.unsqueeze(0)
            if len(problem_tensor.shape) == 1:
                problem_tensor = problem_tensor.unsqueeze(0)
                
            output = self.model(user_tensor, problem_tensor)
            return output.cpu().numpy()
    
    def save_model(self, model_path):
        """保存模型"""
        torch.save(self.model.state_dict(), model_path)
        logger.info(f"Model saved to {model_path}")

class DQN(nn.Module):
    """深度Q网络"""
    def __init__(self, state_size, action_size, hidden_size=128):
        super(DQN, self).__init__()
        self.fc1 = nn.Linear(state_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.fc3 = nn.Linear(hidden_size, hidden_size // 2)
        self.fc4 = nn.Linear(hidden_size // 2, action_size)
        self.dropout = nn.Dropout(0.2)
        
    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        x = F.relu(self.fc3(x))
        x = self.dropout(x)
        x = self.fc4(x)
        return x
    
class EnhancedQLearningRecommender:
    """增强版Q学习推荐器"""
    
    def __init__(self, state_size=16, action_size=7, model_path=None):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.state_size = state_size
        self.action_size = action_size
        
        # 深度Q网络
        self.q_network = DQN(state_size, action_size).to(self.device)
        self.target_network = DQN(state_size, action_size).to(self.device)
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=0.001)
        
        # 经验回放
        self.memory = deque(maxlen=10000)
        self.batch_size = 64
        
        # Q-learning参数
        self.epsilon = 1.0  # 探索率
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.gamma = 0.95  # 折扣因子
        self.learning_rate = 0.001
        self.update_target_freq = 100  # 更新目标网络的频率
        self.step_count = 0
        
        self.action_space = [
            'hybrid', 
            'content', 
            'collaborative', 
            'ml_enhanced', 
            'deep_learning', 
            'online_learning',
            'popularity'
        ]
        
        # 模型保存路径
        self.model_path = 'ai/dl_models/rl/enhanced_dqn.pth'
        self.target_model_path = 'ai/dl_models/rl/target_dqn.pth'
        
        # 加载预训练模型
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
        elif os.path.exists(self.model_path):
            self.load_model(self.model_path)
    
    def get_user_state(self, user_id):
        """
        获取增强版用户状态表示
        状态包括：基础能力、知识点掌握、近期行为、时间特征等
        """
        try:
            from ai.models import AIProgrammingAbility, AIUserKnowledgeState
            from submission.models import Submission
            from problem.models import Problem
            from django.utils import timezone
            from datetime import timedelta
            
            # 1. 用户能力特征 (4维)
            try:
                ability = AIProgrammingAbility.objects.get(user_id=user_id)
                ability_features = [
                    min(1.0, ability.basic_programming_score / 40.0),
                    min(1.0, ability.data_structure_score / 40.0),
                    min(1.0, ability.algorithm_design_score / 40.0),
                    min(1.0, ability.problem_solving_score / 40.0)
                ]
            except AIProgrammingAbility.DoesNotExist:
                ability_features = [0.5, 0.5, 0.5, 0.5]
            
            # 2. 知识点掌握特征 (4维) 
            knowledge_states = AIUserKnowledgeState.objects.filter(user_id=user_id)
            knowledge_features = [0.0] * 4
            knowledge_list = list(knowledge_states[:4])  # 先转换为列表再取前4个
            for i, state in enumerate(knowledge_list):
                knowledge_features[i] = state.proficiency_level
            
            # 3. 近期行为特征 (6维)
            recent_submissions = Submission.objects.filter(
                user_id=user_id
            ).order_by('-create_time')
            
            # 获取最近的提交记录列表
            recent_submissions_list = list(recent_submissions[:10])
            
            # 近期提交数量
            recent_submission_count = len(recent_submissions_list)
            
            # 近期通过率
            recent_accepted = sum(1 for s in recent_submissions_list if s.result == 0)
            recent_acceptance_rate = recent_accepted / recent_submission_count if recent_submission_count > 0 else 0
            
            # 近期挑战题目平均难度
            recent_problems = [s.problem for s in recent_submissions_list if s.problem]
            if recent_problems:
                difficulty_map = {'Low': 1, 'Mid': 2, 'High': 3}
                avg_difficulty = sum(
                    difficulty_map.get(p.difficulty, 2) for p in recent_problems
                ) / len(recent_problems)
                avg_difficulty_normalized = avg_difficulty / 3.0
            else:
                avg_difficulty_normalized = 0.5
            
            # 连续登陆天数
            login_days = set()
            for submission in recent_submissions_list:
                login_days.add(submission.create_time.date())
            consecutive_days = len(login_days)
            
            # 最近一次提交时间间隔（小时）
            if recent_submissions_list:
                last_submission_time = recent_submissions_list[0].create_time
                hours_since_last = (timezone.now() - last_submission_time).total_seconds() / 3600
                # 归一化到0-1范围
                time_since_last_normalized = min(1.0, hours_since_last / 168.0)  # 168小时=1周
            else:
                time_since_last_normalized = 1.0
            
            behavior_features = [
                min(1.0, recent_submission_count / 10.0),  # 最近提交数量
                recent_acceptance_rate,  # 近期通过率
                avg_difficulty_normalized,  # 平均难度
                min(1.0, consecutive_days / 7.0),  # 连续登陆天数
                time_since_last_normalized,  # 距离上次提交时间
                min(1.0, len([s for s in recent_submissions_list if s.result == 0]) / 5.0)  # 最近通过题目数
            ]
            
            # 4. 时间特征 (2维)
            current_hour = timezone.now().hour
            hour_feature = current_hour / 24.0  # 当前小时
            
            current_weekday = timezone.now().weekday()
            weekday_feature = current_weekday / 6.0  # 当前星期
            
            time_features = [hour_feature, weekday_feature]
            
            # 组合所有特征
            state = ability_features + knowledge_features + behavior_features + time_features
            return np.array(state, dtype=np.float32)
            
        except Exception as e:
            logger.error(f"Error getting user state for user {user_id}: {str(e)}")
            # 返回默认状态
            return np.array([0.5] * self.state_size, dtype=np.float32)
    
    def select_action(self, user_id, training=True):
        """
        选择动作（推荐算法）
        """
        state = self.get_user_state(user_id)
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        
        # ε-贪婪策略
        if training and random.random() < self.epsilon:
            # 随机探索
            return random.randrange(self.action_size)
        else:
            # 利用当前策略
            self.q_network.eval()
            with torch.no_grad():
                q_values = self.q_network(state_tensor)
            self.q_network.train()
            return q_values.max(1)[1].item()
    
    def select_algorithm(self, user_id):
        """
        选择推荐算法（对外接口）
        """
        action = self.select_action(user_id, training=False)
        return self.action_space[action]
    
    def remember(self, state, action, reward, next_state, done):
        """
        存储经验到回放缓冲区
        """
        self.memory.append((state, action, reward, next_state, done))
    
    def replay(self):
        """
        从经验回放中学习
        """
        if len(self.memory) < self.batch_size:
            return
        
        # 采样一批经验
        batch = random.sample(self.memory, self.batch_size)
        states = torch.FloatTensor([e[0] for e in batch]).to(self.device)
        actions = torch.LongTensor([e[1] for e in batch]).to(self.device)
        rewards = torch.FloatTensor([e[2] for e in batch]).to(self.device)
        next_states = torch.FloatTensor([e[3] for e in batch]).to(self.device)
        dones = torch.BoolTensor([e[4] for e in batch]).to(self.device)
        
        # 当前Q值
        current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1))
        
        # 下一状态的Q值
        with torch.no_grad():
            next_q_values = self.target_network(next_states).max(1)[0]
            target_q_values = rewards + (self.gamma * next_q_values * ~dones)
        
        # 计算损失
        loss = F.mse_loss(current_q_values.squeeze(), target_q_values)
        
        # 优化
        self.optimizer.zero_grad()
        loss.backward()
        # 添加梯度裁剪以防止梯度爆炸
        torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), max_norm=1.0)
        self.optimizer.step()
        
        # 降低探索率
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
    
    def update_target_network(self):
        """
        更新目标网络
        """
        self.target_network.load_state_dict(self.q_network.state_dict())
    
    def update(self, user_id, algorithm, reward):
        """
        更新Q值（对外接口）
        """
        # 获取动作索引
        try:
            action = self.action_space.index(algorithm)
        except ValueError:
            action = 0  # 默认动作
        
        # 获取当前状态和下一状态
        state = self.get_user_state(user_id)
        # 模拟下一状态（简化处理）
        next_state = state.copy()
        
        # 存储经验
        self.remember(state, action, reward, next_state, done=False)
        
        # 学习
        self.replay()
        
        # 更新目标网络
        self.step_count += 1
        if self.step_count % self.update_target_freq == 0:
            self.update_target_network()
        
        # 保存模型
        if self.step_count % 1000 == 0:
            self.save_model()
    
    def save_model(self):
        """
        保存模型
        """
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            torch.save(self.q_network.state_dict(), self.model_path)
            torch.save(self.target_network.state_dict(), self.target_model_path)
            logger.info("Enhanced Q-learning model saved")
        except Exception as e:
            logger.error(f"Failed to save enhanced Q-learning model: {str(e)}")
    
    def load_model(self, model_path):
        """
        加载模型
        """
        try:
            self.q_network.load_state_dict(torch.load(model_path, map_location=self.device))
            self.target_network.load_state_dict(torch.load(self.target_model_path, map_location=self.device))
            logger.info("Enhanced Q-learning model loaded")
        except Exception as e:
            logger.error(f"Failed to load enhanced Q-learning model: {str(e)}")

