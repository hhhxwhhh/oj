import sys
from django.core.management.base import BaseCommand
from django.db import transaction
from problem.models import Problem, ProblemTag
from ai.service import AIService
from ai.models import AIModel

class Command(BaseCommand):
    help = '为所有题目自动生成标签'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='每批处理的题目数量'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制重新生成所有题目的标签'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        force = options['force']
        
        # 检查是否有激活的AI模型
        if not AIModel.objects.filter(is_active=True).exists():
            self.stdout.write(
                self.style.ERROR('没有激活的AI模型，请先配置AI模型')
            )
            return
            
        # 获取所有题目
        problems = Problem.objects.all()
        
        total_problems = problems.count()
        if total_problems == 0:
            self.stdout.write('没有需要处理的题目')
            return
            
        self.stdout.write(f'总共需要处理 {total_problems} 道题目')
        
        processed = 0
        failed = 0
        
        for i in range(0, total_problems, batch_size):
            batch = problems[i:i+batch_size]
            
            for problem in batch:
                try:
                    with transaction.atomic():
                        # 生成标签
                        tags = self.generate_tags_for_problem(problem)
                        
                        # 清除旧标签
                        problem.tags.clear()
                        
                        # 添加新标签
                        for tag_name in tags:
                            tag, created = ProblemTag.objects.get_or_create(name=tag_name)
                            problem.tags.add(tag)
                        
                        problem.save()
                        processed += 1
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'成功为题目 {problem._id} 生成标签: {", ".join(tags)}'
                            )
                        )
                        
                except Exception as e:
                    failed += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'处理题目 {problem._id} 失败: {str(e)}'
                        )
                    )
            
            self.stdout.write(f'已处理 {min(i+batch_size, total_problems)}/{total_problems} 道题目')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'处理完成！成功: {processed}, 失败: {failed}'
            )
        )

    def generate_tags_for_problem(self, problem):
        """
        为题目生成标签
        """
        prompt = f"""
        请根据以下编程题目内容，提取3-5个最能代表题目核心知识点和算法的标签。
        标签应该是简洁的关键词，如"动态规划"、"图论"、"贪心算法"等。
        
        题目ID: {problem._id}
        题目标题: {problem.title}
        题目描述: {problem.description}
        输入描述: {problem.input_description}
        输出描述: {problem.output_description}
        
        请只返回标签列表，每个标签用逗号分隔，不需要其他文字说明。
        例如: 动态规划,贪心算法,数组
        """
        
        try:
            # 调用AI服务生成标签
            messages = [{"role": "user", "content": prompt}]
            ai_response = AIService.call_ai_model(messages)
            
            # 解析AI响应
            tags = [tag.strip() for tag in ai_response.strip().split(',')]
            # 过滤掉空标签并限制数量
            tags = [tag for tag in tags if tag][:5]
            
            if not tags:
                # 如果AI没有返回有效标签，使用默认标签
                tags = ['算法', '编程']
                
            return tags
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(
                    f'为题目 {problem._id} 生成标签时出错，使用默认标签: {str(e)}'
                )
            )
            return ['算法', '编程']