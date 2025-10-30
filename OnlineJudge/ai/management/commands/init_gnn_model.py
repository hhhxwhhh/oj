from django.core.management.base import BaseCommand
from ai.service import KnowledgeGraphService

class Command(BaseCommand):
    help = '初始化图神经网络模型和知识点嵌入数据'

    def handle(self, *args, **options):
        self.stdout.write('开始初始化GNN模型...')
        
        # 训练GNN模型
        model = KnowledgeGraphService.train_gnn_model(epochs=100, lr=0.01, hidden_dim=64)
        
        if model:
            self.stdout.write(
                self.style.SUCCESS('GNN模型训练完成')
            )
        else:
            self.stdout.write(
                self.style.ERROR('GNN模型训练失败')
            )