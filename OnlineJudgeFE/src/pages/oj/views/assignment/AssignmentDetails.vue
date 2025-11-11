<template>
    <div class="assignment-details-container">
        <div class="assignment-content" v-if="!loading && assignment">
            <Panel :padding="24" shadow>
                <div slot="title" class="panel-title">{{ assignment.title }}</div>
                <div class="assignment-meta">
                    <div class="meta-item">
                        <Icon type="ios-calendar" />
                        <span>{{ $t('m.Start_Time') }}: {{ assignment.start_time | localtime }}</span>
                    </div>
                    <div class="meta-item">
                        <Icon type="ios-calendar" />
                        <span>{{ $t('m.End_Time') }}: {{ assignment.end_time | localtime }}</span>
                    </div>
                    <div class="meta-item">
                        <Icon type="ios-list" />
                        <span>{{ $t('m.Problems_Count') }}: {{ assignment.problem_count }}</span>
                    </div>
                    <div class="meta-item">
                        <Icon type="md-checkmark" />
                        <span>{{ $t('m.Status') }}:
                            <Tag :color="getStatusColor(assignment.status)">
                                {{ getStatusText(assignment.status) }}
                            </Tag>
                        </span>
                    </div>
                    <div class="meta-item" v-if="assignment.score !== null">
                        <Icon type="md-medal" />
                        <span>{{ $t('m.Score') }}: {{ assignment.score }}/{{ assignment.max_score }}</span>
                    </div>
                </div>
                <div class="assignment-description">
                    <h3>{{ $t('m.Description') }}</h3>
                    <p>{{ assignment.description }}</p>
                </div>
            </Panel>

            <Panel :padding="24" shadow class="problems-panel">
                <div slot="title" class="panel-title">{{ $t('m.Problems') }}</div>
                <div class="problems-list">
                    <div v-if="problems.length === 0" class="no-problems">
                        <Icon type="ios-book-outline" size="80" />
                        <p>{{ $t('m.No_Problems') }}</p>
                    </div>
                    <div v-else>
                        <div v-for="(problem, index) in problems" :key="problem.id" class="problem-item">
                            <Card class="problem-card" @click.native="goToProblem(problem.problem_id)">
                                <div class="problem-header">
                                    <div class="problem-index">{{ String.fromCharCode(65 + index) }}.</div>
                                    <div class="problem-title">{{ problem.problem_title }}</div>
                                    <div class="problem-score">{{ problem.score }} {{ $t('m.Points') }}</div>
                                </div>
                                <div class="problem-meta">
                                    <Tag :color="getDifficultyColor(problem.problem_difficulty)">
                                        {{ $t('m.' + problem.problem_difficulty) }}
                                    </Tag>
                                    <span class="ac-rate">
                                        {{ $t('m.AC_Rate') }}: {{ getACRate(problem.problem_accepted_number,
                                            problem.problem_submission_number) }}
                                    </span>
                                </div>
                            </Card>
                        </div>
                    </div>
                </div>
            </Panel>
        </div>

        <div class="loading-container" v-else-if="loading">
            <Spin size="large" />
            <p>{{ $t('m.Loading') }}</p>
        </div>

        <div class="error-container" v-else>
            <Icon type="ios-information-circle-outline" size="80" />
            <p>{{ $t('m.Failed_to_get_Assignment_Details') }}</p>
            <Button @click="loadAssignmentDetails" type="primary">{{ $t('m.Refresh') }}</Button>
        </div>
    </div>
</template>

<script>
import api from '@oj/api'
import moment from 'moment'

export default {
    name: 'AssignmentDetails',
    data() {
        return {
            loading: true,
            assignment: null,
            problems: []
        }
    },
    mounted() {
        this.loadAssignmentDetails()
    },
    methods: {
        loadAssignmentDetails() {
            this.loading = true
            const assignmentID = this.$route.params.assignmentID

            // 获取作业详情
            api.getUserAssignmentDetail(assignmentID).then(res => {
                this.assignment = res.data.data
                return api.getAssignmentProblems(this.assignment.assignment_id)
            }).then(res => {
                this.problems = res.data.data
                this.loading = false
            }).catch(() => {
                this.loading = false
                this.$error(this.$t('m.Failed_to_get_Assignment_Details'))
            })
        },

        goToProblem(problemID) {
            this.$router.push({
                name: 'problem-details',
                params: { problemID: problemID }
            })
        },

        getStatusColor(status) {
            const statusColors = {
                'not_started': 'blue',
                'in_progress': 'green',
                'ended': 'red'
            }
            return statusColors[status] || 'blue'
        },

        getStatusText(status) {
            const statusTexts = {
                'not_started': this.$t('m.Not_Started'),
                'in_progress': this.$t('m.In_Progress'),
                'ended': this.$t('m.Ended')
            }
            return statusTexts[status] || status
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
        }
    },
    filters: {
        localtime(date) {
            if (!date) return ''
            return moment(date).format('YYYY-MM-DD HH:mm:ss')
        }
    }
}
</script>

<style lang="less" scoped>
.assignment-details-container {
    margin: 20px auto;
    max-width: 1200px;
    width: 100%;

    .assignment-content {
        margin: 0 20px;

        .panel-title {
            font-size: 26px;
            font-weight: 700;
            color: #2c3e50;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }

        .assignment-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-bottom: 20px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 8px;

            .meta-item {
                display: flex;
                align-items: center;
                font-size: 14px;
                color: #555;

                i {
                    margin-right: 8px;
                    color: #40a9ff;
                }
            }
        }

        .assignment-description {
            h3 {
                margin-top: 0;
                margin-bottom: 15px;
                color: #2c3e50;
            }

            p {
                color: #666;
                line-height: 1.6;
                font-size: 15px;
            }
        }

        .problems-panel {
            margin-top: 20px;

            .problems-list {
                .no-problems {
                    text-align: center;
                    padding: 40px 20px;
                    color: #999;

                    p {
                        margin-top: 20px;
                        font-size: 20px;
                    }
                }

                .problem-item {
                    margin-bottom: 15px;

                    .problem-card {
                        cursor: pointer;
                        transition: all 0.3s ease;
                        border: 1px solid #e8eaec;
                        border-radius: 8px;

                        &:hover {
                            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
                            border-color: #40a9ff;
                        }

                        .problem-header {
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                            padding: 15px 20px;
                            border-bottom: 1px solid #eee;

                            .problem-index {
                                font-weight: bold;
                                color: #40a9ff;
                                font-size: 18px;
                            }

                            .problem-title {
                                flex: 1;
                                margin: 0 20px;
                                font-size: 16px;
                                color: #2c3e50;
                            }

                            .problem-score {
                                font-weight: bold;
                                color: #52c41a;
                            }
                        }

                        .problem-meta {
                            padding: 15px 20px;
                            display: flex;
                            align-items: center;
                            gap: 15px;

                            .ac-rate {
                                color: #888;
                                font-size: 14px;
                            }
                        }
                    }
                }
            }
        }
    }

    .loading-container,
    .error-container {
        text-align: center;
        padding: 60px 20px;

        p {
            margin: 20px 0;
            font-size: 18px;
            color: #666;
        }
    }
}

@media (max-width: 768px) {
    .assignment-details-container {
        margin: 10px auto;

        .assignment-content {
            margin: 0 10px;

            .assignment-meta {
                flex-direction: column;
                gap: 10px;
                padding: 10px;
            }

            .problems-panel {
                .problems-list {
                    .problem-item {
                        .problem-card {
                            .problem-header {
                                flex-direction: column;
                                align-items: flex-start;
                                gap: 10px;

                                .problem-title {
                                    margin: 10px 0;
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
</style>