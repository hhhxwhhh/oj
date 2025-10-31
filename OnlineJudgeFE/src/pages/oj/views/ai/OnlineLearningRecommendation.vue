<template>
    <div class="online-learning-recommendation">
        <div class="header">
            <h2>{{ $t('m.Online_Learning_Recommendation') }}</h2>
            <p>{{ $t('m.Recommendations_based_on_your_interactions') }}</p>
        </div>

        <Card :bordered="false" dis-hover>
            <div class="algorithm-selector">
                <div class="selector-label">{{ $t('m.Select_Recommendation_Algorithm') }}:</div>
                <RadioGroup v-model="selectedAlgorithm" @on-change="onAlgorithmChange" type="button">
                    <Radio label="hybrid">{{ $t('Hybrid Recommendation') }}</Radio>
                    <Radio label="collaborative">{{ $t('Collaborative Filtering') }}</Radio>
                    <Radio label="content">{{ $t('Content Based') }}</Radio>
                    <Radio label="online_learning">{{ $t('Online Learning') }}</Radio>
                </RadioGroup>
            </div>

            <div class="recommendations-container">
                <div v-if="loading" class="loading">
                    <Spin size="large">{{ $t('Loading recommendations') }}</Spin>
                </div>

                <div v-else-if="recommendations.length === 0" class="no-recommendations">
                    <p>{{ $t('No recommendations available') }}</p>
                </div>

                <div v-else class="recommendations-list">
                    <div v-for="(problem, index) in recommendations" :key="problem.problem_id"
                        class="recommendation-item" @click="goToProblem(problem.problem_display_id)">
                        <div class="item-header">
                            <span class="problem-id">{{ problem.problem_display_id }}</span>
                            <span class="problem-title">{{ problem.title }}</span>
                            <Tag v-if="problem.algorithm_score" :color="getScoreColor(problem.algorithm_score)"
                                class="score-tag">
                                {{ (problem.algorithm_score * 100).toFixed(1) }}%
                            </Tag>
                        </div>

                        <div class="item-meta">
                            <Tag :color="getDifficultyColor(problem.difficulty)" class="difficulty-tag">
                                {{ problem.difficulty }}
                            </Tag>
                            <span class="acceptance-rate">
                                {{ $t('Acceptance') }}: {{ (problem.acceptance_rate * 100).toFixed(1) }}%
                            </span>
                        </div>

                        <div class="recommendation-reason">
                            <Icon type="md-information-circle" /> {{ problem.reason }}
                        </div>

                        <div class="feedback-buttons">
                            <Button size="small" type="success" @click.stop="submitFeedback(problem, true)">
                                {{ $t('Helpful') }}
                            </Button>
                            <Button size="small" type="error" @click.stop="submitFeedback(problem, false)">
                                {{ $t('Not Helpful') }}
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        </Card>
    </div>
</template>

<script>
import api from '@oj/api'
import { ProblemMixin } from '@oj/components/mixins'

export default {
    name: 'OnlineLearningRecommendation',
    mixins: [ProblemMixin],
    data() {
        return {
            recommendations: [],
            loading: false,
            selectedAlgorithm: 'online_learning'
        }
    },

    mounted() {
        this.loadRecommendations();
    },

    methods: {
        async loadRecommendations() {
            this.loading = true;
            try {
                const response = await api.getRecommendedProblems(15, this.selectedAlgorithm);
                this.recommendations = response.data.data || [];
            } catch (error) {
                console.error('Failed to load recommendations:', error);
                this.$error(this.$t('m.Failed_to_load_recommendations'));
            } finally {
                this.loading = false;
            }
        },

        onAlgorithmChange() {
            this.loadRecommendations();
        },

        async submitFeedback(problem, accepted) {
            try {
                await api.submitRecommendationFeedback({
                    recommendation_id: problem.recommendation_id || problem.id,
                    accepted: accepted,
                    solved: false
                });

                this.$Message.success(this.$t('m.Feedback_submitted'));

                // 如果反馈为无用，刷新推荐
                if (!accepted) {
                    this.loadRecommendations();
                }
            } catch (error) {
                console.error('Failed to submit feedback:', error);
                this.$error(this.$t('m.Failed_to_submit_feedback'));
            }
        },

        goToProblem(problemID) {
            this.$router.push({ name: 'problem-details', params: { problemID } });
        },

        getDifficultyColor(difficulty) {
            const colorMap = {
                'Low': 'success',
                'Mid': 'warning',
                'High': 'error'
            };
            return colorMap[difficulty] || 'default';
        },

        getScoreColor(score) {
            if (score >= 0.8) return 'success';
            if (score >= 0.6) return 'warning';
            return 'error';
        }
    }
}
</script>

<style scoped lang="less">
.online-learning-recommendation {
    padding: 20px;
    max-width: 1200px;
    margin: 0 auto;

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

    .algorithm-selector {
        margin-bottom: 20px;
        padding: 15px;
        background-color: #f8f8f9;
        border-radius: 4px;

        .selector-label {
            margin-bottom: 10px;
            font-weight: bold;
        }
    }

    .recommendations-container {
        .loading {
            text-align: center;
            padding: 40px 20px;
        }

        .no-recommendations {
            text-align: center;
            padding: 40px 20px;
            color: #999;
        }

        .recommendations-list {
            .recommendation-item {
                padding: 15px;
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
                    margin-bottom: 8px;

                    .problem-id {
                        font-weight: 600;
                        color: #2d8cf0;
                        margin-right: 10px;
                        font-family: monospace;
                    }

                    .problem-title {
                        font-size: 16px;
                        flex: 1;
                        white-space: nowrap;
                        overflow: hidden;
                        text-overflow: ellipsis;
                    }

                    .score-tag {
                        flex-shrink: 0;
                    }
                }

                .item-meta {
                    display: flex;
                    align-items: center;
                    margin-bottom: 8px;

                    .difficulty-tag {
                        margin-right: 10px;
                    }

                    .acceptance-rate {
                        font-size: 13px;
                        color: #808695;
                    }
                }

                .recommendation-reason {
                    font-size: 13px;
                    color: #808695;
                    margin-bottom: 10px;

                    i {
                        margin-right: 4px;
                    }
                }

                .feedback-buttons {
                    display: flex;
                    gap: 8px;
                    justify-content: flex-end;
                }
            }
        }
    }
}
</style>