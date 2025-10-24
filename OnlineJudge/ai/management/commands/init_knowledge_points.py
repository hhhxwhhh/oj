import logging
from django.core.management.base import BaseCommand
from ai.service import KnowledgePointService

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Initialize knowledge points from problem tags'

    def handle(self, *args, **options):
        self.stdout.write('Initializing knowledge points from problem tags...')
        try:
            # 创建知识点
            result = KnowledgePointService.create_knowledge_points_from_tags_detailed()
            self.stdout.write(f'Created/updated {result["total_tags"]} knowledge points')
            self.stdout.write(f'Created: {result["created"]}, Updated: {result["updated"]}')
            
            # 建立依赖关系
            deps_result = KnowledgePointService.build_knowledge_point_dependencies()
            self.stdout.write(f'Built dependencies for {deps_result["updated_knowledge_points"]} knowledge points')
            
            # 关联题目
            assoc_result = KnowledgePointService.associate_problems_with_knowledge_points()
            self.stdout.write(f'Associated {assoc_result["associated_problems"]} problems with knowledge points')
            
            self.stdout.write(
                self.style.SUCCESS('Successfully initialized knowledge points')
            )
        except Exception as e:
            logger.error(f"Failed to initialize knowledge points: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f'Failed to initialize knowledge points: {str(e)}')
            )