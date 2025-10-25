import torch
import torch.nn as nn
import torch.nn.functional as F
import logging
logger = logging.getLogger(__name__)

class ProblemRecommendationNet(nn.Module):
    """题目推荐神经网络"""
    def __init__(self, user_dim=20, problem_dim=10, embedding_dim=64):
        super(ProblemRecommendationNet, self).__init__()
        self.user_embedding = nn.Linear(user_dim, embedding_dim)
        self.problem_embedding = nn.Linear(problem_dim, embedding_dim)
        self.fc1 = nn.Linear(embedding_dim * 2, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, 1)
        self.dropout = nn.Dropout(0.2)
        
    def forward(self, user_features, problem_features):
        user_emb = F.relu(self.user_embedding(user_features))
        problem_emb = F.relu(self.problem_embedding(problem_features))
        
        # 合并用户和题目嵌入
        combined = torch.cat([user_emb, problem_emb], dim=1)
        x = F.relu(self.fc1(combined))
        x = self.dropout(x)
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        x = torch.sigmoid(self.fc3(x))  # 输出0-1之间的匹配分数
        return x

class DeepLearningRecommender:
    """深度学习推荐器"""
    
    def __init__(self, model_path=None):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = ProblemRecommendationNet().to(self.device)
        self.criterion = nn.BCELoss()
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        
        if model_path and torch.load(model_path, map_location=self.device):
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            logger.info("Loaded pre-trained recommendation model from %s", model_path)
    
    def train(self, user_features, problem_features, labels, epochs=50, batch_size=32):
        """训练推荐模型"""
        dataset = torch.utils.data.TensorDataset(
            torch.FloatTensor(user_features),
            torch.FloatTensor(problem_features),
            torch.FloatTensor(labels)
        )
        loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        for epoch in range(epochs):
            self.model.train()
            total_loss = 0
            for batch_user, batch_problem, batch_labels in loader:
                batch_user = batch_user.to(self.device)
                batch_problem = batch_problem.to(self.device)
                batch_labels = batch_labels.to(self.device)
                
                self.optimizer.zero_grad()
                outputs = self.model(batch_user, batch_problem)
                loss = self.criterion(outputs.squeeze(), batch_labels)
                loss.backward()
                self.optimizer.step()
                
                total_loss += loss.item()
            
            avg_loss = total_loss / len(loader)
            logger.info(f'Recommendation Model Epoch [{epoch+1}/{epochs}], Loss: {avg_loss:.4f}')
        
        # 保存模型
        torch.save(self.model.state_dict(), 'ai/models/deep_learning/recommendation_model.pth')
    
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
                
            score = self.model(user_tensor, problem_tensor)
            return score.cpu().numpy()