from django.core.management.base import BaseCommand
from ai.service import AIProgrammingAbilityService, AIRecommendationService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '训练机器学习模型'

    def add_arguments(self, parser):
        parser.add_argument('--model', type=str, default='all', 
                           choices=['all', 'ability', 'recommendation'],
                           help='要训练的模型类型')

    def handle(self, *args, **options):
        model_type = options['model']
        
        self.stdout.write(f'开始训练{model_type}模型...')
        
        try:
            if model_type in ['all', 'ability']:
                self.stdout.write('训练能力评估模型...')
                AIProgrammingAbilityService._train_ability_assessment_model()
                self.stdout.write(self.style.SUCCESS('能力评估模型训练完成'))
            
            if model_type in ['all', 'recommendation']:
                self.stdout.write('训练推荐模型...')
                AIRecommendationService.train_recommendation_model()
                self.stdout.write(self.style.SUCCESS('推荐模型训练完成'))
            
            self.stdout.write(
                self.style.SUCCESS('所有模型训练完成')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'训练过程中出现错误: {str(e)}')
            )