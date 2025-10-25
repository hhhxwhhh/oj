import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from torch.utils.data import Dataset, DataLoader
import logging

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