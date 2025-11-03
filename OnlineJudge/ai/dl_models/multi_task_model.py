import torch
import torch.nn as nn
import torch.nn.functional as F
import logging

logger = logging.getLogger(__name__)

class MultiTaskLearningNetwork(nn.Module):
    """
    多任务学习网络
    同时进行能力评估和题目推荐
    """
    def __init__(self, user_feature_dim=20, problem_feature_dim=10, shared_dim=64):
        super(MultiTaskLearningNetwork, self).__init__()
        
        # 共享特征提取层
        self.shared_user_encoder = nn.Sequential(
            nn.Linear(user_feature_dim, shared_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(shared_dim, shared_dim // 2),
            nn.ReLU()
        )
        
        self.shared_problem_encoder = nn.Sequential(
            nn.Linear(problem_feature_dim, shared_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(shared_dim, shared_dim // 2),
            nn.ReLU()
        )
        
        # 能力评估分支
        self.ability_branch = nn.Sequential(
            nn.Linear(shared_dim // 2, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 5)  # 5个能力维度
        )
        
        # 题目推荐分支
        self.recommendation_branch = nn.Sequential(
            nn.Linear(shared_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
        
    def forward(self, user_features, problem_features=None):
        user_encoded = self.shared_user_encoder(user_features)
        
        if problem_features is not None:
            # 同时进行能力评估和题目推荐
            problem_encoded = self.shared_problem_encoder(problem_features)
            
            # 能力评估
            ability_scores = self.ability_branch(user_encoded)
            
            # 题目推荐
            combined_features = torch.cat([user_encoded, problem_encoded], dim=1)
            recommendation_score = self.recommendation_branch(combined_features)
            
            return ability_scores, recommendation_score
        else:
            # 只进行能力评估
            ability_scores = self.ability_branch(user_encoded)
            return ability_scores

class MultiTaskRecommender:
    """
    多任务学习推荐器
    """
    def __init__(self, model_path=None):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = MultiTaskLearningNetwork().to(self.device)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        
        # 多任务损失函数
        self.ability_criterion = nn.MSELoss()
        self.recommendation_criterion = nn.BCELoss()
        
        if model_path and torch.load(model_path, map_location=self.device):
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            logger.info("Loaded pre-trained multi-task model from %s", model_path)
    
    def train(self, user_features, problem_features, ability_labels, recommendation_labels, epochs=100):
        """
        训练多任务模型
        """
        self.model.train()
        dataset = torch.utils.data.TensorDataset(
            torch.FloatTensor(user_features),
            torch.FloatTensor(problem_features),
            torch.FloatTensor(ability_labels),
            torch.FloatTensor(recommendation_labels)
        )
        loader = torch.utils.data.DataLoader(dataset, batch_size=32, shuffle=True)
        
        for epoch in range(epochs):
            total_loss = 0
            ability_loss_total = 0
            recommendation_loss_total = 0
            
            for user_batch, problem_batch, ability_batch, recommendation_batch in loader:
                user_batch = user_batch.to(self.device)
                problem_batch = problem_batch.to(self.device)
                ability_batch = ability_batch.to(self.device)
                recommendation_batch = recommendation_batch.to(self.device)
                
                self.optimizer.zero_grad()
                
                ability_pred, recommendation_pred = self.model(user_batch, problem_batch)
                
                ability_loss = self.ability_criterion(ability_pred, ability_batch)
                recommendation_loss = self.recommendation_criterion(recommendation_pred.squeeze(), recommendation_batch)
                
                # 多任务损失加权
                total_loss_val = ability_loss * 0.6 + recommendation_loss * 0.4
                
                total_loss_val.backward()
                self.optimizer.step()
                
                total_loss += total_loss_val.item()
                ability_loss_total += ability_loss.item()
                recommendation_loss_total += recommendation_loss.item()
            
            if epoch % 20 == 0:
                logger.info(f'Multi-task Training Epoch [{epoch}/{epochs}]')
                logger.info(f'  Total Loss: {total_loss/len(loader):.4f}')
                logger.info(f'  Ability Loss: {ability_loss_total/len(loader):.4f}')
                logger.info(f'  Recommendation Loss: {recommendation_loss_total/len(loader):.4f}')
        
        # 保存模型
        torch.save(self.model.state_dict(), 'ai/dl_models/multi_task/multi_task_model.pth')
    
    def predict_ability(self, user_features):
        """
        预测用户能力
        """
        self.model.eval()
        with torch.no_grad():
            user_tensor = torch.FloatTensor(user_features).to(self.device)
            if len(user_tensor.shape) == 1:
                user_tensor = user_tensor.unsqueeze(0)
            
            ability_scores = self.model(user_tensor)
            return ability_scores.cpu().numpy()
    
    def predict_recommendation_score(self, user_features, problem_features):
        """
        预测推荐分数
        """
        self.model.eval()
        with torch.no_grad():
            user_tensor = torch.FloatTensor(user_features).to(self.device)
            problem_tensor = torch.FloatTensor(problem_features).to(self.device)
            
            if len(user_tensor.shape) == 1:
                user_tensor = user_tensor.unsqueeze(0)
            if len(problem_tensor.shape) == 1:
                problem_tensor = problem_tensor.unsqueeze(0)
            
            _, recommendation_score = self.model(user_tensor, problem_tensor)
            return recommendation_score.cpu().numpy()[0]