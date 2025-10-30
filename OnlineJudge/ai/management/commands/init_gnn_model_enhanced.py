from django.core.management.base import BaseCommand
from ai.service import KnowledgeGraphService
from ai.models import KnowledgePoint

class Command(BaseCommand):
    help = '初始化图神经网络模型和知识点嵌入数据（增强版）'

    def add_arguments(self, parser):
        parser.add_argument('--epochs', type=int, default=100, help='训练轮数')
        parser.add_argument('--lr', type=float, default=0.01, help='学习率')
        parser.add_argument('--hidden_dim', type=int, default=64, help='隐藏层维度')

    def handle(self, *args, **options):
        epochs = options['epochs']
        lr = options['lr']
        hidden_dim = options['hidden_dim']
        
        self.stdout.write('开始初始化GNN模型（增强版）...')
        
        # 检查数据
        total_kp = KnowledgePoint.objects.count()
        self.stdout.write(f'知识点总数: {total_kp}')
        
        if total_kp == 0:
            self.stdout.write(self.style.ERROR('没有找到知识点数据，请先创建知识点'))
            return
            
        kps_with_parents = KnowledgePoint.objects.filter(parent_points__isnull=False).distinct().count()
        self.stdout.write(f'有前置知识点的知识点数: {kps_with_parents}')
        
        if kps_with_parents == 0:
            self.stdout.write(self.style.WARNING('没有知识点依赖关系，将训练无依赖关系的模型'))
        
        # 构建知识图谱结构
        self.stdout.write('构建知识图谱结构...')
        data, kp_list, kp_id_to_index = KnowledgeGraphService.build_knowledge_graph()
        
        self.stdout.write(f'图结构构建完成:')
        self.stdout.write(f'  节点数: {data.x.size(0)}')
        self.stdout.write(f'  边数: {data.edge_index.size(1)}')
        self.stdout.write(f'  节点特征维度: {data.x.size(1)}')
        
        if data.x.size(0) == 0:
            self.stdout.write(self.style.ERROR('没有节点数据，无法训练模型'))
            return
            
        # 训练GNN模型
        self.stdout.write(f'开始训练GNN模型 (epochs={epochs}, lr={lr}, hidden_dim={hidden_dim})...')
        model = KnowledgeGraphService.train_gnn_model(epochs=epochs, lr=lr, hidden_dim=hidden_dim)
        
        if model:
            # 检查结果
            kps_with_embedding = KnowledgePoint.objects.exclude(embedding='').count()
            self.stdout.write(f'生成向量表示的知识点数: {kps_with_embedding}')
            
            self.stdout.write(self.style.SUCCESS('GNN模型训练完成'))
        else:
            self.stdout.write(self.style.ERROR('GNN模型训练失败'))