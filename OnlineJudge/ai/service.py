import openai
import requests
import json
import re
from django.db import transaction,models
from django.utils import timezone
from .models import AIModel, AIMessage,AICodeExplanationCache,AIUserKnowledgeState,AIUserLearningPath,AIUserLearningPathNode
from .models import KnowledgePoint,AIUserKnowledgeState,AIAbilityDimension,AIProgrammingAbility,AIUserAbilityDetail
from problem.models import Problem,ProblemTag
from submission.models import Submission
import logging
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os
from collections import defaultdict
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import hashlib
from account.models import User
import torch
from .models.deep_learning import DeepLearningAbilityAssessor,ProblemRecommendationNet
from .models.recommendation_model import DeepLearningRecommender
logger=logging.getLogger(__name__)

class AIService:
    @staticmethod
    def get_active_ai_model():
        try:
            active_model=AIModel.objects.filter(is_active=True).first()
            return active_model
        except AIModel.DoesNotExist:
            logger.error("No active AI model found")
            return None
    @staticmethod
    def call_ai_model(messages, ai_model=None):
        if ai_model is None:
            ai_model = AIService.get_active_ai_model()
        if not ai_model:
            raise Exception("No active AI model found")
        
        if ai_model.provider == "openai":
            return AIService._call_openai(messages, ai_model)
        elif ai_model.provider == "azure":
            return AIService._call_azure(messages, ai_model)
        elif ai_model.provider == "openkey":
            return AIService._call_openkey(messages, ai_model)
        elif ai_model.provider == "deepseek":
            return AIService._call_deepseek(messages, ai_model)
        else:
            raise Exception(f"Unsupported AI provider: {ai_model.provider}")

    @staticmethod
    def _call_openkey(messages, ai_model):
        import requests
        import json
        
        url = "https://openkey.cloud/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {ai_model.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": ai_model.model,
            "messages": messages,
            **ai_model.config
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        except requests.exceptions.Timeout:
            logger.error("OpenKey API request timed out")
            raise Exception("AI服务调用超时，请稍后重试")
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenKey API request error: {str(e)}")
            raise Exception(f"AI服务调用失败: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in _call_openkey: {str(e)}")
            raise Exception(f"Unexpected error: {str(e)}")
    @staticmethod
    def _call_deepseek(messages, ai_model):
        import requests
        import json
        
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {ai_model.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": ai_model.model,
            "messages": messages,
            **ai_model.config
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        except requests.exceptions.Timeout:
            logger.error("DeepSeek API request timed out")
            raise Exception("AI服务调用超时，请稍后重试")
        except requests.exceptions.RequestException as e:
            logger.error(f"DeepSeek API request error: {str(e)}")
            raise Exception(f"AI服务调用失败: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in _call_deepseek: {str(e)}")
            raise Exception(f"Unexpected error: {str(e)}")
    @staticmethod
    def _call_azure(messages, ai_model):
        import requests
        import json
        
        # Azure OpenAI需要不同的端点格式
        url = ai_model.config.get("endpoint", "") + "/openai/deployments/" + ai_model.model + "/chat/completions?api-version=" + ai_model.config.get("api_version", "2023-05-15")
        headers = {
            "api-key": ai_model.api_key,
            "Content-Type": "application/json"
        }
        
        # Azure需要移除一些配置项
        filtered_config = {k: v for k, v in ai_model.config.items() if k not in ["endpoint", "api_version"]}
        data = {
            "messages": messages,
            **filtered_config
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        except requests.exceptions.Timeout:
            logger.error("Azure API request timed out")
            raise Exception("AI服务调用超时，请稍后重试")
        except requests.exceptions.RequestException as e:
            logger.error(f"Azure API request error: {str(e)}")
            raise Exception(f"AI服务调用失败: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in _call_azure: {str(e)}")
            raise Exception(f"Unexpected error: {str(e)}")
    
    @staticmethod
    def _call_openai(messages, ai_model):
        import requests
        import json
        
        # 检查是否使用OpenKey服务
        if "openkey.cloud" in ai_model.api_key:
            url = "https://api.openkey.cloud/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {ai_model.api_key}",
                "Content-Type": "application/json"
            }
        else:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {ai_model.api_key}",
                "Content-Type": "application/json"
            }
            
        data = {
            "model": ai_model.model,
            "messages": messages,
            **ai_model.config
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        except requests.exceptions.Timeout:
            logger.error("OpenAI API request timed out")
            raise Exception("AI服务调用超时，请稍后重试")
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenAI API request error: {str(e)}")
            raise Exception(f"AI服务调用失败: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in _call_openai: {str(e)}")
            raise Exception(f"Unexpected error: {str(e)}")
    
    @staticmethod
    def get_chat_history(conversation_id):
        messages=AIMessage.objects.filter(conversation_id=conversation_id).order_by("create_time")
        return [{"role":message.role,"content":message.content} for message in messages]
    
    @staticmethod
    def generate_problem_solution(problem_id):
        try:
            problem = Problem.objects.get(id=problem_id)
        except Problem.DoesNotExist:
            raise Exception("Problem not found")
        
        prompt = f"题目: {problem.title}\n描述: {problem.description}\n\n请提供解题思路和要点:"
        messages = [{"role": "user", "content": prompt}]
        
        ai_model = AIService.get_active_ai_model()
        if not ai_model:
            raise Exception("No active AI model found")
        
        return AIService.call_ai_model(messages, ai_model)
    
    @staticmethod
    def review_code(problem_id,code,language):
        try:
            problem = Problem.objects.get(id=problem_id)
        except Problem.DoesNotExist:
            raise Exception("Problem not found")
        
        prompt = f"题目: {problem.title}\n描述: {problem.description}\n\n请审查以下{language}代码并提供改进建议:\n\n{code}\n\n审查结果:"
        messages = [{"role": "user", "content": prompt}]
        
        ai_model = AIService.get_active_ai_model()
        if not ai_model:
            raise Exception("No active AI model found")
        
        return AIService.call_ai_model(messages, ai_model)
    
    @staticmethod
    def diagnose_submission(submission_id):
        try:
            submission=Submission.objects.select_related("problem").get(id=submission_id)
        except Submission.DoesNotExist:
            raise Exception("Submission not found")
        problem=submission.problem
        code=submission.code  
        result=submission.result 
        info=submission.info 
        language=submission.language

        result_text_map = {
            -1: "答案错误(Wrong Answer)",
            1: "CPU时间限制 exceeded",
            2: "运行时间超限(Real Time Limit Exceeded)",
            3: "内存超限(Memory Limit Exceeded)",
            4: "运行时错误(Runtime Error)",
            5: "系统错误(System Error)"
        }
        result_text = result_text_map.get(result, "未知错误")
        
        prompt = f"""
                    题目: {problem.title}
                    描述: {problem.description}

                    学生提交的{language}代码:
                    {code}

                    判题结果: {result_text}

                    详细信息: {info if info else "无"}

                    请分析这段代码可能存在的问题，并提供具体的修改建议。
                    如果可能，请给出修改后的代码示例。
                    """.strip()
        messages=[{"role":"user","content":prompt}]
        ai_model=AIService.get_active_ai_model()
        if not ai_model:
            raise Exception("No active AI model found")
        return AIService.call_ai_model(messages,ai_model)
    

    @staticmethod
    def recommend_problems(user_id,count=5):
        from django.db.models import Count
        from account.models import User
        try:
            user=User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise Exception("User not found")
        solved_submissions=Submission.objects.filter(
            user_id=user_id,
            result=0
        ).select_related("problem")
        solved_problems=[sub.problem for sub in solved_submissions]
        solved_tags=[]
        for problem in solved_problems:
            solved_tags.extend(problem.tags.all())

        from problem.models import Problem

        recommended_problems=Problem.objects.filter(
            tags__in=solved_tags,
            visible=True
        ).exclude(
            id__in=[problem.id for problem in solved_problems]
        ).distinct().order_by('?')[:count]

        problem_list = "\n".join([
            f"{i+1}. {problem.title}" for i, problem in enumerate(recommended_problems)
        ])

        prompt = f"""
                    根据用户已完成的题目和掌握的知识点，推荐{count}道适合练习的OJ题目。

                    用户已完成的题目涉及知识点包括：{', '.join([tag.name for tag in set(solved_tags)])}

                    推荐的题目列表：
                    {problem_list}

                    请为这些题目写一段推荐理由，说明为什么这些题目适合该用户进一步提升。
                    """.strip()
        
        messages = [{"role": "user", "content": prompt}]
        
        ai_model = AIService.get_active_ai_model()
        if not ai_model:
            raise Exception("No active AI model found")
            
        recommendation = AIService.call_ai_model(messages, ai_model)
        return {
            "problems": [{"id": p.id, "title": p.title} for p in recommended_problems],
            "recommendation": recommendation
        }
    @staticmethod
    def generate_code_explanation(code, language):
        try:
            prompt = f"请用中文详细解释以下{language}代码的功能和逻辑:\n\n{code}\n\n解释:"
            messages = [{"role": "user", "content": prompt}]
            
            ai_model = AIService.get_active_ai_model()
            if not ai_model:
                raise Exception("No active AI model found")
            
            return AIService.call_ai_model(messages, ai_model)
        except Exception as e:
            logger.error(f"Error in generate_code_explanation: {str(e)}")
            raise Exception(f"Failed to generate code explanation: {str(e)}")

    @staticmethod
    def generate_real_time_suggestion(code, language, cursor_position, problem_id=None):
        """
        根据当前代码和光标位置生成实时建议
        """
        try:
            # 构建提示语
            problem_context = ""
            if problem_id:
                try:
                    problem = Problem.objects.get(id=problem_id)
                    problem_context = f"题目: {problem.title}\n题目描述: {problem.description}\n\n"
                except Problem.DoesNotExist:
                    pass

            prompt = f"""
{problem_context}请根据以下{language}代码和光标位置提供实时编程建议：

代码:
{code}

光标位置: {cursor_position}

请提供以下信息：
1. 在光标位置可能的代码补全建议
2. 当前代码行的潜在问题或改进建议
3. 相关的编程知识点提醒

请以以下JSON格式返回结果：
{{
    "suggestions": ["建议1", "建议2", "建议3"],
    "completions": ["补全选项1", "补全选项2"],
    "issues": ["潜在问题1", "潜在问题2"],
    "knowledge_points": ["相关知识点1", "相关知识点2"]
}}
""".strip()

            messages = [
                {"role": "system", "content": "你是一个专业的编程助手，擅长提供实时编程建议和代码补全。"},
                {"role": "user", "content": prompt}
            ]
            
            ai_model = AIService.get_active_ai_model()
            if not ai_model:
                raise Exception("No active AI model found")
            
            response = AIService.call_ai_model(messages, ai_model)
            
            # 解析JSON响应
            import json
            import re
            
            # 尝试提取JSON内容
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                response = json_match.group()
            
            suggestion_data = json.loads(response)
            return suggestion_data
            
        except Exception as e:
            logger.error(f"Failed to generate real-time suggestion: {str(e)}")
            # 返回默认建议
            return {
                "suggestions": ["继续编写代码", "检查语法错误"],
                "completions": [],
                "issues": [],
                "knowledge_points": []
            }
        
    @staticmethod
    def auto_complete_code(code, language, prefix, problem_id=None):
        """
        根据当前代码和前缀提供代码自动补全建议
        """
        try:
            # 构建提示语
            problem_context = ""
            if problem_id:
                try:
                    problem = Problem.objects.get(id=problem_id)
                    problem_context = f"题目: {problem.title}\n题目描述: {problem.description}\n\n"
                except Problem.DoesNotExist:
                    pass

            prompt = f"""
{problem_context}请根据以下{language}代码和输入前缀提供代码自动补全建议：

代码:
{code}

输入前缀: {prefix}

请提供以下信息：
1. 可能的补全选项列表（最多5个）
2. 每个选项的简要说明

请以以下JSON格式返回结果：
{{
    "completions": [
        {{"text": "补全文本1", "description": "说明1"}},
        {{"text": "补全文本2", "description": "说明2"}}
    ]
}}
""".strip()

            messages = [
                {"role": "system", "content": "你是一个专业的编程助手，擅长提供代码自动补全建议。"},
                {"role": "user", "content": prompt}
            ]
            
            ai_model = AIService.get_active_ai_model()
            if not ai_model:
                raise Exception("No active AI model found")
            
            response = AIService.call_ai_model(messages, ai_model)
            
            # 解析JSON响应
            import json
            import re
            
            # 尝试提取JSON内容
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                response = json_match.group()
            
            completion_data = json.loads(response)
            return completion_data
            
        except Exception as e:
            logger.error(f"Failed to generate auto completion: {str(e)}")
            # 返回默认补全
            return {
                "completions": [
                {"text": prefix + "printf", "description": "格式化输出函数"},
                {"text": prefix + "scanf", "description": "格式化输入函数"},
                {"text": prefix + "if", "description": "条件语句"},
                {"text": prefix + "for", "description": "循环语句"}
            ]
            }

class AIRecommendationService:
    @staticmethod
    def get_code_hash(code, language):
        """生成代码的哈希值"""
        hash_string = f"{code}:{language}"
        return hashlib.md5(hash_string.encode('utf-8')).hexdigest()
    
    @staticmethod
    def get_cached_explanation(code, language):
        """获取缓存的代码解释"""
        try:
            code_hash = AIRecommendationService.get_code_hash(code, language)
            cached_explanation = AICodeExplanationCache.objects.get(code_hash=code_hash)
            cached_explanation.usage_count += 1
            cached_explanation.save(update_fields=['usage_count'])
            return cached_explanation.explanation
        except AICodeExplanationCache.DoesNotExist:
            return None
    @staticmethod
    def get_user_problem_matrix():
        """构建用户-题目矩阵"""
        submissions=Submission.objects.filter(
            result=0
        )
        user_problems=defaultdict(set)
        for submission in submissions:
            user_problems[submission.user_id].add(submission.problem_id)
        return user_problems
    
    def cache_explanation(code, language, explanation):
        """缓存代码解释"""
        try:
            code_hash = AIRecommendationService.get_code_hash(code, language)
            AICodeExplanationCache.objects.create(
                code_hash=code_hash,
                language=language,
                explanation=explanation
            )
        except Exception as e:
            logger.warning(f"Failed to cache code explanation: {str(e)}")
    @staticmethod
    def calculate_similarity_matrix(user_problems,target_user_id):
        """基于用户的解题记录 计算用户的相似度矩阵"""
        if target_user_id not in user_problems:
            raise Exception("Target user not found")
        target_problems=user_problems[target_user_id]
        similarities={}
        for user_id,problems in user_problems.items():
            if target_user_id==user_id:
                continue
            intersection = len(target_problems.intersection(problems))
            union = len(target_problems.union(problems))
            if union >0:
                similarty=intersection/union
                similarities[user_id]=similarty

        return similarities
    
    @staticmethod
    def collaborative_filtering_recommendations(user_id,count=10):
        """基于协同过滤推荐算法"""
        user_problems=AIRecommendationService.get_user_problem_matrix()
        similarities=AIRecommendationService.calculate_similarity_matrix(user_problems=user_problems,target_user_id=user_id)
        solved_problems=user_problems.get(user_id,set())
        candidate_problems=defaultdict(float)
        for similar_user_id ,similarty in similarities.items():
            if similarty>0.1:
                for problem_id in user_problems[similar_user_id]:
                    if problem_id not in solved_problems:
                        candidate_problems[problem_id]+=similarty
        sorted_candidate_problems=sorted(candidate_problems.items(),key=lambda x: x[1],reverse=True)
        return [(problem_id, score, "基于相似用户推荐") for problem_id, score in sorted_candidate_problems[:count]]
    @staticmethod
    def content_based_recommendations(user_id,count=10):
        """基于内容的推荐：使用TF-IDF和余弦相似度分析题目描述相似性"""
        try:
            # 获取用户已解决的题目
            solved_problems = Submission.objects.filter(
                user_id=user_id,
                result=0
            ).select_related('problem')
            
            if not solved_problems:
                # 如果用户没有解决问题，返回热门题目
                from problem.models import Problem
                problems = Problem.objects.filter(visible=True).order_by("-accepted_number")[:count]
                return [(p.id, 0.5, "热门题目推荐") for p in problems]
            
            # 获取所有可见题目
            from problem.models import Problem
            all_problems = Problem.objects.filter(visible=True)
            
            # 提取已解决问题的描述
            solved_descriptions = [sp.problem.description for sp in solved_problems if sp.problem.description]
            # 如果没有描述，使用标题
            if not solved_descriptions:
                solved_descriptions = [sp.problem.title for sp in solved_problems]
            
            # 提取所有题目的描述
            all_descriptions = [p.description if p.description else p.title for p in all_problems]
            
            # 合并已解决问题和所有题目的描述用于TF-IDF
            all_texts = solved_descriptions + all_descriptions
            
            # 创建TF-IDF向量
            vectorizer = TfidfVectorizer(max_features=1000, stop_words=None, ngram_range=(1, 2))
            tfidf_matrix = vectorizer.fit_transform(all_texts)
            
            # 分离已解决问题向量和所有题目向量
            solved_tfidf = tfidf_matrix[:len(solved_descriptions)]
            all_problems_tfidf = tfidf_matrix[len(solved_descriptions):]
            
            # 计算余弦相似度
            similarity_matrix = cosine_similarity(solved_tfidf, all_problems_tfidf)
            
            # 计算每个题目的平均相似度
            avg_similarities = similarity_matrix.mean(axis=0)
            
            # 获取已解决的题目ID集合
            solved_problem_ids = set(sp.problem.id for sp in solved_problems)
            
            # 创建(题目ID, 相似度, 推荐理由)元组列表
            recommendations = []
            for i, problem in enumerate(all_problems):
                # 排除已解决的题目
                if problem.id in solved_problem_ids:
                    continue
                
                similarity_score = avg_similarities[i]
                recommendations.append((problem.id, similarity_score, "基于题目内容相似性推荐"))
            
            # 按相似度排序并返回前count个
            recommendations.sort(key=lambda x: x[1], reverse=True)
            return recommendations[:count]
            
        except Exception as e:
            logger.error(f"Content-based recommendation failed: {str(e)}")
            # 出错时返回基于标签的推荐
            solved_submissions=Submission.objects.filter(
                user_id=user_id,
                result=0
            ).select_related("problem")
            solved_problems=[sub.problem for sub in solved_submissions]

            if not solved_problems:
                popular_problems=Problem.objects.filter(visible=True).order_by("-accepted_number")[:count]
                return [(problem.id, 0, "基于热门题目推荐") for problem in popular_problems]
            solved_tags=set()
            for problem in solved_problems:
                for tag in problem.tags.all():
                    solved_tags.add(tag)

            unsolved_problems = Problem.objects.filter(visible=True).exclude(
                id__in=[p.id for p in solved_problems]
            ).prefetch_related('tags')
            candidate_problems=[]
            for problem in unsolved_problems:
                problem_tags = {tag.name for tag in problem.tags.all()}
                if solved_tags and problem_tags:
                    intersection=len(solved_tags.intersection(problem_tags))
                    union=len(solved_tags.union(problem_tags))
                    if union>0:
                        similarty=intersection/union
                        candidate_problems.append((problem.id,similarty,"基于标签推荐"))

            candidate_problems.sort(key=lambda x:x[1],reverse=True)
            return candidate_problems[:count]
    @staticmethod
    def hybrid_recommendations(user_id, count=10):
        """
        混合推荐算法，结合协同过滤和内容推荐，并考虑用户行为数据
        """
        # 获取各种推荐结果
        cf_recommendations = AIRecommendationService.collaborative_filtering_recommendations(user_id=user_id, count=count*2)
        cb_recommendations = AIRecommendationService.content_based_recommendations(user_id=user_id, count=count*2)
        
        # 获取用户行为数据
        behavior_weights = AIRecommendationService._get_user_behavior_weights(user_id)
        
        problem_scores = defaultdict(list)
        for problem_id, score, reason in cf_recommendations:
            problem_scores[problem_id].append((score, reason))
        for problem_id, score, reason in cb_recommendations:
            problem_scores[problem_id].append((score, reason))
            
        final_recommendations = []
        for problem_id, scores_reasons in problem_scores.items():
            # 计算平均分数
            avg_score = sum(score for score, _ in scores_reasons) / len(scores_reasons)
            
            # 获取该题目的行为权重
            behavior_weight = behavior_weights.get(problem_id, 1.0)
            
            # 综合分数 = 平均分数 * 行为权重
            final_score = avg_score * behavior_weight
            
            reasons = list(set(reason for _, reason in scores_reasons))
            combined_reason = ", ".join(reasons)
            
            final_recommendations.append((problem_id, final_score, combined_reason))

        # 按分数排序
        final_recommendations.sort(key=lambda x: x[1], reverse=True)
        return final_recommendations[:count]
    
    @staticmethod
    def _get_user_behavior_weights(user_id):
        """
        根据用户行为数据计算题目推荐权重
        考虑提交频率、通过率等行为因素
        """
        try:
            from django.db.models import Count
            from submission.models import Submission
            
            # 获取用户最近的提交行为
            recent_submissions = Submission.objects.filter(
                user_id=user_id
            ).order_by('-create_time')[:50]  # 最近50次提交
            
            if not recent_submissions:
                return {}
            
            # 统计各题目的提交次数和通过次数
            problem_stats = {}
            for submission in recent_submissions:
                problem_id = submission.problem_id
                if problem_id not in problem_stats:
                    problem_stats[problem_id] = {'total': 0, 'accepted': 0}
                
                problem_stats[problem_id]['total'] += 1
                if submission.result == 0:  # 0表示通过
                    problem_stats[problem_id]['accepted'] += 1
            
            # 计算行为权重
            behavior_weights = {}
            for problem_id, stats in problem_stats.items():
                # 通过率越高，相似题目的推荐权重越低（用户已经掌握相关知识点）
                # 提交次数越多，相似题目的推荐权重越低（用户已经练习过相关知识点）
                acceptance_rate = stats['accepted'] / stats['total'] if stats['total'] > 0 else 0
                submission_count = stats['total']
                
                # 权重计算公式：基础权重 * 通过率惩罚因子 * 提交次数惩罚因子
                base_weight = 1.0
                acceptance_penalty = 1 - acceptance_rate * 0.5  # 通过率越高，惩罚越大
                submission_penalty = max(0.5, 1 - submission_count * 0.02)  # 提交次数越多，惩罚越大
                
                behavior_weights[problem_id] = base_weight * acceptance_penalty * submission_penalty
                
            return behavior_weights
        except Exception as e:
            logger.error(f"Failed to get user behavior weights: {str(e)}")
            return {}

    @staticmethod
    def ml_hybrid_recommendations(user_id, count=10):
        """
        基于机器学习的混合推荐算法
        """
        try:
            # 获取协同过滤和内容推荐的结果
            cf_recommendations = AIRecommendationService.collaborative_filtering_recommendations(user_id, count*2)
            cb_recommendations = AIRecommendationService.content_based_recommendations(user_id, count*2)
            
            # 构建训练数据用于学习最佳组合权重
            train_data = []
            for problem_id, score, reason in cf_recommendations:
                train_data.append((problem_id, score, 'cf', reason))
            for problem_id, score, reason in cb_recommendations:
                train_data.append((problem_id, score, 'cb', reason))
            
            problem_scores = defaultdict(list)
            for problem_id, score, method, reason in train_data:
                problem_scores[problem_id].append((score, method, reason))
            
            # 计算综合得分
            final_recommendations = []
            for problem_id, scores_reasons in problem_scores.items():
                # 简单平均
                avg_score = sum(score for score, _, _ in scores_reasons) / len(scores_reasons)
                
                # 收集推荐理由
                reasons = list(set(reason for _, _, reason in scores_reasons))
                combined_reason = ", ".join(reasons)
                
                final_recommendations.append((problem_id, avg_score, combined_reason))
            
            # 按分数排序
            final_recommendations.sort(key=lambda x: x[1], reverse=True)
            return final_recommendations[:count]
            
        except Exception as e:
            logger.error(f"ML hybrid recommendation failed: {str(e)}")
            # 回退到传统的混合推荐
            return AIRecommendationService.hybrid_recommendations(user_id, count)
    
    @staticmethod
    def _extract_user_problem_features(user_id, problem_id):
        """
        提取用户-题目的特征用于机器学习推荐
        """
        try:
            # 获取用户特征
            user_features = AIRecommendationService._build_user_features(user_id)
            
            # 获取题目
            problem = Problem.objects.get(id=problem_id)
            problem_features = AIRecommendationService._build_problem_features(problem)
            
            # 构建交互特征
            # 用户整体通过率与题目通过率的匹配度
            user_acc_rate = user_features.get('acceptance_rate', 0)
            problem_acc_rate = problem_features.get('acceptance_rate', 0)
            acc_rate_diff = abs(user_acc_rate - problem_acc_rate)
            
            # 用户擅长的标签与题目标签的匹配度
            user_tags = set(user_features.get('top_tags', {}).keys())
            problem_tags = set(problem_features.get('tags', []))
            tag_overlap = len(user_tags.intersection(problem_tags))
            tag_union = len(user_tags.union(problem_tags))
            tag_similarity = tag_overlap / tag_union if tag_union > 0 else 0
            
            # 难度匹配度
            user_high_count = user_features.get('high_difficulty_count', 0)
            user_mid_count = user_features.get('mid_difficulty_count', 0)
            user_low_count = user_features.get('low_difficulty_count', 0)
            total_solved = user_high_count + user_mid_count + user_low_count
            
            if total_solved > 0:
                user_pref_difficulty = (
                    1 * user_low_count + 
                    2 * user_mid_count + 
                    3 * user_high_count
                ) / total_solved
            else:
                user_pref_difficulty = 2  # 默认中等难度
            
            problem_difficulty = problem_features.get('difficulty', 2)
            difficulty_match = 1 - abs(user_pref_difficulty - problem_difficulty) / 2  # 归一化到0-1
            
            # 构建特征向量
            features = [
                user_acc_rate,
                problem_acc_rate,
                acc_rate_diff,
                tag_similarity,
                user_pref_difficulty,
                problem_difficulty,
                difficulty_match,
                problem_features.get('submission_number', 0),
                problem_features.get('accepted_number', 0),
                tag_overlap,
                len(user_tags),
                len(problem_tags)
            ]
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting user-problem features for user {user_id}, problem {problem_id}: {str(e)}")
            return [0] * 12
    @staticmethod
    def train_recommendation_model():
        """
        训练推荐模型
        """
        try:
            from sklearn.linear_model import LogisticRegression
            from sklearn.model_selection import train_test_split
            
            # 准备训练数据
            X = []  # 特征
            y = []  # 标签（用户是否解决了题目）
            
            # 获取所有提交记录作为训练数据
            submissions = Submission.objects.all()[:10000]  # 限制数据量以避免内存问题
            
            for submission in submissions:
                features = AIRecommendationService._extract_user_problem_features(
                    submission.user_id, submission.problem_id
                )
                label = 1 if submission.result == 0 else 0  # 0表示正确解决
                
                X.append(features)
                y.append(label)
            
            if len(X) < 100:  # 数据太少不训练
                return None
            
            # 转换为numpy数组
            import numpy as np
            X = np.array(X)
            y = np.array(y)
            
            # 划分训练集和测试集
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # 训练逻辑回归模型
            model = LogisticRegression(random_state=42, max_iter=1000)
            model.fit(X_train, y_train)
            
            # 评估模型
            train_score = model.score(X_train, y_train)
            test_score = model.score(X_test, y_test)
            
            logger.info(f"Recommendation model trained. Train accuracy: {train_score:.4f}, Test accuracy: {test_score:.4f}")
            
            # 保存模型
            model_dir = 'ai/models/ml_models'
            if not os.path.exists(model_dir):
                os.makedirs(model_dir)
            joblib.dump(model, f'{model_dir}/recommendation_model.pkl')
            
            return model
            
        except Exception as e:
            logger.error(f"Error training recommendation model: {str(e)}")
            return None
        
    @staticmethod
    def ml_enhanced_recommendations(user_id, count=10):
        """
        使用机器学习增强的推荐算法
        """
        try:
            # 检查推荐模型是否存在
            model_path = 'ai/models/ml_models/recommendation_model.pkl'
            if not os.path.exists(model_path):
                # 如果模型不存在，训练模型
                AIRecommendationService.train_recommendation_model()
            
            # 加载模型
            if os.path.exists(model_path):
                model = joblib.load(model_path)
            else:
                # 如果无法加载模型，回退到混合推荐
                return AIRecommendationService.ml_hybrid_recommendations(user_id, count)
            
            # 获取用户提交记录
            submissions = Submission.objects.filter(user_id=user_id).select_related('problem')
            solved_problem_ids = set(sub.problem.problem.id for sub in submissions if sub.result == 0)
            
            # 获取所有可见题目
            all_problems = Problem.objects.filter(visible=True)
            
            # 为每个题目计算推荐分数
            problem_scores = []
            for problem in all_problems:
                # 跳过已解决的题目
                if problem.id in solved_problem_ids:
                    continue
                
                # 提取特征
                features = AIRecommendationService._extract_user_problem_features(user_id, problem.id)
                
                # 使用模型预测
                import numpy as np
                try:
                    score = model.predict_proba([features])[0][1]  # 获取正类概率
                except Exception as e:
                    logger.error(f"Error predicting for user {user_id}, problem {problem.id}: {str(e)}")
                    # 如果预测失败，使用简单的启发式方法
                    user_features = AIRecommendationService._build_user_features(user_id)
                    problem_features = AIRecommendationService._build_problem_features(problem)
                    similarity = AIRecommendationService._calculate_feature_similarity(user_features, problem_features)
                    score = similarity
                
                problem_scores.append((problem.id, score, "基于机器学习推荐"))
            
            # 按分数排序并返回前count个
            problem_scores.sort(key=lambda x: x[1], reverse=True)
            return problem_scores[:count]
            
        except Exception as e:
            logger.error(f"ML enhanced recommendation failed: {str(e)}")
            # 回退到混合推荐
            return AIRecommendationService.ml_hybrid_recommendations(user_id, count)

    @staticmethod
    def _train_dl_recommendation_model():
        """
        训练深度学习推荐模型
        """
        try:
            # 准备训练数据
            # 这里需要构建用户-题目交互数据
            user_features = []
            problem_features = []
            labels = []  # 1表示解决，0表示未解决或失败
            
            # 获取所有提交记录
            submissions = Submission.objects.select_related('user', 'problem')
            
            for submission in submissions:
                user_id = submission.user_id
                problem_id = submission.problem_id
                
                # 提取用户特征
                user_feature = AIProgrammingAbilityService._extract_ml_features(user_id)
                
                # 提取题目特征
                problem_feature = AIRecommendationService._extract_problem_features(problem_id)
                
                # 标签：0表示通过，1表示未通过
                label = 1 if submission.result == 0 else 0
                
                user_features.append(user_feature)
                problem_features.append(problem_feature)
                labels.append(label)
            
            if len(user_features) < 20:
                return None
            
            # 训练模型
            recommender = DeepLearningRecommender()
            recommender.train(user_features, problem_features, labels, epochs=50)
            
            return recommender
            
        except Exception as e:
            logger.error(f"Error training deep learning recommendation model: {str(e)}")
            return None
    @staticmethod
    def _extract_problem_features(problem_id):
        """
        提取题目特征向量
        """
        try:
            problem = Problem.objects.get(id=problem_id)
            
            # 题目难度特征
            difficulty_map = {'Low': [1, 0, 0], 'Mid': [0, 1, 0], 'High': [0, 0, 1]}
            difficulty_features = difficulty_map.get(problem.difficulty, [0, 0, 1])
            
            # 通过率特征
            acceptance_rate = problem.accepted_number / problem.submission_number if problem.submission_number > 0 else 0
            
            # 标签特征（简化为标签数量）
            tag_count = problem.tags.count()
            
            # 组合特征
            features = difficulty_features + [acceptance_rate, tag_count, problem.submission_number]
            
            return features
        except Exception as e:
            logger.error(f"Error extracting problem features for problem {problem_id}: {str(e)}")
            return [0, 0, 1, 0, 0, 0]  
    @staticmethod
    def deep_learning_recommendations(user_id, count=10):
        """
        基于深度学习的题目推荐
        """
        try:
            # 检查模型是否存在
            model_path = 'ai/models/deep_learning/recommendation_model.pth'
            import os
            if not os.path.exists(model_path):
                # 训练模型
                recommender = AIRecommendationService._train_dl_recommendation_model()
                if recommender is None:
                    # 回退到原有方法
                    return AIRecommendationService.hybrid_recommendations(user_id=user_id, count=count)
            else:
                # 加载模型
                recommender = DeepLearningRecommender(model_path)
            
            # 获取用户特征
            user_features = AIProgrammingAbilityService._extract_ml_features(user_id)
            
            # 获取用户已解决的题目
            solved_problems = set(
                Submission.objects.filter(user_id=user_id, result=0)
                .values_list('problem_id', flat=True)
            )
            
            # 获取所有可见题目
            all_problems = Problem.objects.filter(visible=True)
            
            # 计算每个题目的推荐分数
            problem_scores = []
            for problem in all_problems:
                if problem.id in solved_problems:
                    continue  # 跳过已解决的题目
                
                # 提取题目特征
                problem_features = AIRecommendationService._extract_problem_features(problem.id)
                
                # 预测分数
                score = recommender.predict_score(user_features, problem_features)[0][0]
                
                problem_scores.append((problem.id, float(score), "深度学习推荐"))
            
            # 按分数排序
            problem_scores.sort(key=lambda x: x[1], reverse=True)
            return problem_scores[:count]
            
        except Exception as e:
            logger.error(f"Deep learning recommendation failed: {str(e)}")
            # 出错时回退到混合推荐
            return AIRecommendationService.hybrid_recommendations(user_id=user_id, count=count)
    
    @staticmethod
    def recommend_problems(user_id, count=10, algorithm='hybrid'):
        """推荐题目的对外接口"""
        try:
            if algorithm == 'collaborative':
                recommendations = AIRecommendationService.collaborative_filtering_recommendations(
                    user_id=user_id, count=count)
            elif algorithm == 'content':
                recommendations = AIRecommendationService.content_based_recommendations(
                    user_id=user_id, count=count)
            elif algorithm == 'deep_learning':
                recommendations = AIRecommendationService.deep_learning_recommendations(
                    user_id=user_id, count=count)
            elif algorithm == 'ml_enhanced':
                # 使用机器学习增强的推荐算法
                recommendations = AIRecommendationService.ml_enhanced_recommendations(
                    user_id=user_id, count=count)
            else:  # 默认使用混合推荐
                recommendations = AIRecommendationService.hybrid_recommendations(
                    user_id=user_id, count=count)
            
            return recommendations
        except Exception as e:
            logger.error(f"Recommendation failed with algorithm {algorithm}: {str(e)}")
            # 出错时回退到热门题目推荐
            popular_problems = Problem.objects.filter(visible=True).order_by("-accepted_number")[:count]
            return [(problem.id, 1.0, "热门题目推荐") for problem in popular_problems]
        
    @staticmethod
    def recommend_next_problem(user_id, problem_id, submission_result):
        """推荐下一题"""
        try:
            # 根据用户提交结果调整推荐策略
            if submission_result == "Accepted":
                recommendations = AIRecommendationService.hybrid_recommendations(user_id=user_id, count=5)
            else:
                recommendations = AIRecommendationService.content_based_recommendations(user_id=user_id, count=5)
            
            if recommendations:
                # 返回第一个推荐结果
                return recommendations[:3]
            else:
                popular_problems = Problem.objects.filter(visible=True).order_by("-accepted_number")[:1]
                if popular_problems:
                    return (popular_problems[0].id, 1.0, "热门题目推荐")
                else:
                    return (None, None, None)
        except Exception as e:
            logger.error(f"Recommend next problem failed: {str(e)}")
            popular_problems = Problem.objects.filter(visible=True).order_by("-accepted_number")[:1]
            if popular_problems:
                return (popular_problems[0].id, 1.0, "热门题目推荐")
            else:
                return (None, None, None)
    @staticmethod
    def generate_code_explanation(code,language):
        try:
            cached_explanation = AIRecommendationService.get_cached_explanation(code, language)
            if cached_explanation:
                logger.info(f"Returning cached explanation for code hash")
                return cached_explanation

            # 为不同编程语言定制提示
            language_prompts = {
                "C++": "C++",
                "C": "C",
                "Python2": "Python",
                "Python3": "Python",
                "Java": "Java",
                "Go": "Go"
            }
            
            display_language = language_prompts.get(language, language)
            
            prompt = f"""
                            请用中文详细解释以下{display_language}代码的功能和逻辑:

                            要求:
                            1. 逐行或逐段解释代码的作用
                            2. 解释关键算法和数据结构
                            3. 指出重要的变量和函数的作用
                            4. 分析代码的时间和空间复杂度
                            5. 如果有优化建议，请提供

                            代码:
                            {code}


                            解释:
                            """.strip()
            messages = [{"role": "user", "content": prompt}]
            
            ai_model = AIService.get_active_ai_model()
            if not ai_model:
                raise Exception("No active AI model found")
            explanation = AIService.call_ai_model(messages, ai_model)
            AIRecommendationService.cache_explanation(code, language, explanation)
            return explanation
        except Exception as e:
            logger.error(f"Error in generate_code_explanation: {str(e)}")
            raise Exception(f"Failed to generate code explanation: {str(e)}")
        

    @staticmethod
    def deep_learning_recommendations(user_id, count=10):
        """
        基于用户行为模式的深度学习推荐算法
        使用简单的神经网络思想进行推荐
        """
        try:
            from sklearn.preprocessing import StandardScaler
            import numpy as np
            
            # 获取用户历史行为数据
            submissions = Submission.objects.filter(user_id=user_id).select_related('problem')
            
            if not submissions:
                # 如果没有提交记录，返回热门题目
                popular_problems = Problem.objects.filter(visible=True).order_by("-accepted_number")[:count]
                return [(problem.id, 0.5, "热门题目推荐") for problem in popular_problems]
            
            # 构建用户特征向量
            user_features = AIRecommendationService._build_user_features(user_id)
            
            # 获取所有可见题目
            all_problems = Problem.objects.filter(visible=True)
            
            # 为每个题目计算匹配分数
            problem_scores = []
            for problem in all_problems:
                # 检查用户是否已解决该题目
                solved = submissions.filter(problem_id=problem.id, result=0).exists()
                if solved:
                    continue  # 跳过已解决的题目
                
                # 构建题目特征向量
                problem_features = AIRecommendationService._build_problem_features(problem)
                
                # 计算用户与题目的匹配分数（简化版余弦相似度）
                similarity = AIRecommendationService._calculate_feature_similarity(user_features, problem_features)
                
                # 考虑题目的热度因素
                popularity_factor = min(1.0, problem.accepted_number / 1000.0) if problem.accepted_number else 0.1
                
                # 综合分数
                final_score = similarity * (0.7 + 0.3 * popularity_factor)
                
                problem_scores.append((problem.id, final_score, "基于深度学习推荐"))
            
            # 按分数排序并返回前count个
            problem_scores.sort(key=lambda x: x[1], reverse=True)
            return problem_scores[:count]
            
        except Exception as e:
            logger.error(f"Deep learning recommendation failed: {str(e)}")
            # 出错时回退到混合推荐
            return AIRecommendationService.hybrid_recommendations(user_id=user_id, count=count)
        
    @staticmethod
    def _build_user_features(user_id):
        """
        构建用户特征向量
        """
        try:
            # 获取用户提交记录
            submissions = Submission.objects.filter(user_id=user_id).select_related('problem')
            
            # 基础特征
            total_submissions = submissions.count()
            accepted_submissions = submissions.filter(result=0).count()
            acceptance_rate = accepted_submissions / total_submissions if total_submissions > 0 else 0
            
            # 难度特征
            high_difficulty_count = submissions.filter(problem__difficulty='High', result=0).count()
            mid_difficulty_count = submissions.filter(problem__difficulty='Mid', result=0).count()
            low_difficulty_count = submissions.filter(problem__difficulty='Low', result=0).count()
            
            # 标签特征（简化处理）
            tag_stats = defaultdict(int)
            for submission in submissions.filter(result=0):
                for tag in submission.problem.tags.all():
                    tag_stats[tag.name] += 1
            
            # 构建特征向量
            features = {
                'total_submissions': total_submissions,
                'acceptance_rate': acceptance_rate,
                'high_difficulty_count': high_difficulty_count,
                'mid_difficulty_count': mid_difficulty_count,
                'low_difficulty_count': low_difficulty_count,
                'top_tags': dict(sorted(tag_stats.items(), key=lambda x: x[1], reverse=True)[:5])
            }
            
            return features
        except Exception as e:
            logger.error(f"Failed to build user features: {str(e)}")
            return {}
        
    @staticmethod
    def _build_problem_features(problem):
        """
        构建题目特征向量
        """
        try:
            # 标签特征
            tags = [tag.name for tag in problem.tags.all()]
            
            # 难度映射
            difficulty_map = {'Low': 1, 'Mid': 2, 'High': 3}
            difficulty_score = difficulty_map.get(problem.difficulty, 2)
            
            # 热度特征
            acceptance_rate = problem.accepted_number / problem.submission_number if problem.submission_number > 0 else 0
            
            # 构建特征向量
            features = {
                'difficulty': difficulty_score,
                'tags': tags,
                'acceptance_rate': acceptance_rate,
                'submission_number': problem.submission_number,
                'accepted_number': problem.accepted_number
            }
            
            return features
        except Exception as e:
            logger.error(f"Failed to build problem features: {str(e)}")
            return {}
        
    @staticmethod
    def _calculate_feature_similarity(user_features, problem_features):
        """
        计算用户和题目的特征相似度
        """
        try:
            # 简化的相似度计算
            # 考虑接受率相似性
            user_acc_rate = user_features.get('acceptance_rate', 0)
            problem_acc_rate = problem_features.get('acceptance_rate', 0)
            acc_rate_similarity = 1 - abs(user_acc_rate - problem_acc_rate)
            
            # 考虑标签匹配度
            user_tags = set(user_features.get('top_tags', {}).keys())
            problem_tags = set(problem_features.get('tags', []))
            tag_overlap = len(user_tags.intersection(problem_tags))
            tag_union = len(user_tags.union(problem_tags))
            tag_similarity = tag_overlap / tag_union if tag_union > 0 else 0
            
            # 综合相似度
            similarity = 0.6 * acc_rate_similarity + 0.4 * tag_similarity
            return max(0.1, similarity)  # 确保最小相似度
            
        except Exception as e:
            logger.error(f"Failed to calculate feature similarity: {str(e)}")
            return 0.1


class AILearningPathService:
    @staticmethod
    def generate_learning_path(user_id, goal="general", current_level=None):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise Exception("User not found")
        
        # 获取用户历史提交记录
        submissions = Submission.objects.filter(user_id=user_id).select_related('problem')
        
        # 分析用户当前水平
        if not current_level:
            current_level = AILearningPathService._assess_user_level(submissions)
        
        # 获取用户知识点掌握情况
        knowledge_states = KnowledgePointService.get_user_knowledge_state(user_id)
        
        # 根据目标确定学习路径内容
        path_content = AILearningPathService._generate_path_content(goal, current_level)
        
        # 构建系统提示
        system_prompt = {
            "role": "system",
            "content": "你是一个专业的编程教育专家，擅长为学生制定个性化的学习路径。"
        }
        
        # 构建用户提示
        user_prompt = {
            "role": "user",
            "content": f"""
            请为一位{current_level}水平的编程学习者生成一个个性化的学习路径，目标是{goal}。
            
            学习者信息:
            - 用户ID: {user_id}
            - 当前水平: {current_level}
            - 学习目标: {goal}
            - 历史提交题目数: {len(submissions)}
            
            学习者知识点掌握情况:
            {', '.join([f"{name}(掌握程度:{state.proficiency_level})" for name, state in knowledge_states.items()][:10])}
            
            请生成一个包含以下内容的学习路径:
            1. 路径标题和简要描述
            2. 预计完成时间
            3. 按顺序排列的学习节点，每个节点包含:
               - 类型 (concept, problem, project)
               - 标题
               - 详细描述
               - 关联内容ID（题目ID等）
               - 预计完成时间（分钟）
               - 前置知识点（数组）
               - 关联的知识点名称（如果有）
               
            学习路径内容参考:
            {path_content}
            
            请以JSON格式返回结果，结构如下:
            {{
                "title": "路径标题",
                "description": "路径描述",
                "estimated_duration": 20,
                "nodes": [
                    {{
                        "node_type": "problem",
                        "title": "节点标题",
                        "description": "节点描述",
                        "content_id": 123,
                        "estimated_time": 30,
                        "prerequisites": ["数组", "循环"],
                        "knowledge_point": "循环结构"  // 新增字段
                    }}
                ]
            }}
            
            重要：
            1. 只返回JSON，不要有任何其他内容
            2. content_id如果是题目，使用已存在的题目ID
            3. 确保JSON格式正确，可以直接解析
            4. 根据用户知识点掌握情况，针对性地推荐需要加强的知识点
            5. 优先推荐掌握程度低于0.7的知识点相关学习内容
            """
        }
        
        messages = [system_prompt, user_prompt]
        
        ai_model = AIService.get_active_ai_model()
        if not ai_model:
            raise Exception("No active AI model found")
        
        try:
            response = AIService.call_ai_model(messages, ai_model)
            # 清理响应内容，确保是有效的JSON
            import json
            import re
            
            # 尝试提取JSON内容
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                response = json_match.group()
            
            path_data = json.loads(response)
            return path_data
        except Exception as e:
            logger.error(f"Failed to generate learning path: {str(e)}")
            logger.error(f"AI response: {response}")
            raise Exception(f"Failed to generate learning path: {str(e)}")
    @staticmethod
    def _assess_user_level(submissions):
        """
        评估用户水平
        """
        if not submissions:
            return "beginner"
        
        # 计算通过率
        accepted_count = sum(1 for s in submissions if s.result == 0)
        total_count = len(submissions)
        acceptance_rate = accepted_count / total_count if total_count > 0 else 0
        
        # 根据通过率和题目难度评估水平
        if acceptance_rate < 0.3 or total_count < 5:
            return "beginner"
        elif acceptance_rate < 0.7 or total_count < 20:
            return "intermediate"
        else:
            return "advanced"
    
    @staticmethod
    def _generate_path_content(goal, level):
        content_map = {
            "interview": {
                "beginner": "基础语法、数组、字符串、链表、栈、队列等数据结构，以及简单算法如排序和查找",
                "intermediate": "树、图、排序算法、动态规划基础、哈希表、递归等中等难度算法",
                "advanced": "高级算法、系统设计、复杂动态规划、图论算法、贪心算法等"
            },
            "algorithm": {
                "beginner": "基础数据结构如数组、链表、栈、队列，以及简单算法",
                "intermediate": "搜索算法(BFS/DFS)、图论基础、分治法、回溯算法",
                "advanced": "高级图论、数论、计算几何、字符串算法、线段树等"
            },
            "data_science": {
                "beginner": "Python基础、NumPy、Pandas入门、数据可视化基础",
                "intermediate": "数据可视化、统计分析、机器学习基础、Scikit-learn使用",
                "advanced": "深度学习、自然语言处理、大数据处理、模型优化等"
            },
            "general": {
                "beginner": "编程基础、基本数据结构如数组、链表、栈、队列",
                "intermediate": "算法设计、面向对象编程、中等难度数据结构如树、图",
                "advanced": "设计模式、系统架构、性能优化、高级算法等"
            }
        }
        
        return content_map.get(goal, content_map["general"]).get(level, "编程基础")
    @staticmethod
    def save_learning_path(user_id, path_data):
        """
        保存学习路径到数据库
        """
        try:
            with transaction.atomic():
                # 创建学习路径
                learning_path = AIUserLearningPath.objects.create(
                    user_id=user_id,
                    title=path_data["title"],
                    description=path_data["description"],
                    estimated_duration=path_data.get("estimated_duration", 0),
                    path_data=path_data
                )

                # 创建学习路径节点
                nodes_data = path_data.get("nodes", [])
                for i, node_data in enumerate(nodes_data):
                    # 处理content_id可能为空或为字符串的情况
                    content_id = node_data.get("content_id")
                    if content_id is None:
                        # 如果content_id为空，根据节点类型设置默认值
                        node_type = node_data.get("node_type", "")
                        if node_type == "problem":
                            # 对于题目类型节点，设置默认题目ID（例如1）
                            content_id = 1
                        else:
                            # 对于其他类型节点，设置为0
                            content_id = 0
                    else:
                        # 确保content_id是整数
                        try:
                            content_id = int(content_id)
                        except (ValueError, TypeError):
                            # 如果转换失败，使用默认值
                            node_type = node_data.get("node_type", "")
                            if node_type == "problem":
                                content_id = 1
                            else:
                                content_id = 0
                    
                    # 处理知识点关联
                    knowledge_point = None
                    knowledge_point_name = node_data.get("knowledge_point")
                    if knowledge_point_name:
                        try:
                            knowledge_point = KnowledgePoint.objects.get(name=knowledge_point_name)
                        except KnowledgePoint.DoesNotExist:
                            # 如果知识点不存在，创建一个新的
                            knowledge_point = KnowledgePoint.objects.create(
                                name=knowledge_point_name,
                                description=f"与{knowledge_point_name}相关的知识点",
                                category="算法与数据结构",
                                difficulty=3
                            )
                    
                    AIUserLearningPathNode.objects.create(
                        learning_path=learning_path,
                        node_type=node_data.get("node_type", "concept"),
                        title=node_data.get("title", "未命名节点"),
                        description=node_data.get("description", ""),
                        content_id=content_id,
                        order=i,
                        estimated_time=node_data.get("estimated_time", 30),
                        prerequisites=node_data.get("prerequisites", []),
                        knowledge_point=knowledge_point  
                    )
                
                return learning_path
        except Exception as e:
            logger.error(f"Failed to save learning path: {str(e)}")
            raise Exception(f"Failed to save learning path: {str(e)}")
    @staticmethod
    def get_user_learning_paths(user_id):
        return AIUserLearningPath.objects.filter(user_id=user_id, is_active=True).order_by('-create_time')
    
    @staticmethod
    def get_learning_path_detail(path_id, user_id):
        try:
            path = AIUserLearningPath.objects.get(id=path_id, user_id=user_id)
            nodes = AIUserLearningPathNode.objects.filter(learning_path=path).order_by('order')
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Retrieved learning path {path_id} with {nodes.count()} nodes")
            return path, nodes
        except AIUserLearningPath.DoesNotExist:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Learning path {path_id} not found for user {user_id}")
            raise Exception("Learning path not found")
    
    @staticmethod
    def update_node_status(node_id, user_id, status):
        try:
            node = AIUserLearningPathNode.objects.filter(
                id=node_id,
                learning_path__user_id=user_id
            ).first()
            
            if not node:
                raise Exception("Node not found")
            
            node.status = status
            node.save()
            return node
        except Exception as e:
            logger.error(f"Failed to update node status: {str(e)}")
            raise Exception(f"Failed to update node status: {str(e)}")


class AICodeDiagnosisService:
    @staticmethod
    def diagnose_submission(submission):
        try:
            # 获取问题信息
            problem = submission.problem
            
            # 构建系统提示
            system_prompt = {
                "role": "system",
                "content": "你是一个专业的编程导师，擅长分析代码错误并提供修复建议。"
            }
            
            # 根据提交结果构建用户提示
            result_description = ""
            if submission.result == 1:  # Wrong Answer
                result_description = "输出结果与预期不符"
            elif submission.result == 2:  # Time Limit Exceeded
                result_description = "程序运行时间超过了限制"
            elif submission.result == 3:  # Memory Limit Exceeded
                result_description = "程序使用的内存超过了限制"
            elif submission.result == 4:  # Runtime Error
                result_description = "程序运行时出现错误"
            elif submission.result == 5:  # Compile Error
                result_description = "代码编译失败"
            else:
                result_description = "代码存在其他问题"
            
            user_prompt = {
                "role": "user",
                "content": f"""
                请分析以下代码中的问题并提供修复建议：
                
                题目: {problem.title}
                题目描述: {problem.description}
                
                提交结果: {result_description}
                
                编程语言: {submission.language}
                代码:
                {submission.code}
                
                请提供以下信息：
                1. 错误分析：详细解释代码中可能存在的问题
                2. 修复建议：具体的修改建议
                3. 示例代码：修改后的代码示例
                4. 学习建议：相关的知识点或技巧
                
                请以以下JSON格式返回结果：
                {{
                    "error_analysis": "错误分析内容",
                    "fix_suggestions": "修复建议内容",
                    "example_code": "修改后的代码示例",
                    "learning_tips": "学习建议内容"
                }}
                
                只返回JSON，不要包含其他内容。
                """
            }
            
            messages = [system_prompt, user_prompt]
            
            # 获取激活的AI模型
            ai_model = AIService.get_active_ai_model()
            if not ai_model:
                raise Exception("No active AI model found")
            
            # 调用AI模型
            response = AIService.call_ai_model(messages, ai_model)
            
            # 解析JSON响应
            import json
            import re
            
            # 尝试提取JSON内容
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                response = json_match.group()
            
            diagnosis_data = json.loads(response)
            return diagnosis_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            logger.error(f"AI response: {response}")
            # 返回一个默认的诊断结果
            return {
                "error_analysis": "无法分析代码错误。",
                "fix_suggestions": "请稍后重试或联系管理员。",
                "example_code": "# 示例代码暂不可用",
                "learning_tips": "尝试重新提交以获取诊断信息。"
            }
        except Exception as e:
            logger.error(f"Failed to diagnose submission: {str(e)}")
            raise Exception(f"Failed to diagnose submission: {str(e)}")
        
    @staticmethod
    def diagnose_code_in_real_time(code, language, problem_id=None):
        """
        实时诊断代码中的潜在问题
        """
        try:
            # 构建提示语
            problem_context = ""
            if problem_id:
                try:
                    problem = Problem.objects.get(id=problem_id)
                    problem_context = f"题目: {problem.title}\n题目描述: {problem.description}\n\n"
                except Problem.DoesNotExist:
                    pass

            prompt = f"""
{problem_context}请分析以下{language}代码中的潜在问题：

代码:
{code}

请提供以下信息：
1. 语法错误
2. 逻辑错误
3. 性能问题
4. 最佳实践建议

请以以下JSON格式返回结果：
{{
    "syntax_errors": ["语法错误1", "语法错误2"],
    "logic_errors": ["逻辑错误1", "逻辑错误2"],
    "performance_issues": ["性能问题1", "性能问题2"],
    "best_practices": ["最佳实践建议1", "最佳实践建议2"]
}}
""".strip()

            messages = [
                {"role": "system", "content": "你是一个专业的编程导师，擅长分析代码中的潜在问题。"},
                {"role": "user", "content": prompt}
            ]
            
            ai_model = AIService.get_active_ai_model()
            if not ai_model:
                raise Exception("No active AI model found")
            
            response = AIService.call_ai_model(messages, ai_model)
            
            # 解析JSON响应
            import json
            import re
            
            # 尝试提取JSON内容
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                response = json_match.group()
            
            diagnosis_data = json.loads(response)
            return diagnosis_data
            
        except Exception as e:
            logger.error(f"Failed to diagnose code in real-time: {str(e)}")
            # 返回默认诊断
            return {
                "syntax_errors": [],
                "logic_errors": [],
                "performance_issues": [],
                "best_practices": []
            }

class KnowledgePointService:
    @staticmethod
    def create_knowledge_points_from_tags():
        """
        从题目标签创建知识点
        """
        from problem.models import ProblemTag
        tags = ProblemTag.objects.all()
        
        for tag in tags:
            KnowledgePoint.objects.get_or_create(
                name=tag.name,
                defaults={
                    'description': f'与{tag.name}相关的知识点',
                    'category': '算法与数据结构',
                    'difficulty': 3
                }
            )
    
    @staticmethod
    def get_user_knowledge_state(user_id):
        """
        获取用户知识点掌握状态
        """
        states = AIUserKnowledgeState.objects.filter(user_id=user_id)
        return {state.knowledge_point.name: state for state in states}
    
    @staticmethod
    def update_user_knowledge_state(user_id, problem_id, is_correct):
        """
        根据用户解答题目情况更新知识点掌握状态
        """
        try:
            # 获取题目相关的知识点
            problem = Problem.objects.get(id=problem_id)
            tags = problem.tags.all()
            
            # 获取或创建对应的知识点
            knowledge_points = []
            for tag in tags:
                kp, created = KnowledgePoint.objects.get_or_create(
                    name=tag.name,
                    defaults={
                        'description': f'与{tag.name}相关的知识点',
                        'category': '算法与数据结构',
                        'difficulty': 3
                    }
                )
                knowledge_points.append(kp)
            
            # 更新用户知识点掌握状态
            for kp in knowledge_points:
                user_state, created = AIUserKnowledgeState.objects.get_or_create(
                    user_id=user_id,
                    knowledge_point=kp,
                    defaults={
                        'proficiency_level': 0.0,
                        'correct_attempts': 0,
                        'total_attempts': 0
                    }
                )
                user_state.update_proficiency(is_correct)
                
        except Exception as e:
            logger.error(f"Failed to update user knowledge state: {str(e)}")
    
    @staticmethod
    def get_knowledge_recommendations(user_id, count=5):
        """
        考虑用户反馈和行为数据优化推荐 引入权重
        """
        try:
            # 获取用户知识点状态，按掌握程度排序（掌握程度低的排在前面）
            user_states = AIUserKnowledgeState.objects.filter(
                user_id=user_id
            ).select_related('knowledge_point').order_by('proficiency_level')[:count*2]  
            
            # 获取用户对推荐的反馈数据
            feedback_weights = KnowledgePointService._get_user_feedback_weights(user_id)
            
            recommendations = []
            for state in user_states:
                # 计算推荐分数（考虑掌握程度和最近更新时间）
                proficiency = state.proficiency_level
                from django.utils import timezone
                days_since_update = (timezone.now() - state.last_updated).days if state.last_updated else 0

                base_score = (1 - proficiency) + min(days_since_update / 30.0, 1.0) * 0.3
                
                # 获取该知识点的反馈权重
                feedback_weight = feedback_weights.get(state.knowledge_point.name, 1.0)
                
                # 获取知识点的推荐权重
                knowledge_point_weight = state.knowledge_point.weight
                
                # 综合分数 = 基础分数 * 反馈权重 * 知识点权重
                final_score = base_score * feedback_weight * knowledge_point_weight
                
                recommendations.append({
                    'knowledge_point': state.knowledge_point.name,
                    'proficiency_level': state.proficiency_level,
                    'score': final_score,
                    'base_score': base_score,
                    'feedback_weight': feedback_weight,
                    'knowledge_point_weight': knowledge_point_weight,
                    'correct_attempts': state.correct_attempts,
                    'total_attempts': state.total_attempts,
                    'recommended_problems': KnowledgePointService._get_problems_for_knowledge_point(
                        state.knowledge_point, user_id
                    )
                })
            
            # 按分数排序并返回前count个
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            return recommendations[:count]
        except Exception as e:
            logger.error(f"Failed to get knowledge recommendations: {str(e)}")
            return []

    @staticmethod
    def _get_user_feedback_weights(user_id):
        """
        根据用户反馈计算知识点推荐权重
        正面反馈增加权重，负面反馈降低权重
        """
        try:
            from .models import AIRecommendationFeedback
            
            # 获取用户对推荐的反馈
            feedbacks = AIRecommendationFeedback.objects.filter(
                user_id=user_id,
                recommendation__user_id=user_id
            ).select_related('recommendation')
            
            # 统计每个知识点的反馈情况
            knowledge_point_feedback = defaultdict(list)
            for feedback in feedbacks:
                kp_name = feedback.recommendation.problem.tags.first().name if feedback.recommendation.problem.tags.exists() else None
                if kp_name:
                    # 正面反馈(accepted=True, solved=True)权重>1，负面反馈权重<1
                    if feedback.accepted and feedback.solved:
                        knowledge_point_feedback[kp_name].append(1.5)  # 强烈推荐
                    elif feedback.accepted:
                        knowledge_point_feedback[kp_name].append(1.2)  # 一般推荐
                    else:
                        knowledge_point_feedback[kp_name].append(0.7)  # 不推荐
                        
            # 计算每个知识点的平均权重
            feedback_weights = {}
            for kp_name, weights in knowledge_point_feedback.items():
                feedback_weights[kp_name] = sum(weights) / len(weights)
                
            return feedback_weights
        except Exception as e:
            logger.error(f"Failed to get user feedback weights: {str(e)}")
            return {}

    @staticmethod
    def _get_problems_for_knowledge_point(knowledge_point, user_id):
        """
        获取针对特定知识点的推荐题目
        """
        try:
            # 获取与知识点相关的题目
            problems = knowledge_point.related_problems.filter(visible=True)[:3]
            if not problems:
                # 如果没有直接关联的题目，则根据标签查找
                from problem.models import Problem
                problems = Problem.objects.filter(
                    tags__name=knowledge_point.name,
                    visible=True
                )[:3]
            
            return [{'id': p.id, 'title': p.title} for p in problems]
        except Exception as e:
            logger.error(f"Failed to get problems for knowledge point: {str(e)}")
            return []
        

    @staticmethod
    def create_knowledge_points_from_tags_detailed():
        """
        从题目标签创建知识点（增强版）
        """
        from problem.models import ProblemTag, Problem
        tags = ProblemTag.objects.all()
        
        created_count = 0
        updated_count = 0
        
        for tag in tags:
            # 创建或更新知识点
            kp, created = KnowledgePoint.objects.get_or_create(
                name=tag.name,
                defaults={
                    'description': f'与{tag.name}相关的知识点',
                    'category': '算法与数据结构',
                    'difficulty': 3
                }
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1
            
            # 关联相关题目
            problems = Problem.objects.filter(tags=tag, visible=True)
            kp.related_problems.set(problems)
        
        return {
            'created': created_count,
            'updated': updated_count,
            'total_tags': tags.count()
        }
    
    @staticmethod
    def build_knowledge_point_dependencies():
        """
        建立知识点之间的依赖关系
        """
        # 定义知识点依赖关系
        dependencies = {
            '数组': [],
            '链表': ['数组'],
            '栈': ['数组'],
            '队列': ['数组'],
            '哈希表': ['数组'],
            '字符串': ['数组'],
            '树': ['链表'],
            '二叉树': ['树'],
            '二叉搜索树': ['二叉树'],
            '堆': ['树'],
            '图': ['树'],
            '排序': ['数组'],
            '查找': ['数组'],
            '递归': ['函数'],
            '分治': ['递归'],
            '动态规划': ['递归', '数组'],
            '贪心算法': ['排序'],
            '回溯算法': ['递归'],
            '深度优先搜索': ['图', '递归'],
            '广度优先搜索': ['图', '队列']
        }
        
        updated_count = 0
        
        for kp_name, parent_names in dependencies.items():
            try:
                kp = KnowledgePoint.objects.get(name=kp_name)
                parent_points = KnowledgePoint.objects.filter(name__in=parent_names)
                kp.parent_points.set(parent_points)
                updated_count += 1
            except KnowledgePoint.DoesNotExist:
                # 知识点不存在，跳过
                continue
        
        return {
            'updated_knowledge_points': updated_count,
            'total_dependencies': len(dependencies)
        }
    
    @staticmethod
    def associate_problems_with_knowledge_points():
        """
        关联所有题目与知识点
        """
        from problem.models import Problem, ProblemTag
        from .models import KnowledgePoint
        
        # 获取所有题目
        problems = Problem.objects.filter(visible=True)
        association_count = 0
        
        for problem in problems:
            # 获取题目的标签
            tags = problem.tags.all()
            tag_names = [tag.name for tag in tags]
            
            # 查找对应的知识点
            knowledge_points = KnowledgePoint.objects.filter(name__in=tag_names)
            
            # 建立关联
            problem.knowledgepoint_set.set(knowledge_points)
            association_count += 1
            
        return {
            'associated_problems': association_count,
            'total_problems': problems.count()
        }
    @staticmethod
    def process_recommendation_feedback(user_id, recommendation_id, accepted, solved, feedback_text=""):
        """
        处理用户对推荐的反馈
        """
        try:
            from .models import AIRecommendation, AIRecommendationFeedback
            
            # 创建反馈记录
            recommendation = AIRecommendation.objects.get(id=recommendation_id)
            feedback = AIRecommendationFeedback.objects.create(
                user_id=user_id,
                problem=recommendation.problem,
                recommendation=recommendation,
                accepted=accepted,
                solved=solved,
                feedback=feedback_text
            )
            
            # 根据反馈更新推荐模型（简化版在线学习）
            if accepted and solved:
                # 正面反馈：增加相关知识点的推荐权重
                KnowledgePointService._update_knowledge_point_weights(
                    user_id, recommendation.problem, 1.2)
            elif not accepted:
                # 负面反馈：减少相关知识点的推荐权重
                KnowledgePointService._update_knowledge_point_weights(
                    user_id, recommendation.problem, 0.8)
                
            return feedback
        except Exception as e:
            logger.error(f"Failed to process recommendation feedback: {str(e)}")
            raise
    @staticmethod
    def _update_knowledge_point_weights(user_id, problem, weight_factor):
        """
        根据反馈更新知识点权重
        使用指数移动平均方法更新权重，使推荐系统能够适应用户偏好变化
        """
        try:
            # 获取与题目关联的所有知识点
            knowledge_points = problem.knowledgepoint_set.all()
            for kp in knowledge_points:
                # 获取用户对该知识点的掌握状态
                try:
                    user_knowledge_state = AIUserKnowledgeState.objects.get(
                        user_id=user_id,
                        knowledge_point=kp
                    )
                    # 基于用户掌握程度调整权重更新因子
                    # 用户掌握程度越高，权重调整幅度应该越小
                    proficiency_factor = 1.0 - user_knowledge_state.proficiency_level
                    
                    # 计算调整后的权重因子
                    adjusted_weight_factor = 1.0 + (weight_factor - 1.0) * proficiency_factor
                    alpha = 0.3  # 学习率
                    new_weight = kp.weight * (1 - alpha) + adjusted_weight_factor * alpha
                    
                    # 确保权重在合理范围内
                    kp.weight = max(0.1, min(10.0, new_weight))
                    kp.save()
                    
                    logger.info(f"Updated knowledge point '{kp.name}' weight from {kp.weight/adjusted_weight_factor:.4f} to {kp.weight:.4f} for user {user_id}")
                except AIUserKnowledgeState.DoesNotExist:
                    alpha = 0.3
                    new_weight = kp.weight * (1 - alpha) + weight_factor * alpha
                    kp.weight = max(0.1, min(10.0, new_weight))
                    kp.save()
                    
                    logger.info(f"Updated knowledge point '{kp.name}' weight from {kp.weight/weight_factor:.4f} to {kp.weight:.4f} for user {user_id}")
                    
        except Exception as e:
            logger.error(f"Failed to update knowledge point weights: {str(e)}")


class AIProblemGenerationService:
    """
    AI驱动的题目生成服务
    """
    
    @staticmethod
    def generate_problem_by_knowledge_point(knowledge_point_name, difficulty="Mid"):
        # 构建提示语
        difficulty_desc = {
            "Low": "简单：适合初学者，主要考察基本语法和简单逻辑",
            "Mid": "中等：适合有一定基础的学习者，需要综合运用多个知识点",
            "High": "困难：适合高级学习者，需要深入理解和创新思维"
        }
        
        prompt = f"""
请根据以下知识点生成一道编程题目：

知识点: {knowledge_point_name}
难度: {difficulty} - {difficulty_desc.get(difficulty, "中等")}

请以JSON格式返回结果，结构如下:
{{
    "title": "题目标题",
    "description": "题目描述，包含问题背景和要求",
    "input_description": "输入描述",
    "output_description": "输出描述",
    "samples": [
        {{
            "input": "样例输入1",
            "output": "样例输出1"
        }},
        {{
            "input": "样例输入2",
            "output": "样例输出2"
        }}
    ],
    "hint": "提示信息（可选）",
    "time_limit": 1000,
    "memory_limit": 256,
    "difficulty": "{difficulty}"
}}

要求：
1. 题目应紧密围绕指定知识点
2. 难度适中，符合指定等级
3. 至少包含2个样例，样例应具有代表性
4. 题目描述清晰，无歧义
5. 只返回JSON，不要有任何其他内容
"""

        messages = [
            {"role": "system", "content": "你是一个专业的编程题目设计师，擅长根据知识点设计合适的编程题目。"},
            {"role": "user", "content": prompt}
        ]
        
        ai_model = AIService.get_active_ai_model()
        if not ai_model:
            raise Exception("No active AI model found")
        
        try:
            response = AIService.call_ai_model(messages, ai_model)
            # 清理响应内容，确保是有效的JSON
            import json
            import re
            
            # 尝试提取JSON内容
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                response = json_match.group()
            
            problem_data = json.loads(response)
            return problem_data
        except Exception as e:
            logger.error(f"Failed to generate problem: {str(e)}")
            logger.error(f"AI response: {response}")
            raise Exception(f"Failed to generate problem: {str(e)}")
        
    @staticmethod
    def validate_and_adjust_problem(problem_data, knowledge_point_name):
        # 确保必要字段存在
        required_fields = ["title", "description", "input_description", "output_description", "samples"]
        for field in required_fields:
            if field not in problem_data:
                problem_data[field] = ""
        
        # 设置默认值
        if "hint" not in problem_data:
            problem_data["hint"] = ""
            
        if "time_limit" not in problem_data:
            problem_data["time_limit"] = 1000
            
        if "memory_limit" not in problem_data:
            problem_data["memory_limit"] = 256
            
        if "difficulty" not in problem_data:
            problem_data["difficulty"] = "Mid"
            
        # 确保samples是列表
        if not isinstance(problem_data["samples"], list):
            problem_data["samples"] = []
            
        # 添加知识点信息到题目描述中
        knowledge_info = f"\n\n**涉及知识点**: {knowledge_point_name}"
        if knowledge_info not in problem_data["description"]:
            problem_data["description"] += knowledge_info
            
        return problem_data
    @staticmethod
    def auto_adjust_difficulty(problem_data, target_difficulty):
        # 这里可以实现更复杂的难度调整逻辑
        problem_data["difficulty"] = target_difficulty
        return problem_data
    
    @staticmethod
    def generate_test_cases(problem_data, test_case_count=5):
        """
        为生成的题目自动生成测试用例
        :param problem_data: 题目数据
        :param test_case_count: 测试用例数量
        :return: 测试用例列表
        """
        prompt = f"""
根据以下题目信息生成{test_case_count}个测试用例：

题目标题: {problem_data.get('title', '未知')}
题目描述: {problem_data.get('description', '无描述')}
输入描述: {problem_data.get('input_description', '无描述')}
输出描述: {problem_data.get('output_description', '无描述')}

请以JSON格式返回结果，结构如下:
[
    {{
        "input": "测试输入1",
        "output": "测试输出1"
    }},
    {{
        "input": "测试输入2", 
        "output": "测试输出2"
    }}
]

要求：
1. 包含边界条件测试用例
2. 包含正常情况测试用例
3. 至少有一个复杂测试用例
4. 确保输出结果正确
5. 只返回JSON数组，不要有任何其他内容
"""

        messages = [
            {"role": "system", "content": "你是一个专业的编程题目测试用例设计专家。"},
            {"role": "user", "content": prompt}
        ]
        
        ai_model = AIService.get_active_ai_model()
        if not ai_model:
            raise Exception("No active AI model found")
        
        try:
            response = AIService.call_ai_model(messages, ai_model)
            # 清理响应内容，确保是有效的JSON
            import json
            import re
            
            # 尝试提取JSON内容
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                response = json_match.group()
            
            test_cases = json.loads(response)
            return test_cases
        except Exception as e:
            logger.error(f"Failed to generate test cases: {str(e)}")
            logger.error(f"AI response: {response}")
            # 返回默认测试用例
            return [
                {"input": "1 2", "output": "3"},
                {"input": "0 0", "output": "0"}
            ]

class AIProgrammingAbilityService:
    """
    编程能力评估服务
    """
    
    @staticmethod
    def initialize_ability_dimensions():
        """
        初始化能力维度定义
        """
        dimensions = [
            {
                'name': 'basic_programming',
                'description': '基础编程能力，包括语法掌握、基本控制结构等',
                'weight': 0.2
            },
            {
                'name': 'data_structures',
                'description': '数据结构运用能力，如数组、链表、树、图等',
                'weight': 0.25
            },
            {
                'name': 'algorithm_design',
                'description': '算法设计与分析能力，包括复杂度分析等',
                'weight': 0.3
            },
            {
                'name': 'problem_solving',
                'description': '问题解决能力，包括问题建模、解决方案设计等',
                'weight': 0.25
            }
        ]
        
        for dim in dimensions:
            AIAbilityDimension.objects.get_or_create(
                name=dim['name'],
                defaults={
                    'description': dim['description'],
                    'weight': dim['weight']
                }
            )
    @staticmethod
    def assess_user_ability(user_id):
        """
        评估用户编程能力
        """
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise Exception("User not found")
        
        # 初始化能力维度
        AIProgrammingAbilityService.initialize_ability_dimensions()
        
        # 计算各个维度得分
        basic_score = AIProgrammingAbilityService._assess_basic_programming(user_id)
        ds_score = AIProgrammingAbilityService._assess_data_structures(user_id)
        algo_score = AIProgrammingAbilityService._assess_algorithm_design(user_id)
        ps_score = AIProgrammingAbilityService._assess_problem_solving(user_id)
        
        # 计算总分
        overall_score = (
            basic_score * 0.2 +
            ds_score * 0.25 +
            algo_score * 0.3 +
            ps_score * 0.25
        )
        
        # 确定能力等级
        level = AIProgrammingAbilityService._determine_level(overall_score)
        
        # 生成分析报告
        analysis_report = AIProgrammingAbilityService._generate_analysis_report(
            user_id, basic_score, ds_score, algo_score, ps_score
        )
        
        # 更新或创建能力评估记录
        ability_record, created = AIProgrammingAbility.objects.update_or_create(
            user=user,
            defaults={
                'overall_score': overall_score,
                'basic_programming_score': basic_score,
                'data_structure_score': ds_score,
                'algorithm_design_score': algo_score,
                'problem_solving_score': ps_score,
                'level': level,
                'analysis_report': analysis_report
            }
        )
        
        # 更新详细能力记录
        AIProgrammingAbilityService._update_ability_details(
            user_id, basic_score, ds_score, algo_score, ps_score
        )
        
        return ability_record
    
    @staticmethod
    def _assess_basic_programming(user_id):
        """
        评估基础编程能力
        基于：简单题目通过率、语法错误频率、提交次数等
        """
        try:
            # 获取用户提交记录
            submissions = Submission.objects.filter(user_id=user_id).select_related('problem')
            
            if not submissions.exists():
                return 0.0
            
            # 筛选出标记为"基础"的题目（可以通过标签或难度判断）
            basic_problems = submissions.filter(
                problem__difficulty='Low'
            )
            
            if not basic_problems.exists():
                return 20.0  # 如果没有做基础题，给一个较低的基础分
            
            total_basic = basic_problems.count()
            passed_basic = basic_problems.filter(result=0).count()  # 假设0表示通过
            
            # 基础通过率
            pass_rate = passed_basic / total_basic if total_basic > 0 else 0
            
            # 计算平均尝试次数（越少越好）
            avg_attempts = total_basic / (passed_basic if passed_basic > 0 else 1)
            attempt_factor = max(0, 1 - (avg_attempts - 1) * 0.1)  # 尝试次数越多，得分越低
            
            # 综合得分 (满分40分)
            score = min(40, pass_rate * 30 + attempt_factor * 10)
            return score
            
        except Exception as e:
            logger.error(f"Error assessing basic programming ability: {str(e)}")
            return 20.0  # 默认分数
        
    @staticmethod
    def _assess_data_structures(user_id):
        """
        评估数据结构能力
        基于：数据结构相关题目的表现、知识点掌握情况等
        """
        try:
            # 定义数据结构相关知识点
            ds_knowledge_points = [
                '数组', '链表', '栈', '队列', '哈希表', 
                '树', '二叉树', '堆', '图'
            ]
            
            # 获取用户在这些知识点上的掌握情况
            knowledge_states = AIUserKnowledgeState.objects.filter(
                user_id=user_id,
                knowledge_point__name__in=ds_knowledge_points
            )
            
            if not knowledge_states.exists():
                return 10.0  # 如果没有相关记录，给较低分数
            
            # 计算平均掌握程度
            total_proficiency = sum(state.proficiency_level for state in knowledge_states)
            avg_proficiency = total_proficiency / knowledge_states.count()
            
            # 获取数据结构相关题目的通过情况
            ds_tags = ProblemTag.objects.filter(name__in=ds_knowledge_points)
            ds_problems = Problem.objects.filter(tags__in=ds_tags).distinct()
            
            submitted_ds_problems = Submission.objects.filter(
                user_id=user_id,
                problem__in=ds_problems
            ).distinct()
            
            passed_ds_problems = submitted_ds_problems.filter(result=0)
            
            # 计算通过率
            ds_pass_rate = (
                passed_ds_problems.count() / submitted_ds_problems.count() 
                if submitted_ds_problems.count() > 0 else 0
            )
            
            # 综合得分 (满分40分)
            # 知识点掌握占60%，通过率占40%
            score = min(40, avg_proficiency * 24 + ds_pass_rate * 16)
            return score
            
        except Exception as e:
            logger.error(f"Error assessing data structures ability: {str(e)}")
            return 15.0  # 默认分数
        
    @staticmethod
    def _assess_algorithm_design(user_id):
        """
        评估算法设计能力
        基于：算法题通过率、时间复杂度优化情况等
        """
        try:
            # 定义算法相关知识点
            algo_knowledge_points = [
                '排序', '查找', '递归', '分治', '动态规划',
                '贪心算法', '回溯算法', '深度优先搜索', '广度优先搜索'
            ]
            
            # 获取用户在这些知识点上的掌握情况
            knowledge_states = AIUserKnowledgeState.objects.filter(
                user_id=user_id,
                knowledge_point__name__in=algo_knowledge_points
            )
            
            # 计算平均掌握程度
            if knowledge_states.exists():
                total_proficiency = sum(state.proficiency_level for state in knowledge_states)
                avg_proficiency = total_proficiency / knowledge_states.count()
            else:
                avg_proficiency = 0.3  # 默认掌握程度
            
            # 获取算法相关题目的通过情况
            algo_tags = ProblemTag.objects.filter(name__in=algo_knowledge_points)
            algo_problems = Problem.objects.filter(tags__in=algo_tags).distinct()
            
            submitted_algo_problems = Submission.objects.filter(
                user_id=user_id,
                problem__in=algo_problems
            ).distinct()
            
            passed_algo_problems = submitted_algo_problems.filter(result=0)
            
            # 计算通过率
            algo_pass_rate = (
                passed_algo_problems.count() / submitted_algo_problems.count() 
                if submitted_algo_problems.count() > 0 else 0
            )
            
            # 获取用户解决的难题数量（高难度题目）
            hard_problems = passed_algo_problems.filter(problem__difficulty='High')
            hard_count_score = min(10, hard_problems.count())  # 最多10分
            
            # 综合得分 (满分40分)
            # 知识点掌握占40%，通过率占40%，难题解决占20%
            score = min(40, avg_proficiency * 16 + algo_pass_rate * 16 + hard_count_score * 0.8)
            return score
            
        except Exception as e:
            logger.error(f"Error assessing algorithm design ability: {str(e)}")
            return 15.0  # 默认分数
    @staticmethod
    def _assess_problem_solving(user_id):
        """
        评估问题解决能力
        基于：解题速度、一次通过率、调试次数等
        """
        try:
            # 获取用户的所有提交记录
            submissions = Submission.objects.filter(user_id=user_id)
            
            if not submissions.exists():
                return 10.0
            
            # 计算一次通过率
            total_problems = submissions.values('problem_id').distinct().count()
            first_pass_count = 0
            
            # 统计每个题目第一次就通过的数量
            problem_first_submissions = {}
            for submission in submissions.order_by('problem_id', 'create_time'):
                problem_id = submission.problem_id
                if problem_id not in problem_first_submissions:
                    problem_first_submissions[problem_id] = submission
                    if submission.result == 0:  # 假设0表示通过
                        first_pass_count += 1
            
            first_pass_rate = first_pass_count / total_problems if total_problems > 0 else 0
            
            # 计算平均解决时间（从第一次提交到通过的时间）
            total_solve_time = 0
            solved_count = 0
            
            user_problems = submissions.values('problem_id').distinct()
            for problem_entry in user_problems:
                problem_id = problem_entry['problem_id']
                problem_submissions = submissions.filter(problem_id=problem_id).order_by('create_time')
                
                # 找到第一个通过的提交
                passed_submission = problem_submissions.filter(result=0).first()
                if passed_submission:
                    first_submission = problem_submissions.first()
                    solve_time = (passed_submission.create_time - first_submission.create_time).total_seconds()
                    total_solve_time += solve_time
                    solved_count += 1
            
            avg_solve_time = total_solve_time / solved_count if solved_count > 0 else 3600  # 默认1小时
            
            # 时间因子（时间越短得分越高）
            time_factor = max(0, 1 - (avg_solve_time / 3600))  # 归一化到1小时内
            
            # 综合得分 (满分40分)
            # 一次通过率占50%，时间因子占50%
            score = min(40, first_pass_rate * 20 + time_factor * 20)
            return score
            
        except Exception as e:
            logger.error(f"Error assessing problem solving ability: {str(e)}")
            return 15.0  # 默认分数
        
    @staticmethod
    def _determine_level(overall_score):
        """
        根据总分确定能力等级
        """
        if overall_score >= 85:
            return 'expert'
        elif overall_score >= 70:
            return 'advanced'
        elif overall_score >= 50:
            return 'intermediate'
        else:
            return 'beginner'
        
    @staticmethod
    def _generate_analysis_report(user_id, basic_score, ds_score, algo_score, ps_score):
        """
        生成详细的分析报告
        """
        report = {
            'generated_at': timezone.now().isoformat(),
            'dimensions': {
                'basic_programming': {
                    'score': basic_score,
                    'max_score': 40,
                    'percentage': (basic_score / 40) * 100 if 40 > 0 else 0,
                    'assessment': AIProgrammingAbilityService._get_dimension_assessment('basic_programming', basic_score)
                },
                'data_structures': {
                    'score': ds_score,
                    'max_score': 40,
                    'percentage': (ds_score / 40) * 100 if 40 > 0 else 0,
                    'assessment': AIProgrammingAbilityService._get_dimension_assessment('data_structures', ds_score)
                },
                'algorithm_design': {
                    'score': algo_score,
                    'max_score': 40,
                    'percentage': (algo_score / 40) * 100 if 40 > 0 else 0,
                    'assessment': AIProgrammingAbilityService._get_dimension_assessment('algorithm_design', algo_score)
                },
                'problem_solving': {
                    'score': ps_score,
                    'max_score': 40,
                    'percentage': (ps_score / 40) * 100 if 40 > 0 else 0,
                    'assessment': AIProgrammingAbilityService._get_dimension_assessment('problem_solving', ps_score)
                }
            },
            'overall': {
                'score': (basic_score + ds_score + algo_score + ps_score),
                'max_score': 160,
                'level': AIProgrammingAbilityService._determine_level(basic_score + ds_score + algo_score + ps_score)
            },
            'recommendations': AIProgrammingAbilityService._generate_recommendations(
                user_id, basic_score, ds_score, algo_score, ps_score
            )
        }
        return report
    
    @staticmethod
    def _get_dimension_assessment(dimension, score):
        """
        根据维度得分给出评估
        """
        assessments = {
            'basic_programming': [
                "基础较薄弱，需要加强语法和基本编程概念的学习",
                "基础一般，建议多练习基础题目巩固知识",
                "基础扎实，继续保持",
                "基础非常扎实，可以挑战更高难度"
            ],
            'data_structures': [
                "对常用数据结构掌握不够，需要系统学习",
                "对基本数据结构有一定了解，还需深入理解",
                "对常见数据结构掌握较好，可以学习高级结构",
                "对各类数据结构都很熟悉，运用自如"
            ],
            'algorithm_design': [
                "算法思维有待提高，建议从基础算法开始学习",
                "具备一定算法思维，可以加强练习",
                "算法设计能力较强，可以挑战复杂算法",
                "算法设计能力出色，可以研究前沿算法"
            ],
            'problem_solving': [
                "解题思路不够清晰，需要培养分析问题的能力",
                "有一定的问题分析能力，还需提升解题效率",
                "解题能力强，思路清晰",
                "解题能力卓越，能快速准确地解决问题"
            ]
        }
        
        # 根据分数选择对应的评估（满分40分）
        if score < 15:
            idx = 0
        elif score < 25:
            idx = 1
        elif score < 35:
            idx = 2
        else:
            idx = 3
            
        return assessments.get(dimension, ["评估不可用"])[idx]
    @staticmethod
    def _generate_recommendations(user_id, basic_score, ds_score, algo_score, ps_score):
        """
        生成学习建议
        """
        recommendations = []
        
        # 基础编程建议
        if basic_score < 25:
            recommendations.append({
                'type': 'basic_programming',
                'priority': 'high',
                'content': '建议加强基础语法练习，多做一些入门级题目巩固基础知识'
            })
        elif basic_score < 35:
            recommendations.append({
                'type': 'basic_programming',
                'priority': 'medium',
                'content': '基础较为扎实，可以适当减少基础练习，转向更有挑战性的题目'
            })
        
        # 数据结构建议
        if ds_score < 25:
            recommendations.append({
                'type': 'data_structures',
                'priority': 'high',
                'content': '建议系统学习常用数据结构，理解其特性和适用场景'
            })
        elif ds_score < 35:
            recommendations.append({
                'type': 'data_structures',
                'priority': 'medium',
                'content': '对基本数据结构掌握良好，可以学习一些高级数据结构'
            })
        
        # 算法设计建议
        if algo_score < 25:
            recommendations.append({
                'type': 'algorithm_design',
                'priority': 'high',
                'content': '建议从基础算法入手，逐步学习更复杂的算法设计技巧'
            })
        elif algo_score < 35:
            recommendations.append({
                'type': 'algorithm_design',
                'priority': 'medium',
                'content': '算法基础不错，可以挑战一些经典算法问题'
            })
        
        # 问题解决建议
        if ps_score < 25:
            recommendations.append({
                'type': 'problem_solving',
                'priority': 'high',
                'content': '建议在解题前先仔细分析问题，制定清晰的解题思路'
            })
        elif ps_score < 35:
            recommendations.append({
                'type': 'problem_solving',
                'priority': 'medium',
                'content': '解题能力良好，注意提高解题效率和准确性'
            })
        
        # 通用建议
        recommendations.append({
            'type': 'general',
            'priority': 'low',
            'content': '保持持续练习，定期回顾错题，总结经验教训'
        })
        
        return recommendations
    
    @staticmethod
    def _update_ability_details(user_id, basic_score, ds_score, algo_score, ps_score):
        """
        更新详细能力记录
        """
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return
        
        # 更新各项能力详情
        dimensions = [
            ('basic_programming', basic_score, '基础编程能力'),
            ('data_structures', ds_score, '数据结构能力'),
            ('algorithm_design', algo_score, '算法设计能力'),
            ('problem_solving', ps_score, '问题解决能力')
        ]
        
        for dim_name, score, desc in dimensions:
            try:
                dimension = AIAbilityDimension.objects.get(name=dim_name)
                proficiency_level = AIProgrammingAbilityService._score_to_level(score)
                
                AIUserAbilityDetail.objects.update_or_create(
                    user=user,
                    dimension=dimension,
                    defaults={
                        'score': score,
                        'proficiency_level': proficiency_level,
                        'evidence': {
                            'last_score': score,
                            'description': desc,
                            'updated_at': timezone.now().isoformat()
                        }
                    }
                )
            except AIAbilityDimension.DoesNotExist:
                continue

    @staticmethod
    def _score_to_level(score):
        """
        将分数转换为熟练度级别
        """
        # 满分40分
        if score >= 35:
            return 'expert'
        elif score >= 25:
            return 'advanced'
        elif score >= 15:
            return 'intermediate'
        else:
            return 'beginner'
    @staticmethod
    def get_user_ability_report(user_id):
        """
        获取用户能力评估报告
        """
        try:
            ability = AIProgrammingAbility.objects.get(user_id=user_id)
            return ability
        except AIProgrammingAbility.DoesNotExist:
            # 如果还没有评估记录，则进行评估
            return AIProgrammingAbilityService.assess_user_ability(user_id)
        
    @staticmethod
    def _extract_ml_features(user_id):
        """
        提取用于机器学习模型的特征
        """
        try:
            # 获取用户提交记录
            submissions = Submission.objects.filter(user_id=user_id)
            
            if not submissions.exists():
                # 返回默认特征
                return [0] * 20
            
            # 基础统计特征
            total_submissions = submissions.count()
            accepted_submissions = submissions.filter(result=0).count()
            acceptance_rate = accepted_submissions / total_submissions if total_submissions > 0 else 0
            
            # 难度分布特征
            low_count = submissions.filter(problem__difficulty='Low', result=0).count()
            mid_count = submissions.filter(problem__difficulty='Mid', result=0).count()
            high_count = submissions.filter(problem__difficulty='High', result=0).count()
            
            total_accepted = low_count + mid_count + high_count
            low_ratio = low_count / (total_accepted + 1e-8)
            mid_ratio = mid_count / (total_accepted + 1e-8)
            high_ratio = high_count / (total_accepted + 1e-8)
            
            # 时间特征
            first_submission = submissions.earliest('create_time')
            last_submission = submissions.latest('create_time')
            active_days = (last_submission.create_time - first_submission.create_time).days
            
            # 平均每天提交次数
            avg_submissions_per_day = total_submissions / (active_days + 1)
            
            # 错误尝试特征
            failed_submissions = submissions.exclude(result=0).count()
            avg_attempts_per_problem = total_submissions / (total_accepted + 1e-8)
            
            # 知识点掌握特征
            knowledge_states = AIUserKnowledgeState.objects.filter(user_id=user_id)
            avg_proficiency = 0
            high_proficiency_count = 0
            low_proficiency_count = 0
            
            if knowledge_states.exists():
                total_proficiency = sum(state.proficiency_level for state in knowledge_states)
                avg_proficiency = total_proficiency / knowledge_states.count()
                high_proficiency_count = sum(1 for state in knowledge_states if state.proficiency_level > 0.7)
                low_proficiency_count = sum(1 for state in knowledge_states if state.proficiency_level < 0.3)
            
            # 标签特征
            tags = ProblemTag.objects.filter(problem__submission__user_id=user_id).distinct().count()
            
            # 构建特征向量
            features = [
                total_submissions,
                accepted_submissions,
                acceptance_rate,
                low_ratio,
                mid_ratio,
                high_ratio,
                active_days,
                avg_submissions_per_day,
                failed_submissions,
                avg_attempts_per_problem,
                avg_proficiency,
                high_proficiency_count,
                low_proficiency_count,
                tags,
                low_count,
                mid_count,
                high_count,
                acceptance_rate * high_ratio,  # 高难度通过率
                avg_proficiency * tags,        # 知识面广度与深度的结合
                active_days / (total_submissions + 1e-8)  # 活跃度
            ]
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting ML features for user {user_id}: {str(e)}")
            # 返回默认特征
            return [0] * 20
    @staticmethod
    def _train_ability_assessment_model():
        """
        训练能力评估模型
        """
        try:
            # 获取所有用户
            users = User.objects.all()
            
            if users.count() < 10:  # 数据量太少不训练
                return None
            
            # 准备训练数据
            X = []  # 特征
            y = []  # 目标值（各个维度的得分）
            
            for user in users:
                # 提取特征
                features = AIProgrammingAbilityService._extract_ml_features(user.id)
                
                # 获取现有的评估结果作为训练标签
                try:
                    ability_record = AIProgrammingAbility.objects.get(user=user)
                    # 使用现有的评估结果作为标签
                    y_basic = ability_record.basic_programming_score
                    y_ds = ability_record.data_structure_score
                    y_algo = ability_record.algorithm_design_score
                    y_ps = ability_record.problem_solving_score
                    y_overall = ability_record.overall_score
                    
                    X.append(features)
                    y.append([y_basic, y_ds, y_algo, y_ps, y_overall])
                except AIProgrammingAbility.DoesNotExist:
                    # 如果没有评估记录，跳过该用户
                    continue
            
            if len(X) < 10:  # 数据量太少
                return None
            
            # 转换为numpy数组
            import numpy as np
            X = np.array(X)
            y = np.array(y)
            
            # 标准化特征
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # 训练随机森林模型
            models = []
            for i in range(5):  # 为5个目标分别训练模型
                model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
                model.fit(X_scaled, y[:, i])
                models.append(model)
            
            # 保存模型和标准化器
            model_dir = 'ai/models/ml_models'
            if not os.path.exists(model_dir):
                os.makedirs(model_dir)
                
            for i, model in enumerate(models):
                joblib.dump(model, f'{model_dir}/ability_model_{i}.pkl')
            joblib.dump(scaler, f'{model_dir}/feature_scaler.pkl')
            
            logger.info("Ability assessment model trained and saved")
            return models, scaler
            
        except Exception as e:
            logger.error(f"Error training ability assessment model: {str(e)}")
            return None
    @staticmethod
    def _predict_ability_with_ml(user_id):
        """
        使用机器学习模型预测用户能力
        """
        try:
            # 检查模型是否存在
            model_dir = 'ai/models/ml_models'
            if not os.path.exists(f'{model_dir}/ability_model_0.pkl'):
                # 如果模型不存在，训练模型
                result = AIProgrammingAbilityService._train_ability_assessment_model()
                if result is None:
                    return None
            
            # 加载模型
            models = []
            for i in range(5):
                model = joblib.load(f'{model_dir}/ability_model_{i}.pkl')
                models.append(model)
            scaler = joblib.load(f'{model_dir}/feature_scaler.pkl')
            
            # 提取用户特征
            features = AIProgrammingAbilityService._extract_ml_features(user_id)
            
            # 标准化特征
            import numpy as np
            features_scaled = scaler.transform([features])
            
            # 进行预测
            predictions = []
            for model in models:
                pred = model.predict(features_scaled)[0]
                predictions.append(max(0, min(40, pred)))  # 限制在合理范围内
            
            # 解析预测结果
            basic_score, ds_score, algo_score, ps_score, overall_score = predictions
            
            # 确保总分计算正确
            if overall_score == predictions[4]:  # 如果总分是预测的
                overall_score = basic_score * 0.2 + ds_score * 0.25 + algo_score * 0.3 + ps_score * 0.25
            else:  # 否则重新计算
                overall_score = basic_score * 0.2 + ds_score * 0.25 + algo_score * 0.3 + ps_score * 0.25
            
            return {
                'basic_programming_score': basic_score,
                'data_structure_score': ds_score,
                'algorithm_design_score': algo_score,
                'problem_solving_score': ps_score,
                'overall_score': overall_score
            }
            
        except Exception as e:
            logger.error(f"Error predicting ability with ML for user {user_id}: {str(e)}")
            return None
        
    @staticmethod
    def assess_user_ability_enhanced(user_id):
        """
        增强版用户能力评估（结合机器学习）
        """
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise Exception("User not found")
        
        # 初始化能力维度
        AIProgrammingAbilityService.initialize_ability_dimensions()
        
        # 尝试使用机器学习模型进行预测
        ml_predictions = AIProgrammingAbilityService._predict_ability_with_ml(user_id)
        
        if ml_predictions:
            # 使用机器学习预测结果
            basic_score = ml_predictions['basic_programming_score']
            ds_score = ml_predictions['data_structure_score']
            algo_score = ml_predictions['algorithm_design_score']
            ps_score = ml_predictions['problem_solving_score']
            overall_score = ml_predictions['overall_score']
        else:
            # 回退到原有的评估方法
            basic_score = AIProgrammingAbilityService._assess_basic_programming(user_id)
            ds_score = AIProgrammingAbilityService._assess_data_structures(user_id)
            algo_score = AIProgrammingAbilityService._assess_algorithm_design(user_id)
            ps_score = AIProgrammingAbilityService._assess_problem_solving(user_id)
            overall_score = (
                basic_score * 0.2 +
                ds_score * 0.25 +
                algo_score * 0.3 +
                ps_score * 0.25
            )
        
        # 确定能力等级
        level = AIProgrammingAbilityService._determine_level(overall_score)
        
        # 生成分析报告
        analysis_report = AIProgrammingAbilityService._generate_analysis_report(
            user_id, basic_score, ds_score, algo_score, ps_score
        )
        
        # 更新或创建能力评估记录
        ability_record, created = AIProgrammingAbility.objects.update_or_create(
            user=user,
            defaults={
                'overall_score': overall_score,
                'basic_programming_score': basic_score,
                'data_structure_score': ds_score,
                'algorithm_design_score': algo_score,
                'problem_solving_score': ps_score,
                'level': level,
                'analysis_report': analysis_report
            }
        )
        
        # 更新详细能力记录
        AIProgrammingAbilityService._update_ability_details(
            user_id, basic_score, ds_score, algo_score, ps_score
        )
        
        return ability_record
    
    @staticmethod
    def _train_dl_ability_model():
        """
        训练深度学习能力评估模型
        """
        try:
            # 获取所有用户
            users = User.objects.all()
            
            if users.count() < 20:  # 数据量太少不训练
                return None
            
            # 准备训练数据
            X = []  # 特征
            y = []  # 目标值（各个维度的得分）
            
            for user in users:
                # 提取特征
                features = AIProgrammingAbilityService._extract_ml_features(user.id)
                
                # 获取现有的评估结果作为训练标签
                try:
                    ability_record = AIProgrammingAbility.objects.get(user=user)
                    # 使用现有的评估结果作为标签
                    y_basic = ability_record.basic_programming_score
                    y_ds = ability_record.data_structure_score
                    y_algo = ability_record.algorithm_design_score
                    y_ps = ability_record.problem_solving_score
                    y_overall = ability_record.overall_score
                    
                    X.append(features)
                    y.append([y_basic, y_ds, y_algo, y_ps, y_overall])
                except AIProgrammingAbility.DoesNotExist:
                    # 如果没有评估记录，跳过该用户
                    continue
            
            if len(X) < 20:  # 数据量太少
                return None
            
            # 转换为numpy数组
            import numpy as np
            X = np.array(X)
            y = np.array(y)
            
            # 划分训练集和验证集
            from sklearn.model_selection import train_test_split
            X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # 创建并训练深度学习模型
            dl_assessor = DeepLearningAbilityAssessor()
            dl_assessor.train(X_train, y_train, X_val, y_val, epochs=100)
            
            logger.info("Deep learning ability assessment model trained and saved")
            return dl_assessor
            
        except Exception as e:
            logger.error(f"Error training deep learning ability assessment model: {str(e)}")
            return None

    @staticmethod
    def _predict_ability_with_dl(user_id):
        """
        使用深度学习模型预测用户能力
        """
        try:
            # 检查模型是否存在
            model_path = 'ai/models/deep_learning/final_ability_model.pth'
            import os
            if not os.path.exists(model_path):
                # 如果模型不存在，训练模型
                dl_assessor = AIProgrammingAbilityService._train_dl_ability_model()
                if dl_assessor is None:
                    return None
            else:
                # 加载模型
                dl_assessor = DeepLearningAbilityAssessor(model_path)
            
            # 提取用户特征
            features = AIProgrammingAbilityService._extract_ml_features(user_id)
            
            # 进行预测
            predictions = dl_assessor.predict(features)[0]
            
            # 解析预测结果
            basic_score, ds_score, algo_score, ps_score, overall_score = predictions
            
            # 确保总分计算正确
            overall_score = basic_score * 0.2 + ds_score * 0.25 + algo_score * 0.3 + ps_score * 0.25
            
            return {
                'basic_programming_score': basic_score,
                'data_structure_score': ds_score,
                'algorithm_design_score': algo_score,
                'problem_solving_score': ps_score,
                'overall_score': overall_score
            }
            
        except Exception as e:
            logger.error(f"Error predicting ability with DL for user {user_id}: {str(e)}")
            return None
    @staticmethod
    def assess_user_ability_enhanced(user_id):
        """
        增强版用户能力评估（结合深度学习）
        """
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise Exception("User not found")
        
        # 初始化能力维度
        AIProgrammingAbilityService.initialize_ability_dimensions()
        
        # 尝试使用深度学习模型进行预测
        dl_predictions = AIProgrammingAbilityService._predict_ability_with_dl(user_id)
        
        if dl_predictions:
            # 使用深度学习预测结果
            basic_score = dl_predictions['basic_programming_score']
            ds_score = dl_predictions['data_structure_score']
            algo_score = dl_predictions['algorithm_design_score']
            ps_score = dl_predictions['problem_solving_score']
            overall_score = dl_predictions['overall_score']
        else:
            # 回退到原有的评估方法
            basic_score = AIProgrammingAbilityService._assess_basic_programming(user_id)
            ds_score = AIProgrammingAbilityService._assess_data_structures(user_id)
            algo_score = AIProgrammingAbilityService._assess_algorithm_design(user_id)
            ps_score = AIProgrammingAbilityService._assess_problem_solving(user_id)
            overall_score = (
                basic_score * 0.2 +
                ds_score * 0.25 +
                algo_score * 0.3 +
                ps_score * 0.25
            )
        
        # 确定能力等级
        level = AIProgrammingAbilityService._determine_level(overall_score)
        
        # 生成分析报告
        analysis_report = AIProgrammingAbilityService._generate_analysis_report(
            user_id, basic_score, ds_score, algo_score, ps_score
        )
        
        # 更新或创建能力评估记录
        ability_record, created = AIProgrammingAbility.objects.update_or_create(
            user=user,
            defaults={
                'overall_score': overall_score,
                'basic_programming_score': basic_score,
                'data_structure_score': ds_score,
                'algorithm_design_score': algo_score,
                'problem_solving_score': ps_score,
                'level': level,
                'analysis_report': analysis_report
            }
        )
        
        # 更新详细能力记录
        AIProgrammingAbilityService._update_ability_details(
            user_id, basic_score, ds_score, algo_score, ps_score
        )
        
        return ability_record



    




