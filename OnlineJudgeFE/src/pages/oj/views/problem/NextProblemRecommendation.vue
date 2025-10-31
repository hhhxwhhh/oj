<template>
    <div class="next-problem-recommendation">
        <div class="header">
            <h2>{{ $t('m.Next_Problem_Recommendation') }}</h2>
            <p>{{ $t('m.Based_on_your_submission') }}</p>
        </div>

        <div class="recommendation-content" v-if="recommendedProblem">
            <Card class="problem-card" :bordered="false" dis-hover>
                <div class="problem-header">
                    <div class="problem-title-section">
                        <h3 @click="goToProblem(recommendedProblem._id)" class="problem-title">
                            {{ recommendedProblem._id }}. {{ recommendedProblem.title }}
                        </h3>
                        <div class="problem-meta">
                            <Tag :color="getDifficultyColor(recommendedProblem.difficulty)">
                                {{ $t('m.' + recommendedProblem.difficulty) }}
                            </Tag>
                            <span class="ac-rate">
                                {{ $t('m.AC_Rate') }}: {{ getACRate(recommendedProblem.accepted_number,
                                    recommendedProblem.submission_number) }}
                            </span>
                        </div>
                    </div>
                </div>

                <div class="problem-tags" v-if="recommendedProblem.tags && recommendedProblem.tags.length > 0">
                    <div class="tags-label">{{ $t('m.Tags') }}:</div>
                    <div class="tags-container">
                        <Tag v-for="tag in recommendedProblem.tags" :key="tag" color="blue">{{ tag }}</Tag>
                    </div>
                </div>

                <div class="problem-description">
                    <div class="description-label">{{ $t('m.Description') }}:</div>
                    <div class="description-content" v-html="formatDescription(recommendedProblem.description)"></div>
                </div>

                <div class="recommendation-reason" v-if="recommendationReason">
                    <div class="reason-label">{{ $t('m.Why_Recommended') }}:</div>
                    <div class="reason-content">{{ recommendationReason }}</div>
                </div>

                <div class="actions">
                    <Button type="primary" @click="goToProblem(recommendedProblem._id)" size="large">
                        {{ $t('m.Try_This_Problem') }}
                    </Button>
                    <Button @click="getNewRecommendation" :loading="loading" size="large" style="margin-left: 10px;">
                        {{ $t('m.Get_Another_Recommendation') }}
                    </Button>
                    <Button @click="goBackToProblem" size="large" style="margin-left: 10px;">
                        {{ $t('m.Back_to_Problem') }}
                    </Button>
                </div>

                <!-- 添加反馈区域 -->
                <div class="feedback-section">
                    <div class="feedback-label">{{ $t('m.Is_this_recommendation_helpful') }}</div>
                    <div class="feedback-buttons">
                        <Button type="success" @click="submitFeedback(true)" size="large">
                            {{ $t('m.Yes_It_is_helpful') }}
                        </Button>
                        <Button type="error" @click="submitFeedback(false)" size="large" style="margin-left: 10px;">
                            {{ $t('m.No_It_is_not_helpful') }}
                        </Button>
                    </div>
                </div>
            </Card>
        </div>

        <div class="loading-container" v-else-if="loading">
            <Spin size="large" />
            <p>{{ $t('m.Finding_best_problem_for_you') }}</p>
        </div>

        <div class="no-recommendation" v-else>
            <Icon type="ios-information-circle-outline" size="48" />
            <p>{{ $t('m.Unable_to_generate_recommendation') }}</p>
            <Button @click="getNewRecommendation" type="primary">{{ $t('m.Try_Again') }}</Button>
        </div>
    </div>
</template>

<script>
import api from '@oj/api'
import { mapGetters } from 'vuex'

export default {
    name: 'NextProblemRecommendation',
    data() {
        return {
            recommendedProblem: null,
            recommendationReason: '',
            loading: false,
            isRequesting: false,
        }
    },
    mounted() {
        this.getRecommendation()
    },
    methods: {
        async getRecommendation() {
            this.loading = true
            try {
                // 从路由参数中获取题目ID和提交结果
                const problemId = this.$route.params.problemID
                const submissionResult = this.$route.query.result || ''

                // 向AI服务发送请求，基于用户刚刚的提交获取推荐题目
                const res = await api.getNextProblemRecommendation({
                    problem_id: problemId,
                    submission_result: submissionResult
                })

                if (res.data && res.data.error === null && res.data.data && res.data.data.length > 0) {
                    this.recommendedProblem = res.data.data[0]
                    this.recommendationReason = this.recommendedProblem.reason || ''
                } else {
                    this.recommendedProblem = null
                    this.recommendationReason = ''
                }
            } catch (err) {
                console.error('Failed to get recommendation:', err)
                // 检查错误响应
                if (err.response && err.response.data) {
                    this.$error(err.response.data.data || this.$t('m.Failed_to_get_recommendation'))
                } else {
                    this.$error(this.$t('m.Failed_to_get_recommendation'))
                }
            } finally {
                this.loading = false
            }
        },

        async getNewRecommendation() {
            if (this.isRequesting) {
                return
            }
            this.isRequesting = true
            this.loading = true
            // 清除当前推荐题目，让用户知道正在加载
            this.recommendedProblem = null
            this.recommendationReason = ''
            try {
                await this.getRecommendation()
                if (!this.recommendedProblem) {
                    this.$Message.warning('暂时没有其他推荐题目')
                }
            } catch (error) {
                this.$Message.error('获取新推荐题目失败，请稍后重试')
            } finally {
                this.loading = false
                this.isRequesting = false
            }
        },

        getDifficultyColor(difficulty) {
            const colorMap = {
                'Low': 'success',
                'Mid': 'warning',
                'High': 'error'
            }
            return colorMap[difficulty] || 'default'
        },

        getACRate(acceptedCount, submissionCount) {
            if (submissionCount === 0) return '0%'
            return Math.round(acceptedCount / submissionCount * 100) + '%'
        },

        formatDescription(description) {
            // 简单的HTML清理，防止XSS
            if (!description) return ''
            return description.replace(/<script[^>]*>.*?<\/script>/gi, '')
        },
        goToProblem(problemId) {
            this.$router.push({
                name: 'problem-details',
                params: { problemID: problemId }
            })
        },
        goBackToProblem() {
            // 如果是从题目页面跳转过来的，返回到原题目
            if (this.$route.params.problemID) {
                this.$router.push({
                    name: 'problem-details',
                    params: { problemID: this.$route.params.problemID }
                })
            } else {
                // 否则返回到题目列表
                this.$router.push({ name: 'problem-list' })
            }
        },

        // 添加反馈提交方法
        async submitFeedback(accepted) {
            if (!this.recommendedProblem || !this.recommendedProblem.recommendation_id) {
                this.$Message.warning(this.$t('m.No_recommendation_to_feedback'));
                return;
            }

            try {
                await api.submitRecommendationFeedback({
                    recommendation_id: this.recommendedProblem.recommendation_id,
                    accepted: accepted,
                    solved: false // 可以根据实际情况设置
                });

                this.$Message.success(this.$t('m.Feedback_submitted'));

                // 如果反馈为无用，获取新的推荐
                if (!accepted) {
                    this.getNewRecommendation();
                }
            } catch (error) {
                console.error('Failed to submit feedback:', error);
                this.$error(this.$t('m.Failed_to_submit_feedback'));
            }
        },
    }
}
</script>

<style scoped lang="less">
.next-problem-recommendation {
    padding: 20px;

    .header {
        text-align: center;
        margin-bottom: 30px;

        h2 {
            font-size: 24px;
            color: #2d8cf0;
            margin-bottom: 10px;
        }

        p {
            color: #808695;
            font-size: 14px;
        }
    }

    .recommendation-content {
        max-width: 800px;
        margin: 0 auto;

        .problem-card {
            .problem-header {
                margin-bottom: 20px;

                .problem-title-section {
                    .problem-title {
                        font-size: 20px;
                        margin-bottom: 10px;
                        cursor: pointer;
                        color: #2d8cf0;

                        &:hover {
                            text-decoration: underline;
                        }
                    }

                    .problem-meta {
                        display: flex;
                        align-items: center;
                        gap: 10px;
                    }
                }
            }

            .problem-tags {
                margin-bottom: 20px;

                .tags-label {
                    font-weight: bold;
                    margin-bottom: 5px;
                }

                .tags-container {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 5px;
                }
            }

            .problem-description {
                margin-bottom: 20px;

                .description-label {
                    font-weight: bold;
                    margin-bottom: 5px;
                }

                .description-content {
                    padding: 10px;
                    background-color: #f8f8f9;
                    border-radius: 4px;
                }
            }

            .recommendation-reason {
                margin-bottom: 20px;
                padding: 10px;
                background-color: #e6f7ff;
                border-radius: 4px;

                .reason-label {
                    font-weight: bold;
                    margin-bottom: 5px;
                }

                .reason-content {
                    color: #555;
                }
            }

            .actions {
                display: flex;
                justify-content: center;
                margin-bottom: 20px;
                flex-wrap: wrap;
                gap: 10px;
            }

            .feedback-section {
                padding: 20px;
                border-top: 1px solid #e8eaec;
                text-align: center;

                .feedback-label {
                    margin-bottom: 15px;
                    font-weight: bold;
                    color: #555;
                }

                .feedback-buttons {
                    display: flex;
                    justify-content: center;
                    gap: 10px;
                    flex-wrap: wrap;
                }
            }
        }
    }

    .loading-container {
        text-align: center;
        padding: 40px 20px;

        p {
            margin-top: 15px;
            color: #808695;
        }
    }

    .no-recommendation {
        text-align: center;
        padding: 40px 20px;

        p {
            margin: 15px 0;
            color: #808695;
        }
    }
}
</style>