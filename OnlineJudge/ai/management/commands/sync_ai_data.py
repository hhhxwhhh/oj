from django.core.management.base import BaseCommand
from submission.models import Submission
from ai.service import KnowledgePointService, AbilityAssessmentService
from submission.models import JudgeStatus
class Command(BaseCommand):
    help = 'Sync AI data for all submissions'
    
    def handle(self, *args, **options):
        submissions = Submission.objects.all()
        total = submissions.count()
        
        for i, submission in enumerate(submissions):
            try:
                is_correct = (submission.result == JudgeStatus.ACCEPTED)
                score = submission.statistic_info.get("score", 0)
                
                # 更新知识点掌握情况
                KnowledgePointService.update_user_knowledge_state(
                    submission.user_id,
                    submission.problem_id,
                    is_correct
                )
                
                # 更新编程能力评估
                AbilityAssessmentService.update_user_ability_assessment(
                    submission.user_id,
                    submission.problem_id,
                    is_correct,
                    score
                )
                
                if i % 100 == 0:
                    self.stdout.write(f'Processed {i}/{total} submissions')
                    
            except Exception as e:
                self.stderr.write(f'Error processing submission {submission.id}: {str(e)}')
