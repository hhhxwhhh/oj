from django.core.management.base import BaseCommand
from ai.models import KnowledgePoint

class Command(BaseCommand):
    help = '检查知识点向量数据'

    def handle(self, *args, **options):
        self.stdout.write('检查知识点向量数据...')
        
        # 检查知识点总数
        total_kp = KnowledgePoint.objects.count()
        self.stdout.write(f'知识点总数: {total_kp}')
        
        # 检查有embedding数据的知识点
        kps_with_embedding = KnowledgePoint.objects.exclude(embedding='').count()
        self.stdout.write(f'有向量表示的知识点数: {kps_with_embedding}')
        
        # 显示前几个知识点的详细信息
        self.stdout.write('\n前5个知识点详情:')
        for i, kp in enumerate(KnowledgePoint.objects.all()[:5]):
            has_embedding = bool(kp.embedding)
            embedding_length = len(kp.embedding.split(',')) if has_embedding and kp.embedding else 0
            self.stdout.write(f'  {i+1}. {kp.name} (ID: {kp.id})')
            self.stdout.write(f'     向量表示: {"有" if has_embedding else "无"}')
            if has_embedding:
                self.stdout.write(f'     向量维度: {embedding_length}')
            self.stdout.write('')