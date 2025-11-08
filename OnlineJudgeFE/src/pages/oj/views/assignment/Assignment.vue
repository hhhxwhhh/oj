<template>
    <div class="assignment-container">
        <div class="assignment-content">
            <Panel :padding="20" shadow>
                <div slot="title" class="panel-title">{{ $t('m.Assignment') }}</div>
                <div class="assignment-list">
                    <div v-if="loading" class="loading-container">
                        <Spin size="large" />
                        <p>{{ $t('m.Loading') }}</p>
                    </div>
                    <div v-else>
                        <div v-if="assignments.length === 0" class="no-assignments">
                            <Icon type="ios-book-outline" size="60" />
                            <p>{{ $t('m.No_Assignments') }}</p>
                        </div>
                        <div v-else>
                            <div v-for="assignment in assignments" :key="assignment.id" class="assignment-item">
                                <Card class="assignment-card" @click.native="goToAssignment(assignment)">
                                    <div class="assignment-header">
                                        <h3>{{ assignment.title }}</h3>
                                        <Tag :color="getStatusColor(assignment.status)">{{
                                            getStatusText(assignment.status) }}</Tag>
                                    </div>
                                    <div class="assignment-meta">
                                        <p class="description">{{ assignment.description }}</p>
                                        <div class="assignment-info">
                                            <div class="info-item">
                                                <Icon type="ios-calendar" />
                                                <span>{{ $t('m.Start_Time') }}: {{ assignment.start_time | localtime
                                                    }}</span>
                                            </div>
                                            <div class="info-item">
                                                <Icon type="ios-calendar" />
                                                <span>{{ $t('m.End_Time') }}: {{ assignment.end_time | localtime
                                                    }}</span>
                                            </div>
                                            <div class="info-item">
                                                <Icon type="ios-list" />
                                                <span>{{ $t('m.Problems_Count') }}: {{ assignment.problem_count
                                                    }}</span>
                                            </div>
                                        </div>
                                    </div>
                                </Card>
                            </div>
                        </div>
                    </div>
                </div>
            </Panel>
        </div>
    </div>
</template>

<script>
import api from '@oj/api'
import { mapGetters } from 'vuex'
import moment from 'moment'

export default {
    name: 'Assignment',
    data() {
        return {
            loading: true,
            assignments: []
        }
    },
    mounted() {
        this.getAssignments()
    },
    methods: {
        getAssignments() {
            this.loading = true
            api.getUserAssignments().then(res => {
                this.assignments = res.data.data
                this.loading = false
            }).catch(() => {
                this.loading = false
                this.$error(this.$t('m.Failed_to_get_Assignments'))
            })
        },
        goToAssignment(assignment) {
            this.$router.push({
                name: 'assignment-details',
                params: { assignmentID: assignment.id }
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
.assignment-container {
    margin: 20px auto;
    max-width: 1200px;

    .assignment-content {
        margin: 0 20px;

        .panel-title {
            font-size: 22px;
            font-weight: 600;
            color: #2c3e50;
        }

        .loading-container {
            text-align: center;
            padding: 40px 0;

            p {
                margin-top: 15px;
                color: #666;
            }
        }

        .no-assignments {
            text-align: center;
            padding: 60px 20px;
            color: #999;

            p {
                margin-top: 20px;
                font-size: 18px;
            }
        }

        .assignment-item {
            margin-bottom: 20px;

            .assignment-card {
                cursor: pointer;
                transition: all 0.3s ease;
                border: 1px solid #e8eaec;

                &:hover {
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                    border-color: #40a9ff;
                }

                .assignment-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 15px;

                    h3 {
                        margin: 0;
                        font-size: 18px;
                        color: #2c3e50;
                    }
                }

                .assignment-meta {
                    .description {
                        color: #666;
                        margin-bottom: 15px;
                        line-height: 1.6;
                    }

                    .assignment-info {
                        display: flex;
                        flex-wrap: wrap;
                        gap: 15px;

                        .info-item {
                            display: flex;
                            align-items: center;
                            font-size: 14px;
                            color: #888;

                            i {
                                margin-right: 5px;
                                color: #40a9ff;
                            }
                        }
                    }
                }
            }
        }
    }
}

@media (max-width: 768px) {
    .assignment-container {
        margin: 10px auto;

        .assignment-content {
            margin: 0 10px;

            .assignment-item {
                .assignment-card {
                    .assignment-header {
                        flex-direction: column;
                        align-items: flex-start;

                        h3 {
                            margin-bottom: 10px;
                        }
                    }

                    .assignment-meta {
                        .assignment-info {
                            flex-direction: column;
                            gap: 8px;
                        }
                    }
                }
            }
        }
    }
}
</style>