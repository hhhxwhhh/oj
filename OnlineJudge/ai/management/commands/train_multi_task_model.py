import logging
from django.core.management.base import BaseCommand
from ai.dl_models.multi_task_model import MultiTaskRecommender
from account.models import User
from submission.models import Submission
from problem.models import Problem
import logging
import numpy as np

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '训练多任务学习模型（同时进行能力评估和题目推荐）'

    def add_arguments(self, parser):
        parser.add_argument('--epochs', type=int, default=100,
                           help='训练轮数')
        parser.add_argument('--users', type=int, default=100,
                           help='训练的用户数量')
        parser.add_argument('--batch-size', type=int, default=32,
                           help='批次大小')
        parser.add_argument('--learning-rate', type=float, default=0.001,
                           help='学习率')

    def handle(self, *args, **options):
        epochs = options['epochs']
        users = options['users']
        batch_size = options['batch_size']
        learning_rate = options['learning_rate']
        
        self.stdout.write(f'开始训练多任务学习模型...')
        self.stdout.write(f'参数: 轮数={epochs}, 用户数={users}, 批次大小={batch_size}, 学习率={learning_rate}')
        
        try:
            # 获取训练用户
            user_ids = list(Submission.objects.values_list('user_id', flat=True).distinct()[:users])
            
            if not user_ids:
                self.stdout.write(self.style.WARNING('未找到真实用户，创建虚拟用户进行训练'))
                user_ids = list(range(1, users + 1))
            
            self.stdout.write(f'开始训练 {len(user_ids)} 个用户的多任务模型...')
            
            # 初始化多任务推荐器
            recommender = MultiTaskRecommender()
            
            # 准备训练数据
            self.stdout.write('准备训练数据...')
            training_data = self.prepare_training_data(user_ids)
            
            if not training_data:
                self.stdout.write(self.style.ERROR('没有可用的训练数据'))
                return
            
            # 训练模型
            user_features, problem_features, ability_labels, recommendation_labels = training_data
            recommender.train(
                user_features, 
                problem_features, 
                ability_labels, 
                recommendation_labels, 
                epochs=epochs
            )
            
            self.stdout.write(
                self.style.SUCCESS('多任务学习模型训练完成')
            )
            
        except Exception as e:
            logger.error(f"训练多任务学习模型失败: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f'训练多任务学习模型失败: {str(e)}')
            )

    def prepare_training_data(self, user_ids):
        """
        准备多任务学习训练数据
        """
        try:
            from ai.service import AIProgrammingAbilityService, AIRecommendationService
            
            user_features_list = []
            problem_features_list = []
            ability_labels_list = []
            recommendation_labels_list = []
            
            # 为每个用户构建训练数据
            for user_id in user_ids:
                # 获取用户特征
                user_features = AIProgrammingAbilityService._extract_ml_features(user_id)
                
                # 获取用户提交记录
                submissions = Submission.objects.filter(user_id=user_id)
                solved_problems = submissions.filter(result=0).values_list('problem_id', flat=True)
                
                # 为每个已解决的题目添加正样本
                for problem_id in solved_problems:
                    try:
                        # 获取题目特征
                        problem_features = AIRecommendationService._extract_problem_features(problem_id)
                        
                        # 构造能力标签（使用现有评估结果）
                        ability_record = None
                        try:
                            from ai.models import AIProgrammingAbility
                            ability_record = AIProgrammingAbility.objects.get(user_id=user_id)
                        except:
                            pass
                        
                        if ability_record:
                            ability_labels = [
                                ability_record.basic_programming_score,
                                ability_record.data_structure_score,
                                ability_record.algorithm_design_score,
                                ability_record.problem_solving_score,
                                ability_record.overall_score
                            ]
                        else:
                            # 使用默认值
                            ability_labels = [20.0, 20.0, 20.0, 20.0, 20.0]
                        
                        user_features_list.append(user_features)
                        problem_features_list.append(problem_features)
                        ability_labels_list.append(ability_labels)
                        recommendation_labels_list.append(1.0)  # 正样本
                    except Exception as e:
                        logger.warning(f"处理用户 {user_id} 的题目 {problem_id} 时出错: {str(e)}")
                        continue
                
                # 添加负样本（未解决的题目）
                unsolved_problems = Problem.objects.filter(visible=True).exclude(
                    id__in=solved_problems
                )[:len(solved_problems)] if len(solved_problems) > 0 else Problem.objects.filter(visible=True)[:5]
                
                for problem in unsolved_problems:
                    try:
                        # 获取题目特征
                        problem_features = AIRecommendationService._extract_problem_features(problem.id)
                        
                        # 构造能力标签（使用现有评估结果）
                        ability_record = None
                        try:
                            from ai.models import AIProgrammingAbility
                            ability_record = AIProgrammingAbility.objects.get(user_id=user_id)
                        except:
                            pass
                        
                        if ability_record:
                            ability_labels = [
                                ability_record.basic_programming_score,
                                ability_record.data_structure_score,
                                ability_record.algorithm_design_score,
                                ability_record.problem_solving_score,
                                ability_record.overall_score
                            ]
                        else:
                            # 使用默认值
                            ability_labels = [20.0, 20.0, 20.0, 20.0, 20.0]
                        
                        user_features_list.append(user_features)
                        problem_features_list.append(problem_features)
                        ability_labels_list.append(ability_labels)
                        recommendation_labels_list.append(0.0)  # 负样本
                    except Exception as e:
                        logger.warning(f"处理用户 {user_id} 的负样本题目 {problem.id} 时出错: {str(e)}")
                        continue
            
            if not user_features_list:
                return None
                
            return (
                np.array(user_features_list),
                np.array(problem_features_list),
                np.array(ability_labels_list),
                np.array(recommendation_labels_list)
            )
            
        except Exception as e:
            logger.error(f"准备训练数据失败: {str(e)}")
            return None