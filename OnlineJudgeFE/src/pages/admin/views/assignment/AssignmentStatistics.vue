<template>
    <div class="assignment-statistics" v-loading="loading">
        <div class="page-header">
            <el-button icon="el-icon-arrow-left" @click="goBack">返回</el-button>
            <h2>{{ assignment.title }} - 统计详情</h2>
            <el-button icon="el-icon-refresh" @click="refreshData" style="margin-left: auto;">刷新</el-button>
            <el-button icon="el-icon-download" @click="exportData" style="margin-left: 10px;">导出</el-button>
        </div>

        <el-card class="stats-summary-card" shadow="hover">
            <div slot="header" class="card-header">
                <span class="card-title">统计概览</span>
            </div>
            <div class="stats-summary">
                <el-row :gutter="20">
                    <el-col :span="6">
                        <div class="summary-item">
                            <div class="summary-icon bg-blue">
                                <i class="el-icon-user"></i>
                            </div>
                            <div class="summary-text">
                                <p class="summary-value">{{ statistics.total_students }}</p>
                                <p class="summary-label">总学生数</p>
                            </div>
                        </div>
                    </el-col>
                    <el-col :span="6">
                        <div class="summary-item">
                            <div class="summary-icon bg-green">
                                <i class="el-icon-upload"></i>
                            </div>
                            <div class="summary-text">
                                <p class="summary-value">{{ statistics.submitted_students }}</p>
                                <p class="summary-label">已提交学生数</p>
                            </div>
                        </div>
                    </el-col>
                    <el-col :span="6">
                        <div class="summary-item">
                            <div class="summary-icon bg-yellow">
                                <i class="el-icon-check"></i>
                            </div>
                            <div class="summary-text">
                                <p class="summary-value">{{ statistics.completion_rate }}%</p>
                                <p class="summary-label">提交率</p>
                            </div>
                        </div>
                    </el-col>
                    <el-col :span="6">
                        <div class="summary-item">
                            <div class="summary-icon bg-purple">
                                <i class="el-icon-star-off"></i>
                            </div>
                            <div class="summary-text">
                                <p class="summary-value">{{ statistics.average_score }}</p>
                                <p class="summary-label">平均分</p>
                            </div>
                        </div>
                    </el-col>
                </el-row>
            </div>
        </el-card>

        <el-row :gutter="20">
            <el-col :span="12">
                <el-card class="completion-stats-card" shadow="hover">
                    <div slot="header" class="card-header">
                        <span class="card-title">完成情况</span>
                    </div>
                    <div class="completion-stats">
                        <div class="chart-container" ref="completionChart" style="width: 100%; height: 300px;"></div>
                    </div>
                </el-card>
            </el-col>
            <el-col :span="12">
                <el-card class="completion-details-card" shadow="hover">
                    <div slot="header" class="card-header">
                        <span class="card-title">完成详情</span>
                    </div>
                    <div class="completion-details">
                        <div class="detail-item">
                            <div class="detail-label">已完成学生数</div>
                            <div class="detail-value">{{ statistics.completed_students }}</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">未完成学生数</div>
                            <div class="detail-value">{{ statistics.total_students - statistics.completed_students }}
                            </div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">完成百分比</div>
                            <div class="detail-value">{{ statistics.completion_percentage }}%</div>
                        </div>
                        <div class="progress-container">
                            <el-progress :percentage="parseFloat(statistics.completion_percentage)" :stroke-width="20"
                                status="success" :show-text="true" text-inside>
                            </el-progress>
                        </div>
                        <div class="chart-container" ref="completionBarChart"
                            style="width: 100%; height: 200px; margin-top: 20px;"></div>
                    </div>
                </el-card>
            </el-col>
        </el-row>

        <el-card class="additional-stats-card" shadow="hover">
            <div slot="header" class="card-header">
                <span class="card-title">详细统计</span>
            </div>
            <el-row :gutter="20">
                <el-col :span="8">
                    <div class="stat-item">
                        <div class="stat-icon bg-blue">
                            <i class="el-icon-s-custom"></i>
                        </div>
                        <div class="stat-content">
                            <div class="stat-value">{{ statistics.average_submissions_per_student }}</div>
                            <div class="stat-label">人均提交次数</div>
                        </div>
                    </div>
                </el-col>
                <el-col :span="8">
                    <div class="stat-item">
                        <div class="stat-icon bg-green">
                            <i class="el-icon-document-checked"></i>
                        </div>
                        <div class="stat-content">
                            <div class="stat-value">{{ statistics.average_accepted_per_student }}</div>
                            <div class="stat-label">人均通过题数</div>
                        </div>
                    </div>
                </el-col>
                <el-col :span="8">
                    <div class="stat-item">
                        <div class="stat-icon bg-yellow">
                            <i class="el-icon-timer"></i>
                        </div>
                        <div class="stat-content">
                            <div class="stat-value">{{ statistics.average_time_to_complete }}</div>
                            <div class="stat-label">平均完成时间</div>
                        </div>
                    </div>
                </el-col>
            </el-row>
        </el-card>
    </div>
</template>

<script>
import api from '../../api.js'
import * as echarts from 'echarts'

export default {
    name: 'AssignmentStatistics',
    data() {
        return {
            loading: false,
            assignmentId: '',
            assignment: {},
            statistics: {
                total_students: 0,
                submitted_students: 0,
                completion_rate: 0,
                completed_students: 0,
                completion_percentage: 0,
                average_score: 0,
                average_submissions_per_student: 0,
                average_accepted_per_student: 0,
                average_time_to_complete: '0天'
            },
            completionChart: null,
            completionBarChart: null
        }
    },
    created() {
        this.assignmentId = this.$route.params.assignmentId
        this.loadData()
    },
    mounted() {
        // 初始化图表
        this.initCharts()
    },
    beforeDestroy() {
        if (this.completionChart) {
            this.completionChart.dispose()
        }
        if (this.completionBarChart) {
            this.completionBarChart.dispose()
        }
    },
    methods: {
        loadData() {
            this.loading = true
            Promise.all([
                api.getAssignment(this.assignmentId),
                api.getAssignmentDetailedStatistics(this.assignmentId)
            ]).then(responses => {
                this.assignment = responses[0].data.data
                this.statistics = responses[1].data.data
                this.loading = false
                this.$nextTick(() => {
                    this.updateCharts()
                })
            }).catch(() => {
                this.loading = false
                this.$message.error('数据加载失败')
            })
        },
        refreshData() {
            this.loadData()
            this.$message.success('数据刷新成功')
        },
        getAssignmentDetail() {
            api.getAssignment(this.assignmentId).then(res => {
                this.assignment = res.data.data
            })
        },
        getStatistics() {
            api.getAssignmentDetailedStatistics(this.assignmentId).then(res => {
                this.statistics = res.data.data
                this.$nextTick(() => {
                    this.updateCharts()
                })
            })
        },
        initCharts() {
            // 初始化完成情况图表
            this.completionChart = echarts.init(this.$refs.completionChart)
            this.completionBarChart = echarts.init(this.$refs.completionBarChart)

            // 监听窗口大小变化
            window.addEventListener('resize', this.resizeCharts)
        },
        resizeCharts() {
            if (this.completionChart) {
                this.completionChart.resize()
            }
            if (this.completionBarChart) {
                this.completionBarChart.resize()
            }
        },
        updateCharts() {
            // 更新完成情况饼图
            if (this.completionChart) {
                const option = {
                    title: {
                        text: '学生完成情况',
                        left: 'center',
                        textStyle: {
                            fontSize: 16,
                            fontWeight: 'normal'
                        }
                    },
                    tooltip: {
                        trigger: 'item',
                        formatter: '{a} <br/>{b}: {c} ({d}%)'
                    },
                    legend: {
                        orient: 'horizontal',
                        bottom: 0
                    },
                    series: [
                        {
                            name: '完成情况',
                            type: 'pie',
                            radius: ['40%', '70%'],
                            avoidLabelOverlap: false,
                            itemStyle: {
                                borderRadius: 10,
                                borderColor: '#fff',
                                borderWidth: 2
                            },
                            label: {
                                show: false,
                                position: 'center'
                            },
                            emphasis: {
                                label: {
                                    show: true,
                                    fontSize: '14',
                                    fontWeight: 'bold',
                                    formatter: '{b}\n{d}%'
                                }
                            },
                            labelLine: {
                                show: false
                            },
                            data: [
                                {
                                    value: this.statistics.completed_students,
                                    name: '已完成',
                                    itemStyle: { color: '#67C23A' }
                                },
                                {
                                    value: this.statistics.total_students - this.statistics.completed_students,
                                    name: '未完成',
                                    itemStyle: { color: '#F56C6C' }
                                }
                            ]
                        }
                    ]
                }
                this.completionChart.setOption(option)
            }

            // 更新完成情况柱状图
            if (this.completionBarChart) {
                const option = {
                    tooltip: {
                        trigger: 'axis',
                        axisPointer: {
                            type: 'shadow'
                        }
                    },
                    grid: {
                        left: '3%',
                        right: '4%',
                        bottom: '3%',
                        containLabel: true
                    },
                    xAxis: {
                        type: 'category',
                        data: ['已完成', '未完成'],
                        axisTick: {
                            alignWithLabel: true
                        }
                    },
                    yAxis: {
                        type: 'value'
                    },
                    series: [
                        {
                            name: '学生数',
                            type: 'bar',
                            barWidth: '60%',
                            data: [
                                {
                                    value: this.statistics.completed_students,
                                    itemStyle: { color: '#67C23A' }
                                },
                                {
                                    value: this.statistics.total_students - this.statistics.completed_students,
                                    itemStyle: { color: '#F56C6C' }
                                }
                            ]
                        }
                    ]
                }
                this.completionBarChart.setOption(option)
            }
        },
        goBack() {
            this.$router.go(-1)
        },
        exportData() {
            // 构造CSV内容
            let csvContent = '\uFEFF'; // 添加BOM以支持中文

            // 作业信息
            csvContent += '作业统计报告\n';
            csvContent += `作业名称: ${this.assignment.title}\n`;
            csvContent += `创建者: ${this.assignment.creator_username}\n`;
            csvContent += `开始时间: ${this.assignment.start_time}\n`;
            csvContent += `结束时间: ${this.assignment.end_time}\n`;
            csvContent += '\n';

            // 统计数据
            csvContent += '统计数据\n';
            csvContent += '总学生数,已提交学生数,提交率,平均分,已完成学生数,完成百分比,人均提交次数,人均通过题数,平均完成时间\n';
            csvContent += `${this.statistics.total_students},${this.statistics.submitted_students},${this.statistics.completion_rate}%,${this.statistics.average_score},${this.statistics.completed_students},${this.statistics.completion_percentage}%,${this.statistics.average_submissions_per_student},${this.statistics.average_accepted_per_student},${this.statistics.average_time_to_complete}\n`;

            // 创建并下载CSV文件
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);

            const fileName = `作业统计_${this.assignment.title}_${new Date().toISOString().slice(0, 10)}.csv`;
            link.setAttribute('href', url);
            link.setAttribute('download', fileName);
            link.style.visibility = 'hidden';

            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            this.$message.success('统计导出成功');
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
    flex: 1;
}

.card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.card-title {
    font-weight: bold;
    font-size: 16px;
    color: #303133;
}

.stats-summary-card,
.completion-stats-card,
.completion-details-card,
.additional-stats-card {
    margin-bottom: 20px;
    border-radius: 8px;
}

.summary-item {
    display: flex;
    align-items: center;
    padding: 20px;
    border-radius: 8px;
    transition: all 0.3s ease;
}

.summary-item:hover {
    transform: translateY(-3px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.summary-icon {
    width: 50px;
    height: 50px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    color: white;
    margin-right: 15px;
    flex-shrink: 0;
}

.summary-text {
    flex: 1;
}

.summary-value {
    font-size: 24px;
    font-weight: bold;
    margin: 0 0 5px 0;
    color: #303133;
}

.summary-label {
    margin: 0;
    color: #909399;
    font-size: 14px;
}

.bg-blue {
    background: linear-gradient(135deg, #409EFF, #1a73e8);
}

.bg-green {
    background: linear-gradient(135deg, #67C23A, #43a047);
}

.bg-yellow {
    background: linear-gradient(135deg, #E6A23C, #ef9a2a);
}

.bg-purple {
    background: linear-gradient(135deg, #909399, #7b7b7b);
}

.completion-details {
    padding: 20px;
}

.detail-item {
    display: flex;
    justify-content: space-between;
    margin-bottom: 15px;
    padding: 10px 0;
    border-bottom: 1px solid #f0f0f0;
}

.detail-label {
    font-size: 16px;
    color: #606266;
}

.detail-value {
    font-size: 18px;
    font-weight: bold;
    color: #303133;
}

.progress-container {
    margin: 20px 0;
}

.stat-item {
    display: flex;
    align-items: center;
    padding: 20px;
    border-radius: 8px;
    transition: all 0.3s ease;
    background-color: #f5f7fa;
    margin-bottom: 20px;
}

.stat-item:hover {
    transform: translateY(-3px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.stat-icon {
    width: 50px;
    height: 50px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    color: white;
    margin-right: 15px;
    flex-shrink: 0;
}

.stat-content {
    flex: 1;
}

.stat-value {
    font-size: 24px;
    font-weight: bold;
    margin: 0 0 5px 0;
    color: #303133;
}

.stat-label {
    margin: 0;
    color: #909399;
    font-size: 14px;
}
</style>