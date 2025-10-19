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
    props: {
        // 用户刚刚提交的题目ID
        problemId: {
            type: [String, Number],
            required: true
        },
        // 用户提交的结果（AC, WA等）
        submissionResult: {
            type: String,
            default: ''
        }
    },
    data() {
        return {
            recommendedProblem: null,
            recommendationReason: '',
            loading: false
        }
    },
    mounted() {
        this.getRecommendation()
    },
    methods: {
        async getRecommendation() {
            this.loading = true
            try {
                // 向AI服务发送请求，基于用户刚刚的提交获取推荐题目
                const res = await api.getNextProblemRecommendation({
                    problem_id: this.problemId,
                    submission_result: this.submissionResult
                })

                if (res.data.data && res.data.data.length > 0) {
                    this.recommendedProblem = res.data.data[0]
                    this.recommendationReason = this.recommendedProblem.reason || ''
                } else {
                    this.recommendedProblem = null
                    this.recommendationReason = ''
                }
            } catch (err) {
                console.error('Failed to get recommendation:', err)
                this.$error(this.$t('m.Failed_to_get_recommendation'))
            } finally {
                this.loading = false
            }
        },

        async getNewRecommendation() {
            await this.getRecommendation()
        },

        goToProblem(problemId) {
            this.$router.push({
                name: 'problem-details',
                params: { problemID: problemId }
            })
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
        }
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
            box-shadow: 0 1px 6px rgba(0, 0, 0, 0.1);

            .problem-header {
                margin-bottom: 20px;

                .problem-title-section {
                    .problem-title {
                        font-size: 20px;
                        margin-bottom: 15px;
                        color: #2d8cf0;
                        cursor: pointer;

                        &:hover {
                            text-decoration: underline;
                        }
                    }

                    .problem-meta {
                        display: flex;
                        align-items: center;
                        gap: 15px;

                        .ac-rate {
                            font-size: 14px;
                            color: #808695;
                        }
                    }
                }
            }

            .problem-tags {
                margin-bottom: 20px;

                .tags-label {
                    font-weight: bold;
                    margin-bottom: 8px;
                    color: #515a6e;
                }

                .tags-container {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 8px;
                }
            }

            .problem-description {
                margin-bottom: 20px;

                .description-label {
                    font-weight: bold;
                    margin-bottom: 8px;
                    color: #515a6e;
                }

                .description-content {
                    padding: 15px;
                    background-color: #f8f8f9;
                    border-radius: 4px;
                    max-height: 200px;
                    overflow-y: auto;

                    /deep/ p {
                        margin: 0 0 10px 0;
                    }
                }
            }

            .recommendation-reason {
                margin-bottom: 25px;
                padding: 15px;
                background-color: #e6f7ff;
                border-radius: 4px;
                border-left: 4px solid #1890ff;

                .reason-label {
                    font-weight: bold;
                    margin-bottom: 8px;
                    color: #515a6e;
                }

                .reason-content {
                    color: #515a6e;
                    line-height: 1.5;
                }
            }

            .actions {
                text-align: center;
                padding-top: 20px;
                border-top: 1px solid #e8eaec;
            }
        }
    }

    .loading-container {
        text-align: center;
        padding: 50px 0;

        p {
            margin-top: 20px;
            color: #808695;
        }
    }

    .no-recommendation {
        text-align: center;
        padding: 50px 20px;

        i {
            color: #e8eaec;
            margin-bottom: 20px;
        }

        p {
            font-size: 16px;
            color: #808695;
            margin-bottom: 20px;
        }
    }
}
</style>