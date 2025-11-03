import torch
import torch.nn as nn
import torch.nn.functional as F
import logging

logger = logging.getLogger(__name__)

class UserBehaviorAutoencoder(nn.Module):
    """
    用户行为自编码器
    用于挖掘用户行为模式和检测异常行为
    """
    def __init__(self, input_dim=50, hidden_dim=32, encoding_dim=16):
        super(UserBehaviorAutoencoder, self).__init__()
        # 编码器
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, encoding_dim),
            nn.ReLU()
        )
        
        # 解码器
        self.decoder = nn.Sequential(
            nn.Linear(encoding_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, input_dim),
            nn.Sigmoid()
        )
        
    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded
    
    def get_encoding(self, x):
        """
        获取用户行为编码
        """
        return self.encoder(x)

class UserBehaviorAnalyzer:
    """
    用户行为分析器
    """
    def __init__(self, model_path=None):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = UserBehaviorAutoencoder().to(self.device)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        self.criterion = nn.MSELoss()
        
        if model_path and torch.load(model_path, map_location=self.device):
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            logger.info("Loaded pre-trained autoencoder model from %s", model_path)
    
    def train(self, user_behavior_data, epochs=100):
        """
        训练自编码器
        """
        self.model.train()
        dataset = torch.utils.data.TensorDataset(torch.FloatTensor(user_behavior_data))
        loader = torch.utils.data.DataLoader(dataset, batch_size=32, shuffle=True)
        
        for epoch in range(epochs):
            total_loss = 0
            for batch in loader:
                batch = batch[0].to(self.device)
                
                self.optimizer.zero_grad()
                reconstructed = self.model(batch)
                loss = self.criterion(reconstructed, batch)
                loss.backward()
                self.optimizer.step()
                
                total_loss += loss.item()
            
            avg_loss = total_loss / len(loader)
            if epoch % 20 == 0:
                logger.info(f'Autoencoder Training Epoch [{epoch}/{epochs}], Loss: {avg_loss:.4f}')
        
        # 保存模型
        torch.save(self.model.state_dict(), 'ai/dl_models/autoencoder/user_behavior_model.pth')
    
    def detect_anomalies(self, user_behavior_vector, threshold=0.1):
        """
        检测用户行为异常
        """
        self.model.eval()
        with torch.no_grad():
            user_tensor = torch.FloatTensor(user_behavior_vector).to(self.device)
            if len(user_tensor.shape) == 1:
                user_tensor = user_tensor.unsqueeze(0)
            
            reconstructed = self.model(user_tensor)
            mse = F.mse_loss(reconstructed, user_tensor, reduction='none').mean(dim=1)
            
            return mse.cpu().numpy() > threshold
    
    def get_user_encoding(self, user_behavior_vector):
        """
        获取用户行为编码
        """
        self.model.eval()
        with torch.no_grad():
            user_tensor = torch.FloatTensor(user_behavior_vector).to(self.device)
            if len(user_tensor.shape) == 1:
                user_tensor = user_tensor.unsqueeze(0)
            
            encoding = self.model.get_encoding(user_tensor)
            return encoding.cpu().numpy()