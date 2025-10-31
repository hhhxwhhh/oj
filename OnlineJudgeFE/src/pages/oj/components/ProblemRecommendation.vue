<template>
    <div class="problem-recommendation">
        <Panel :padding="15" shadow>
            <div slot="title" class="title">
                <Icon type="md-compass" /> {{ $t('m.Recommended_For_You') }}
            </div>
            <div slot="extra">
                <Button type="primary" size="small" @click="refreshRecommendations" :loading="loading">
                    <Icon type="md-refresh" /> {{ $t('m.Refresh') }}
                </Button>
            </div>

            <div v-if="loading" class="loading">
                <Spin size="large">{{ $t('m.Loading') }}</Spin>
            </div>

            <div v-else>
                <div v-if="recommendations.length === 0" class="no-recommendations">
                    <p>{{ $t('m.No_Recommendations') }}</p>
                </div>

                <div v-else>
                    <div v-for="(problem, index) in recommendations" :key="problem.problem_id"
                        class="recommendation-item" @click="goToProblem(problem.problem_display_id)">
                        <div class="item-header">
                            <span class="problem-id">{{ problem.problem_display_id }}</span>
                            <span class="problem-title">{{ problem.title }}</span>
                        </div>
                        <div class="item-meta">
                            <Tag :color="getDifficultyColor(problem.difficulty)" class="difficulty-tag">
                                {{ problem.difficulty }}
                            </Tag>
                            <span class="acceptance-rate">
                                {{ $t('m.Acceptance') }}: {{ (problem.acceptance_rate * 100).toFixed(1) }}%
                            </span>
                        </div>
                        <div class="recommendation-reason">
                            <Icon type="md-information-circle" /> {{ problem.reason }}
                        </div>
                        <!-- 添加反馈按钮 -->
                        <div class="feedback-buttons">
                            <Button size="small" type="success" @click.stop="submitFeedback(problem, true)">有用</Button>
                            <Button size="small" type="error" @click.stop="submitFeedback(problem, false)">无用</Button>
                        </div>
                    </div>

                    <div class="recommendation-footer">
                        <p>{{ $t('m.Based_on_your_solved_problems') }}</p>
                    </div>
                </div>
            </div>
        </Panel>
    </div>
</template>

<script>
import api from '@oj/api'
import { ProblemMixin } from '@oj/components/mixins'

export default {
    name: 'ProblemRecommendation',
    mixins: [ProblemMixin],
    data() {
        return {
            recommendations: [],
            loading: true
        }
    },

    mounted() {
        this.loadRecommendations()
    },

    methods: {
        async loadRecommendations() {
            this.loading = true
            try {
                const response = await api.getRecommendedProblems(10)
                this.recommendations = response.data.data || []
            } catch (error) {
                console.error('Failed to load recommendations:', error)
                this.$error(this.$t('m.Failed_to_load_recommendations'))
            } finally {
                this.loading = false
            }
        },

        refreshRecommendations() {
            this.loadRecommendations()
        },

        getDifficultyColor(difficulty) {
            const colorMap = {
                'Low': 'success',
                'Mid': 'warning',
                'High': 'error'
            }
            return colorMap[difficulty] || 'default'
        },

        goToProblem(problemID) {
            this.$router.push({ name: 'problem-details', params: { problemID } })
        },

        // 添加反馈提交方法
        async submitFeedback(problem, accepted) {
            try {
                // 查找推荐记录ID
                const recommendationId = problem.recommendation_id || problem.id;

                await api.submitRecommendationFeedback({
                    recommendation_id: recommendationId,
                    accepted: accepted,
                    solved: false
                });

                this.$Message.success(this.$t('m.Feedback_submitted'));

                if (!accepted) {
                    this.refreshRecommendations();
                }
            } catch (error) {
                console.error('Failed to submit feedback:', error);
                this.$error(this.$t('m.Failed_to_submit_feedback'));
            }
        }
    }
}
</script>

<style scoped lang="less">
.problem-recommendation {
    .title {
        font-weight: 500;
    }

    .loading {
        text-align: center;
        padding: 20px;
    }

    .no-recommendations {
        text-align: center;
        padding: 20px;
        color: #999;
    }

    .recommendation-item {
        padding: 12px 0;
        border-bottom: 1px solid #e8eaec;
        cursor: pointer;
        transition: background-color 0.2s;

        &:last-child {
            border-bottom: none;
        }

        &:hover {
            background-color: #f8f8f9;
        }

        .item-header {
            display: flex;
            align-items: center;
            margin-bottom: 5px;

            .problem-id {
                font-weight: 600;
                color: #2d8cf0;
                margin-right: 8px;
                font-family: monospace;
            }

            .problem-title {
                font-size: 15px;
                flex: 1;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
        }

        .item-meta {
            display: flex;
            align-items: center;
            margin-bottom: 5px;

            .difficulty-tag {
                margin-right: 10px;
            }

            .acceptance-rate {
                font-size: 12px;
                color: #808695;
            }
        }

        .recommendation-reason {
            font-size: 12px;
            color: #808695;
            margin-bottom: 8px;

            i {
                margin-right: 4px;
            }
        }

        .feedback-buttons {
            display: flex;
            gap: 5px;
            justify-content: flex-end;
        }
    }

    .recommendation-footer {
        margin-top: 10px;
        text-align: center;

        p {
            font-size: 12px;
            color: #c5c8ce;
        }
    }
}
</style>