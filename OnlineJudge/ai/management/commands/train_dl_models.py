from django.core.management.base import BaseCommand
from ai.service import AIRecommendationService
import logging
import os

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '训练深度学习模型'

    def add_arguments(self, parser):
        parser.add_argument('--model', type=str, default='all',
                           choices=['all', 'recommendation'],
                           help='要训练的模型类型')
        parser.add_argument('--epochs', type=int, default=50,
                           help='训练轮数')
        parser.add_argument('--batch-size', type=int, default=32,
                           help='批次大小')

    def handle(self, *args, **options):
        model_type = options['model']
        epochs = options['epochs']
        batch_size = options['batch_size']
        
        self.stdout.write(f'开始训练{model_type}深度学习模型，训练轮数: {epochs}，批次大小: {batch_size}...')
        
        try:
            if model_type in ['all', 'recommendation']:
                self.stdout.write('训练深度学习推荐模型...')
                
                # 检查是否有足够的数据进行训练
                recommender = AIRecommendationService._train_dl_recommendation_model()
                
                if recommender:
                    model_path = 'ai/dl_models/cnn/recommendation_model.pth'
                    if os.path.exists(model_path):
                        self.stdout.write(self.style.SUCCESS(f'深度学习推荐模型训练完成，模型已保存到: {model_path}'))
                    else:
                        self.stdout.write(self.style.WARNING('深度学习推荐模型训练完成，但模型文件未找到'))
                else:
                    self.stdout.write(self.style.WARNING('深度学习推荐模型训练失败，可能是因为训练数据不足（需要至少20条记录）'))
            
            self.stdout.write(
                self.style.SUCCESS('所有深度学习模型训练完成')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'训练过程中出现错误: {str(e)}')
            )