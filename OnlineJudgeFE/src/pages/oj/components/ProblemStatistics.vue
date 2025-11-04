<template>
    <div class="problem-statistics">
        <Panel :padding="15" shadow>
            <div slot="title" class="card-title">
                <Icon type="ios-analytics" />
                题目统计信息
            </div>

            <div v-if="loading" class="loading">
                <Spin size="large"></Spin>
                <p class="loading-text">正在加载统计信息...</p>
            </div>

            <div v-else-if="statisticsData" class="statistics-content">
                <div class="statistics-overview">
                    <div class="overview-item">
                        <div class="overview-value">{{ statisticsData.total_submissions }}</div>
                        <div class="overview-label">总提交数</div>
                    </div>

                    <div class="overview-item">
                        <div class="overview-value">{{ statisticsData.accepted_submissions }}</div>
                        <div class="overview-label">通过数</div>
                    </div>

                    <div class="overview-item">
                        <div class="overview-value">{{ statisticsData.acceptance_rate }}%</div>
                        <div class="overview-label">通过率</div>
                    </div>
                </div>

                <div class="chart-container">
                    <ECharts :options="chartOptions" :initOptions="{ width: '100%', height: '300px' }"></ECharts>
                </div>

                <div class="detail-stats">
                    <div class="stat-item" v-for="(value, key) in statisticsData.detail" :key="key">
                        <div class="stat-label">{{ getJudgeStatusName(key) }}</div>
                        <div class="stat-value">{{ value }}</div>
                        <div class="stat-bar">
                            <div class="stat-bar-fill" :style="{
                                width: (value / statisticsData.total_submissions * 100) + '%',
                                backgroundColor: getJudgeStatusColor(key)
                            }"></div>
                        </div>
                    </div>
                </div>
            </div>

            <div v-else class="no-data">
                <Icon type="ios-alert-outline" size="40" class="no-data-icon" />
                <p>暂无统计信息</p>
            </div>
        </Panel>
    </div>
</template>

<script>
import Panel from './Panel.vue'
import ECharts from 'vue-echarts/components/ECharts.vue'
import 'echarts/lib/chart/pie'
import 'echarts/lib/component/title'
import 'echarts/lib/component/tooltip'
import 'echarts/lib/component/legend'
import { JUDGE_STATUS } from '@/utils/constants'

export default {
    name: 'ProblemStatistics',
    components: {
        Panel,
        ECharts
    },
    props: {
        problem: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            chartOptions: {}
        }
    },
    computed: {
        loading() {
            return !this.problem;
        },
        statisticsData() {
            if (!this.problem || !this.problem.statistic_info) {
                return null;
            }

            const statistic_info = this.problem.statistic_info;
            const total_submissions = this.problem.submission_number;
            const accepted_submissions = this.problem.accepted_number;
            const acceptance_rate = total_submissions > 0 ? (accepted_submissions / total_submissions * 100).toFixed(1) : 0;

            return {
                total_submissions,
                accepted_submissions,
                acceptance_rate,
                detail: statistic_info
            };
        }
    },
    watch: {
        problem: {
            handler() {
                if (this.statisticsData) {
                    this.generateChartOptions();
                }
            },
            immediate: true
        }
    },
    methods: {
        generateChartOptions() {
            if (!this.statisticsData) return

            const data = []
            Object.keys(this.statisticsData.detail).forEach(key => {
                if (this.statisticsData.detail[key] > 0) {
                    data.push({
                        name: this.getJudgeStatusName(key),
                        value: this.statisticsData.detail[key],
                        itemStyle: { color: this.getJudgeStatusColor(key) }
                    })
                }
            })

            // 添加AC和WA数据
            data.push({
                name: 'Accepted',
                value: this.statisticsData.accepted_submissions,
                itemStyle: { color: this.getJudgeStatusColor('0') }
            })

            const waCount = this.statisticsData.total_submissions - this.statisticsData.accepted_submissions
            if (waCount > 0) {
                data.push({
                    name: 'Wrong Answer',
                    value: waCount,
                    itemStyle: { color: this.getJudgeStatusColor('-1') }
                })
            }

            this.chartOptions = {
                tooltip: {
                    trigger: 'item',
                    formatter: '{a} <br/>{b}: {c} ({d}%)'
                },
                legend: {
                    orient: 'vertical',
                    left: 'left',
                    data: data.map(item => item.name)
                },
                series: [
                    {
                        name: '提交统计',
                        type: 'pie',
                        radius: ['40%', '70%'],
                        avoidLabelOverlap: false,
                        label: {
                            show: false,
                            position: 'center'
                        },
                        emphasis: {
                            label: {
                                show: true,
                                fontSize: '14',
                                fontWeight: 'bold'
                            }
                        },
                        labelLine: {
                            show: false
                        },
                        data: data
                    }
                ]
            }
        },

        getJudgeStatusName(statusCode) {
            return JUDGE_STATUS[statusCode] ? JUDGE_STATUS[statusCode].name : 'Unknown'
        },

        getJudgeStatusColor(statusCode) {
            return JUDGE_STATUS[statusCode] ? JUDGE_STATUS[statusCode].color : '#909399'
        }
    }
}
</script>

<style scoped lang="less">
.problem-statistics {
    margin-top: 20px;

    .card-title {
        font-weight: 500;
    }

    .loading {
        text-align: center;
        padding: 40px 0;

        .loading-text {
            margin-top: 15px;
            color: #808695;
        }
    }

    .statistics-content {
        .statistics-overview {
            display: flex;
            justify-content: space-around;
            margin-bottom: 20px;
            padding: 15px 0;
            border-bottom: 1px solid #e8eaec;

            .overview-item {
                text-align: center;

                .overview-value {
                    font-size: 24px;
                    font-weight: 600;
                    color: #2d8cf0;
                }

                .overview-label {
                    font-size: 14px;
                    color: #808695;
                    margin-top: 5px;
                }
            }
        }

        .chart-container {
            height: 300px;
            margin-bottom: 20px;
        }

        .detail-stats {
            .stat-item {
                margin-bottom: 15px;
                padding: 10px;
                border-radius: 4px;
                background-color: #fafafa;
                border: 1px solid #f0f0f0;

                .stat-label {
                    font-weight: 500;
                    margin-bottom: 5px;
                    color: #515a6e;
                }

                .stat-value {
                    font-weight: 600;
                    margin-bottom: 5px;
                    color: #2d8cf0;
                }

                .stat-bar {
                    height: 6px;
                    background-color: #e8eaec;
                    border-radius: 3px;
                    overflow: hidden;

                    .stat-bar-fill {
                        height: 100%;
                        border-radius: 3px;
                        transition: width 0.3s ease;
                    }
                }
            }
        }
    }

    .no-data {
        text-align: center;
        padding: 40px 0;

        .no-data-icon {
            color: #c5c8ce;
            margin-bottom: 15px;
        }

        p {
            font-size: 15px;
            color: #808695;
        }
    }
}

@media screen and (max-width: 768px) {
    .problem-statistics {
        .statistics-content {
            .statistics-overview {
                flex-direction: column;
                gap: 15px;
                align-items: center;

                .overview-item {
                    width: 100%;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 10px 15px;
                    background: #f8faff;
                    border-radius: 6px;
                    border: 1px solid #e0e0e0;

                    .overview-value {
                        font-size: 20px;
                    }

                    .overview-label {
                        margin-top: 0;
                    }
                }
            }
        }
    }
}
</style>