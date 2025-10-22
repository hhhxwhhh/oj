import openai
import requests
import json
import re
from django.db import transaction
from .models import AIModel, AIMessage,AICodeExplanationCache,AIUserKnowledgeState,AIUserLearningPath,AIUserLearningPathNode
from .models import KnowledgePoint,AIUserKnowledgeState
from problem.models import Problem
from submission.models import Submission
import logging
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import hashlib
from account.models import User

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
                "completions": []
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
    def hybrid_recommendations(user_id,count=10):
        cf_recommendations=AIRecommendationService.collaborative_filtering_recommendations(user_id=user_id,count=count*2)
        cb_recommendations=AIRecommendationService.content_based_recommendations(user_id=user_id,count=count*2)
        problem_socres=defaultdict(list)
        for probelm_id,score,reason in cf_recommendations:
            problem_socres[probelm_id].append((score,reason))
        for probelm_id,score,reason in cb_recommendations:
            problem_socres[probelm_id].append((score,reason))
        final_recomendations=[]
        for problem_id,scores_reasons in problem_socres.items():
            avg_score = sum(score for score, _ in scores_reasons) / len(scores_reasons)
            reasons=list(set(reason for _,reason in scores_reasons))
            combined_reason=", ".join(reasons)
            final_recomendations.append((problem_id,avg_score,combined_reason))

        final_recomendations.sort(key=lambda x:x[1],reverse=True)
        return final_recomendations[:count]
    
    @staticmethod
    def recommend_problems(user_id,count=10):
        """推荐题目的对外接口"""
        try:
            recommendations=AIRecommendationService.hybrid_recommendations(user_id=user_id,count=count)
            return recommendations
        except Exception as e:
            popular_problems=Problem.objects.filter(visible=True).order_by("-accepted_number")[:count]
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
                    # 处理content_id可能为空的情况
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
                        knowledge_point=knowledge_point  # 新增字段
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
        基于知识点掌握情况推荐需要加强的知识点
        """
        try:
            # 获取用户知识点状态，按掌握程度排序（掌握程度低的排在前面）
            user_states = AIUserKnowledgeState.objects.filter(
                user_id=user_id
            ).order_by('proficiency_level')[:count]
            
            recommendations = []
            for state in user_states:
                recommendations.append({
                    'knowledge_point': state.knowledge_point.name,
                    'proficiency_level': state.proficiency_level,
                    'recommended_problems': KnowledgePointService._get_problems_for_knowledge_point(
                        state.knowledge_point, user_id
                    )
                })
            
            return recommendations
        except Exception as e:
            logger.error(f"Failed to get knowledge recommendations: {str(e)}")
            return []

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

    


