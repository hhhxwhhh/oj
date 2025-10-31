import logging
from django.core.management.base import BaseCommand
from ai.service import KnowledgePointService, KnowledgeGraphService

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Complete fix for knowledge point similarity issues'

    def add_arguments(self, parser):
        parser.add_argument('--skip-training', action='store_true', help='Skip GNN model training')
        parser.add_argument('--epochs', type=int, default=200, help='Number of training epochs')
        parser.add_argument('--lr', type=float, default=0.001, help='Learning rate')
        parser.add_argument('--hidden_dim', type=int, default=128, help='Hidden layer dimension')
        parser.add_argument('--model_type', type=str, default='gcn', help='Model type: gcn or gat')

    def handle(self, *args, **options):
        self.stdout.write('开始完整修复知识点相似度问题...')
        try:
            # 第一步：更新知识点频率和重要性
            self.stdout.write('第一步：更新知识点频率和重要性...')
            result = KnowledgePointService.update_knowledge_point_metrics()
            if result:
                self.stdout.write(
                    self.style.SUCCESS('成功更新知识点频率和重要性')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('更新知识点频率和重要性失败')
                )
                return
            
            # 第二步：训练GNN模型（可选）
            if not options['skip_training']:
                self.stdout.write('第二步：训练GNN模型...')
                epochs = options['epochs']
                lr = options['lr']
                hidden_dim = options['hidden_dim']
                model_type = options['model_type']
                
                model = KnowledgeGraphService.train_gnn_model(
                    epochs=epochs, 
                    lr=lr, 
                    hidden_dim=hidden_dim, 
                    model_type=model_type
                )
                
                if model:
                    self.stdout.write(
                        self.style.SUCCESS('成功训练GNN模型并生成嵌入向量')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING('训练GNN模型失败')
                    )
            else:
                self.stdout.write('跳过GNN模型训练')
            
            # 第三步：验证修复结果
            self.stdout.write('第三步：验证修复结果...')
            from ai.models import KnowledgePoint
            
            # 检查重要性更新情况
            default_importance = KnowledgePoint.objects.filter(importance=1.0).count()
            zero_importance = KnowledgePoint.objects.filter(importance=0).count()
            self.stdout.write(f'重要性仍为默认值(1.0)的知识点数: {default_importance}')
            self.stdout.write(f'重要性为0的知识点数: {zero_importance}')
            
            # 检查频率更新情况
            zero_frequency = KnowledgePoint.objects.filter(frequency=0).count()
            self.stdout.write(f'频率为0的知识点数: {zero_frequency}')
            
            # 检查嵌入向量情况
            kps_with_embedding = KnowledgePoint.objects.exclude(embedding='').count()
            total_kp = KnowledgePoint.objects.count()
            self.stdout.write(f'有嵌入向量的知识点数: {kps_with_embedding}/{total_kp}')
            
            self.stdout.write(
                self.style.SUCCESS('知识点相似度问题修复完成')
            )
            
        except Exception as e:
            logger.error(f"修复知识点相似度问题失败: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f'修复失败: {str(e)}')
            )