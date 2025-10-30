import logging
from django.core.management.base import BaseCommand
from ai.service import KnowledgePointService

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update knowledge point frequency and importance metrics'

    def handle(self, *args, **options):
        self.stdout.write('Updating knowledge point frequency and importance metrics...')
        try:
            # 更新所有知识点的频率和重要性指标
            result = KnowledgePointService.update_knowledge_point_metrics()
            if result:
                self.stdout.write(
                    self.style.SUCCESS('Successfully updated knowledge point metrics')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('Failed to update knowledge point metrics')
                )
        except Exception as e:
            logger.error(f"Failed to update knowledge point metrics: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f'Failed to update knowledge point metrics: {str(e)}')
            )