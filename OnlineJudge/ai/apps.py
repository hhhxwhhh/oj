from django.apps import AppConfig
import logging
logger=logging.getLogger(__name__)

class AiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai'

    def ready(self):
        try:
            from ai.dl_models.deep_learning import EnhancedQLearningRecommender
            global ql_recommender
            ql_recommender = EnhancedQLearningRecommender(state_size=16, action_size=7)
            logger.info("强化学习推荐器初始化成功")
        except Exception as e:
            logger.error(f"初始化强化学习推荐器失败: {str(e)}")
