import logging
from django.core.management.base import BaseCommand
from ai.models import KnowledgePoint
from ai.service import KnowledgeGraphService
import numpy as np

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Diagnose and fix knowledge point similarity issues'

    def handle(self, *args, **options):
        self.stdout.write('诊断知识点相似度问题...')
        try:
            # 检查知识点总数
            total_kp = KnowledgePoint.objects.count()
            self.stdout.write(f'知识点总数: {total_kp}')
            
            # 检查有embedding数据的知识点
            kps_with_embedding = KnowledgePoint.objects.exclude(embedding='').count()
            self.stdout.write(f'有向量表示的知识点数: {kps_with_embedding}')
            
            # 检查importance和frequency字段
            self.stdout.write('\n检查importance和frequency字段:')
            zero_importance = KnowledgePoint.objects.filter(importance=0).count()
            default_importance = KnowledgePoint.objects.filter(importance=1.0).count()
            zero_frequency = KnowledgePoint.objects.filter(frequency=0).count()
            
            self.stdout.write(f'  importance为0的知识点数: {zero_importance}')
            self.stdout.write(f'  importance为默认值(1.0)的知识点数: {default_importance}')
            self.stdout.write(f'  frequency为0的知识点数: {zero_frequency}')
            
            # 检查几个具体知识点的相似度计算
            self.stdout.write('\n检查具体知识点相似度计算:')
            kps = KnowledgePoint.objects.all()[:3]
            for i, kp1 in enumerate(kps):
                for j, kp2 in enumerate(kps):
                    if i < j:
                        similarity = KnowledgeGraphService.get_knowledge_similarity(kp1.id, kp2.id)
                        self.stdout.write(f'  {kp1.name} 与 {kp2.name} 的相似度: {similarity:.4f}')
                        
                        # 检查各自的嵌入向量
                        if kp1.embedding and kp2.embedding:
                            try:
                                emb1 = np.array([float(x) for x in kp1.embedding.split(',')])
                                emb2 = np.array([float(x) for x in kp2.embedding.split(',')])
                                self.stdout.write(f'    {kp1.name} 嵌入向量维度: {len(emb1)}')
                                self.stdout.write(f'    {kp2.name} 嵌入向量维度: {len(emb2)}')
                            except Exception as e:
                                self.stdout.write(f'    嵌入向量解析失败: {str(e)}')
            
            # 检查嵌入向量的质量
            if kps_with_embedding > 0:
                self.stdout.write('\n检查嵌入向量质量:')
                sample_kp = KnowledgePoint.objects.exclude(embedding='').first()
                if sample_kp.embedding:
                    try:
                        emb = np.array([float(x) for x in sample_kp.embedding.split(',')])
                        self.stdout.write(f'  示例知识点 "{sample_kp.name}" 嵌入向量:')
                        self.stdout.write(f'    维度: {len(emb)}')
                        self.stdout.write(f'    范数: {np.linalg.norm(emb):.6f}')
                        self.stdout.write(f'    前5个值: {[f"{x:.6f}" for x in emb[:5]]}')
                    except Exception as e:
                        self.stdout.write(f'  嵌入向量解析失败: {str(e)}')
            
            self.stdout.write(
                self.style.SUCCESS('诊断完成')
            )
        except Exception as e:
            logger.error(f"诊断知识点相似度问题失败: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f'诊断失败: {str(e)}')
            )