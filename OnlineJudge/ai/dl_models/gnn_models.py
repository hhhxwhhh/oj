import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv
import logging

logger = logging.getLogger(__name__)

class ProblemKnowledgeGNN(nn.Module):
    """
    题目-知识点图神经网络
    用于建模题目和知识点之间的复杂关系
    """
    def __init__(self, num_problems, num_knowledge_points, embedding_dim=64):
        super(ProblemKnowledgeGNN, self).__init__()
        self.num_problems = num_problems
        self.num_knowledge_points = num_knowledge_points
        
        self.problem_embedding = nn.Embedding(num_problems, embedding_dim)
        self.knowledge_embedding = nn.Embedding(num_knowledge_points, embedding_dim)
        
        # 使用GCN层处理图结构
        self.conv1 = GCNConv(embedding_dim, embedding_dim)
        self.conv2 = GCNConv(embedding_dim, embedding_dim)
        
        # 注意力机制增强
        self.attention = nn.MultiheadAttention(embedding_dim, num_heads=4, batch_first=True)
        
        self.fc = nn.Linear(embedding_dim * 2, 1)
        self.dropout = nn.Dropout(0.2)
        
    def forward(self, problem_indices, knowledge_indices, edge_index):
        # 检查输入索引是否在有效范围内
        problem_indices = torch.clamp(problem_indices, 0, self.num_problems - 1)
        knowledge_indices = torch.clamp(knowledge_indices, 0, self.num_knowledge_points - 1)
        
        # 获取嵌入
        problem_emb = self.problem_embedding(problem_indices)
        knowledge_emb = self.knowledge_embedding(knowledge_indices)
        
        # 图卷积处理
        all_features = torch.cat([problem_emb, knowledge_emb], dim=0)
        
        # 确保边索引在有效范围内
        if edge_index.numel() > 0:
            max_index = all_features.size(0) - 1
            edge_index = torch.clamp(edge_index, 0, max_index)
        
        all_features = F.relu(self.conv1(all_features, edge_index))
        all_features = self.dropout(all_features)
        all_features = F.relu(self.conv2(all_features, edge_index))
        
        # 分离特征
        problem_features = all_features[:len(problem_indices)]
        knowledge_features = all_features[len(problem_indices):]
        
        # 注意力机制融合
        if knowledge_features.size(0) > 0 and problem_features.size(0) > 0:
            # 确保序列长度一致
            min_len = min(problem_features.size(0), knowledge_features.size(0))
            problem_seq = problem_features[:min_len].unsqueeze(0)
            knowledge_seq = knowledge_features[:min_len].unsqueeze(0)
            
            combined_features, _ = self.attention(
                problem_seq, 
                knowledge_seq, 
                knowledge_seq
            )
            combined_features = combined_features.squeeze(0)
        else:
            # 如果没有知识点特征或问题特征，使用问题特征
            combined_features = problem_features
        
        # 合并特征
        if knowledge_features.size(0) > 0 and combined_features.size(0) > 0:
            knowledge_mean = combined_features.mean(dim=0, keepdim=True).expand_as(problem_features)
        else:
            # 如果没有知识点特征，使用零向量
            knowledge_mean = torch.zeros_like(problem_features)
            
        merged = torch.cat([problem_features, knowledge_mean], dim=1)
        output = torch.sigmoid(self.fc(self.dropout(merged))).squeeze()
        return output

class GNNBasedRecommender:
    """
    基于GNN的推荐器
    """
    def __init__(self, num_problems=None, num_knowledge_points=None, embedding_dim=64, model_path=None):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # 使用传入的实际参数
        self.num_problems = num_problems
        self.num_knowledge_points = num_knowledge_points
        self.embedding_dim = embedding_dim
        
        self.model = ProblemKnowledgeGNN(
            self.num_problems, 
            self.num_knowledge_points,
            self.embedding_dim
        ).to(self.device)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        self.criterion = nn.BCELoss()
        
        if model_path and torch.load(model_path, map_location=self.device):
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            logger.info("Loaded pre-trained GNN recommendation model from %s", model_path)
    
    def train_with_batches(self, dataloader, edge_index, epochs=50):
        """
        使用批处理训练GNN推荐模型
        """
        self.model.train()
        edge_index = edge_index.to(self.device)
        
        for epoch in range(epochs):
            total_loss = 0
            batch_count = 0
            
            for batch_idx, (problem_batch, knowledge_batch, labels_batch) in enumerate(dataloader):
                self.optimizer.zero_grad()
                
                problem_batch = problem_batch.to(self.device)
                knowledge_batch = knowledge_batch.to(self.device)
                labels_batch = labels_batch.to(self.device)
                
                outputs = self.model(problem_batch, knowledge_batch, edge_index)
                
                # 确保输出和标签形状匹配
                if outputs.dim() == 0:
                    outputs = outputs.unsqueeze(0)
                if labels_batch.dim() == 0:
                    labels_batch = labels_batch.unsqueeze(0)
                
                # 只计算非空批次的损失
                if outputs.numel() > 0 and labels_batch.numel() > 0:
                    loss = self.criterion(outputs, labels_batch)
                    loss.backward()
                    self.optimizer.step()
                    
                    total_loss += loss.item()
                    batch_count += 1
            
            if batch_count > 0:
                avg_loss = total_loss / batch_count
                if epoch % 10 == 0:
                    logger.info(f'GNN Training Epoch [{epoch}/{epochs}], Average Loss: {avg_loss:.4f}')
            else:
                logger.warning(f'GNN Training Epoch [{epoch}/{epochs}] completed with no valid batches')
        
        # 保存模型
        torch.save(self.model.state_dict(), 'ai/dl_models/gnn/gnn_recommendation_model.pth')
    
    def train(self, problem_indices, knowledge_indices, edge_index, labels, epochs=50):
        """
        原始训练方法（兼容性保留）
        """
        # 转换为张量
        problem_tensor = torch.LongTensor(problem_indices)
        knowledge_tensor = torch.LongTensor(knowledge_indices)
        labels_tensor = torch.FloatTensor(labels)
        
        # 创建数据集和数据加载器
        from torch.utils.data import TensorDataset, DataLoader
        dataset = TensorDataset(problem_tensor, knowledge_tensor, labels_tensor)
        dataloader = DataLoader(dataset, batch_size=32, shuffle=True)
        
        # 使用批处理训练
        self.train_with_batches(dataloader, edge_index, epochs)
    
    def predict_score(self, problem_id, user_knowledge_states):
        """
        预测用户对题目的兴趣分数
        """
        self.model.eval()
        with torch.no_grad():
            # 确保问题ID在有效范围内
            problem_id = max(0, min(problem_id, self.num_problems - 1))
            problem_indices = torch.LongTensor([problem_id]).to(self.device)
            
            # 确保知识点ID在有效范围内
            valid_knowledge_ids = [max(0, min(state.knowledge_point_id, self.num_knowledge_points - 1)) 
                                 for state in user_knowledge_states]
            
            if not valid_knowledge_ids:
                # 如果没有有效的知识点，返回默认低分
                return 0.1
                
            knowledge_indices = torch.LongTensor(valid_knowledge_ids).to(self.device)
            
            # 构建边索引（简化处理）
            if len(knowledge_indices) > 0:
                edge_index = torch.LongTensor([
                    [i for i in range(len(knowledge_indices))],
                    [len(knowledge_indices)] * len(knowledge_indices)
                ]).to(self.device)
            else:
                edge_index = torch.empty((2, 0), dtype=torch.long).to(self.device)
            
            score = self.model(problem_indices, knowledge_indices, edge_index)
            return score.cpu().numpy()[0] if len(score.shape) > 0 else score.cpu().numpy()
