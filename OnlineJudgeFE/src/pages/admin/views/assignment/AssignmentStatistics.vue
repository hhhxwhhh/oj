<template>
    <div class="assignment-statistics">
        <div class="page-header">
            <el-button icon="el-icon-arrow-left" @click="goBack">返回</el-button>
            <h2>{{ assignment.title }} - 统计详情</h2>
        </div>

        <el-card class="stats-summary-card">
            <div class="stats-summary">
                <h3>统计概览</h3>
                <el-row :gutter="20">
                    <el-col :span="6">
                        <div class="summary-item">
                            <p class="summary-value">{{ statistics.total_students }}</p>
                            <p class="summary-label">总学生数</p>
                        </div>
                    </el-col>
                    <el-col :span="6">
                        <div class="summary-item">
                            <p class="summary-value">{{ statistics.submitted_students }}</p>
                            <p class="summary-label">已提交学生数</p>
                        </div>
                    </el-col>
                    <el-col :span="6">
                        <div class="summary-item">
                            <p class="summary-value">{{ statistics.completion_rate }}%</p>
                            <p class="summary-label">提交率</p>
                        </div>
                    </el-col>
                    <el-col :span="6">
                        <div class="summary-item">
                            <p class="summary-value">{{ statistics.average_score }}</p>
                            <p class="summary-label">平均分</p>
                        </div>
                    </el-col>
                </el-row>
            </div>
        </el-card>

        <el-card class="completion-stats-card">
            <div class="completion-stats">
                <h3>完成情况</h3>
                <el-row :gutter="20">
                    <el-col :span="12">
                        <div class="chart-container">
                            <canvas ref="completionChart" height="300"></canvas>
                        </div>
                    </el-col>
                    <el-col :span="12">
                        <div class="completion-details">
                            <p>已完成学生数: {{ statistics.completed_students }}</p>
                            <p>完成百分比: {{ statistics.completion_percentage }}%</p>
                            <el-progress :percentage="parseFloat(statistics.completion_percentage)" :stroke-width="20"
                                status="success">
                            </el-progress>
                        </div>
                    </el-col>
                </el-row>
            </div>
        </el-card>
    </div>
</template>

<script>
import api from '../../api.js'
import Chart from 'chart.js'

export default {
    name: 'AssignmentStatistics',
    data() {
        return {
            assignmentId: '',
            assignment: {},
            statistics: {
                total_students: 0,
                submitted_students: 0,
                completion_rate: 0,
                completed_students: 0,
                completion_percentage: 0,
                average_score: 0
            },
            completionChart: null
        }
    },
    created() {
        this.assignmentId = this.$route.params.assignmentId
        this.getAssignmentDetail()
        this.getStatistics()
    },
    beforeDestroy() {
        if (this.completionChart) {
            this.completionChart.destroy()
        }
    },
    methods: {
        getAssignmentDetail() {
            api.getAssignment(this.assignmentId).then(res => {
                this.assignment = res.data.data
            })
        },
        getStatistics() {
            api.getAssignmentDetailedStatistics(this.assignmentId).then(res => {
                this.statistics = res.data.data
                this.$nextTick(() => {
                    this.renderCompletionChart()
                })
            })
        },
        renderCompletionChart() {
            const ctx = this.$refs.completionChart.getContext('2d')

            if (this.completionChart) {
                this.completionChart.destroy()
            }

            this.completionChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['已完成', '未完成'],
                    datasets: [{
                        data: [
                            this.statistics.completed_students,
                            this.statistics.total_students - this.statistics.completed_students
                        ],
                        backgroundColor: [
                            '#42b983',
                            '#e4e7ed'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    legend: {
                        position: 'bottom'
                    },
                    tooltips: {
                        callbacks: {
                            label: function (tooltipItem, data) {
                                const dataset = data.datasets[tooltipItem.datasetIndex];
                                const total = dataset.data.reduce(function (previousValue, currentValue) {
                                    return previousValue + currentValue;
                                });
                                const currentValue = dataset.data[tooltipItem.index];
                                const percentage = Math.floor(((currentValue / total) * 100) + 0.5);
                                return data.labels[tooltipItem.index] + ': ' + currentValue + ' (' + percentage + '%)';
                            }
                        }
                    }
                }
            })
        },
        goBack() {
            this.$router.go(-1)
        }
    }
}
</script>

<style scoped>
.assignment-statistics {
    margin: 20px;
}

.page-header {
    display: flex;
    align-items: center;
    margin-bottom: 20px;
}

.page-header h2 {
    margin-left: 15px;
}

.stats-summary-card,
.completion-stats-card {
    margin-bottom: 20px;
}

.stats-summary {
    padding: 10px 0;
}

.summary-item {
    text-align: center;
}

.summary-value {
    font-size: 24px;
    font-weight: bold;
    margin: 0;
}

.summary-label {
    margin: 5px 0 0 0;
    color: #999;
}

.completion-stats {
    padding: 10px 0;
}

.chart-container {
    position: relative;
    height: 300px;
}

.completion-details {
    display: flex;
    flex-direction: column;
    justify-content: center;
    height: 300px;
}

.completion-details p {
    font-size: 16px;
    margin-bottom: 15px;
}
</style>