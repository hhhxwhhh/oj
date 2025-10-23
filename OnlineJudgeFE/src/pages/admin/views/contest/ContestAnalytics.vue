<template>
    <div class="contest-analytics">
        <div class="header">
            <h2>{{ $t('m.Contest_Analytics') }} - {{ contestInfo.title }}</h2>
            <el-button type="primary" @click="refreshData" :loading="loading">
                <i class="el-icon-refresh"></i> {{ $t('m.Refresh') }}
            </el-button>
        </div>

        <!-- 竞赛基本信息 -->
        <el-row :gutter="20" class="info-cards">
            <el-col :span="6">
                <el-card class="info-card">
                    <div class="info-card-content">
                        <div class="info-card-icon" style="background-color: #E8F4FD;">
                            <i class="el-icon-user info-icon" style="color: #1890FF;"></i>
                        </div>
                        <div class="info-card-text">
                            <div class="info-card-title">{{ $t('m.Participants') }}</div>
                            <div class="info-card-value">{{ contestInfo.participants_count }}</div>
                        </div>
                    </div>
                </el-card>
            </el-col>
            <el-col :span="6">
                <el-card class="info-card">
                    <div class="info-card-content">
                        <div class="info-card-icon" style="background-color: #EFF9F4;">
                            <i class="el-icon-document-checked info-icon" style="color: #52C41A;"></i>
                        </div>
                        <div class="info-card-text">
                            <div class="info-card-title">{{ $t('m.Total_Submissions') }}</div>
                            <div class="info-card-value">{{ submissionStats.total }}</div>
                        </div>
                    </div>
                </el-card>
            </el-col>
            <el-col :span="6">
                <el-card class="info-card">
                    <div class="info-card-content">
                        <div class="info-card-icon" style="background-color: #FEF5E9;">
                            <i class="el-icon-check info-icon" style="color: #FA8C16;"></i>
                        </div>
                        <div class="info-card-text">
                            <div class="info-card-title">{{ $t('m.Accepted_Submissions') }}</div>
                            <div class="info-card-value">{{ submissionStats.accepted }}</div>
                        </div>
                    </div>
                </el-card>
            </el-col>
            <el-col :span="6">
                <el-card class="info-card">
                    <div class="info-card-content">
                        <div class="info-card-icon" style="background-color: #F0F2F5;">
                            <i class="el-icon-data-analysis info-icon" style="color: #722ED1;"></i>
                        </div>
                        <div class="info-card-text">
                            <div class="info-card-title">{{ $t('m.Acceptance_Rate') }}</div>
                            <div class="info-card-value">{{ submissionStats.acceptance_rate }}%</div>
                        </div>
                    </div>
                </el-card>
            </el-col>
        </el-row>

        <!-- 图表区域 -->
        <el-row :gutter="20" class="charts">
            <el-col :span="16">
                <el-card class="chart-card">
                    <div slot="header" class="chart-header">
                        <span>{{ $t('m.Submission_Trend') }}</span>
                    </div>
                    <div class="chart-container">
                        <v-chart :options="timeSeriesChartOptions" autoresize />
                    </div>
                </el-card>
            </el-col>
            <el-col :span="8">
                <el-card class="chart-card">
                    <div slot="header" class="chart-header">
                        <span>{{ $t('m.Score_Distribution') }}</span>
                    </div>
                    <div class="chart-container">
                        <v-chart :options="scoreDistributionChartOptions" autoresize />
                    </div>
                </el-card>
            </el-col>
        </el-row>

        <!-- 排名和题目统计 -->
        <el-row :gutter="20" class="tables">
            <el-col :span="12">
                <el-card class="table-card">
                    <div slot="header" class="table-header">
                        <span>{{ $t('m.Top_Users') }}</span>
                    </div>
                    <el-table :data="rankData" style="width: 100%" max-height="400">
                        <el-table-column prop="rank" :label="$t('m.Rank')" width="60"></el-table-column>
                        <el-table-column :label="$t('m.User')">
                            <template slot-scope="scope">
                                <div class="user-info">
                                    <img :src="scope.row.avatar || '/public/avatar/default.png'" class="user-avatar" />
                                    <div class="user-details">
                                        <div class="username">{{ scope.row.username }}</div>
                                        <div class="real-name" v-if="scope.row.real_name">{{ scope.row.real_name }}
                                        </div>
                                    </div>
                                </div>
                            </template>
                        </el-table-column>
                        <el-table-column v-if="contestInfo.rule_type === 'ACM'" prop="accepted_number"
                            :label="$t('m.Accepted')" width="100"></el-table-column>
                        <el-table-column v-if="contestInfo.rule_type === 'ACM'" prop="total_time"
                            :label="$t('m.Total_Time')" width="120"></el-table-column>
                        <el-table-column v-if="contestInfo.rule_type === 'OI'" prop="total_score"
                            :label="$t('m.Total_Score')" width="120"></el-table-column>
                        <el-table-column prop="submission_number" :label="$t('m.Submissions')"
                            width="120"></el-table-column>
                    </el-table>
                </el-card>
            </el-col>
            <el-col :span="12">
                <el-card class="table-card">
                    <div slot="header" class="table-header">
                        <span>{{ $t('m.Problem_Statistics') }}</span>
                    </div>
                    <el-table :data="problemStats" style="width: 100%" max-height="400">
                        <el-table-column prop="problem_title" :label="$t('m.Problem')"></el-table-column>
                        <el-table-column prop="total_submissions" :label="$t('m.Total_Submissions')"
                            width="120"></el-table-column>
                        <el-table-column prop="accepted_submissions" :label="$t('m.Accepted')"
                            width="100"></el-table-column>
                        <el-table-column prop="acceptance_rate" :label="$t('m.Acceptance_Rate')" width="120">
                            <template slot-scope="scope">
                                <el-progress :percentage="scope.row.acceptance_rate"
                                    :status="scope.row.acceptance_rate >= 50 ? 'success' : 'exception'"
                                    :show-text="false" :stroke-width="10">
                                </el-progress>
                                <div class="rate-text">{{ scope.row.acceptance_rate }}%</div>
                            </template>
                        </el-table-column>
                    </el-table>
                </el-card>
            </el-col>
        </el-row>
    </div>
</template>

<script>
import api from '../../api'
import 'echarts/lib/chart/line'
import 'echarts/lib/chart/bar'
import 'echarts/lib/component/tooltip'
import 'echarts/lib/component/title'
import 'echarts/lib/component/legend'

export default {
    name: 'ContestAnalytics',
    data() {
        return {
            loading: false,
            contestId: '',
            contestInfo: {
                id: 0,
                title: '',
                participants_count: 0,
                rule_type: 'ACM'
            },
            submissionStats: {
                total: 0,
                accepted: 0,
                acceptance_rate: 0
            },
            rankData: [],
            problemStats: [],
            timeSeriesData: [],
            scoreDistribution: [],
            timeSeriesChartOptions: {
                title: {
                    text: this.$t('m.Submission_Trend')
                },
                tooltip: {
                    trigger: 'axis'
                },
                xAxis: {
                    type: 'category',
                    data: []
                },
                yAxis: {
                    type: 'value'
                },
                series: [{
                    data: [],
                    type: 'line',
                    smooth: true,
                    areaStyle: {}
                }]
            },
            scoreDistributionChartOptions: {
                title: {
                    text: this.$t('m.Score_Distribution')
                },
                tooltip: {
                    trigger: 'axis'
                },
                xAxis: {
                    type: 'category',
                    data: []
                },
                yAxis: {
                    type: 'value'
                },
                series: [{
                    data: [],
                    type: 'bar'
                }]
            }
        }
    },
    created() {
        this.contestId = this.$route.query.contestId
        if (this.contestId) {
            this.fetchAnalyticsData()
        } else {
            this.$router.push({ name: 'contest-list' })
        }
    },
    methods: {
        async fetchAnalyticsData() {
            this.loading = true
            try {
                const res = await api.getContestAnalytics(this.contestId)
                const data = res.data.data

                this.contestInfo = data.contest_info
                this.submissionStats = data.submission_stats
                this.rankData = data.rank_data
                this.problemStats = data.problem_stats
                this.timeSeriesData = data.time_series_data
                this.scoreDistribution = data.score_distribution

                // 更新时间序列图表
                this.timeSeriesChartOptions.xAxis.data = this.timeSeriesData.map(item => item.time)
                this.timeSeriesChartOptions.series[0].data = this.timeSeriesData.map(item => item.count)

                // 更新分数分布图表
                this.scoreDistributionChartOptions.xAxis.data = this.scoreDistribution.map(item => item.range)
                this.scoreDistributionChartOptions.series[0].data = this.scoreDistribution.map(item => item.count)
            } catch (err) {
                this.$error(this.$t('m.Failed_to_get_analytics_data'))
            } finally {
                this.loading = false
            }
        },
        refreshData() {
            this.fetchAnalyticsData()
        }
    }
}
</script>

<style scoped lang="less">
.contest-analytics {
    padding: 20px;

    .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;

        h2 {
            margin: 0;
            color: #303133;
        }
    }

    .info-cards {
        margin-bottom: 20px;

        .info-card {
            border-radius: 8px;
            box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);

            .info-card-content {
                display: flex;
                align-items: center;

                .info-card-icon {
                    width: 50px;
                    height: 50px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin-right: 15px;

                    .info-icon {
                        font-size: 24px;
                    }
                }

                .info-card-text {
                    .info-card-title {
                        font-size: 14px;
                        color: #909399;
                        margin-bottom: 5px;
                    }

                    .info-card-value {
                        font-size: 24px;
                        font-weight: bold;
                        color: #303133;
                    }
                }
            }
        }
    }

    .charts {
        margin-bottom: 20px;

        .chart-card {
            border-radius: 8px;
            box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);

            .chart-header {
                font-size: 16px;
                font-weight: 500;
                color: #303133;
            }

            .chart-container {
                height: 300px;
            }
        }
    }

    .tables {
        .table-card {
            border-radius: 8px;
            box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);

            .table-header {
                font-size: 16px;
                font-weight: 500;
                color: #303133;
            }

            .user-info {
                display: flex;
                align-items: center;

                .user-avatar {
                    width: 36px;
                    height: 36px;
                    border-radius: 50%;
                    margin-right: 10px;
                    object-fit: cover;
                }

                .user-details {
                    .username {
                        font-weight: 500;
                        color: #303133;
                    }

                    .real-name {
                        font-size: 12px;
                        color: #909399;
                    }
                }
            }

            .rate-text {
                text-align: center;
                font-size: 12px;
                color: #909399;
                margin-top: 5px;
            }
        }
    }
}

.echarts {
    width: 100%;
    height: 100%;
}
</style>