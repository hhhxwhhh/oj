<template>
    <div class="assignment-dashboard" v-loading="loading">
        <div class="page-header">
            <el-button icon="el-icon-arrow-left" @click="goBack">返回</el-button>
            <h2>{{ assignment.title }} - 分析仪表板</h2>
            <el-button icon="el-icon-download" @click="exportData" style="margin-left: auto;">导出数据</el-button>
        </div>

        <div v-if="!loading">
            <!-- 统计概览卡片 -->
            <el-row :gutter="20" class="summary-cards">
                <el-col :span="6">
                    <el-card class="summary-card" shadow="hover">
                        <div class="summary-content">
                            <div class="summary-icon bg-blue">
                                <i class="el-icon-user"></i>
                            </div>
                            <div class="summary-text">
                                <p class="summary-value">{{ summary.total_students }}</p>
                                <p class="summary-label">总学生数</p>
                            </div>
                        </div>
                    </el-card>
                </el-col>
                <el-col :span="6">
                    <el-card class="summary-card" shadow="hover">
                        <div class="summary-content">
                            <div class="summary-icon bg-green">
                                <i class="el-icon-upload"></i>
                            </div>
                            <div class="summary-text">
                                <p class="summary-value">{{ summary.submitted_students }}</p>
                                <p class="summary-label">已提交学生</p>
                            </div>
                        </div>
                    </el-card>
                </el-col>
                <el-col :span="6">
                    <el-card class="summary-card" shadow="hover">
                        <div class="summary-content">
                            <div class="summary-icon bg-yellow">
                                <i class="el-icon-star-on"></i>
                            </div>
                            <div class="summary-text">
                                <p class="summary-value">{{ summary.average_score }}</p>
                                <p class="summary-label">平均分</p>
                            </div>
                        </div>
                    </el-card>
                </el-col>
                <el-col :span="6">
                    <el-card class="summary-card" shadow="hover">
                        <div class="summary-content">
                            <div class="summary-icon bg-purple">
                                <i class="el-icon-check"></i>
                            </div>
                            <div class="summary-text">
                                <p class="summary-value">{{ summary.completion_percentage }}%</p>
                                <p class="summary-label">完成率</p>
                            </div>
                        </div>
                    </el-card>
                </el-col>
            </el-row>

            <!-- 图表区域 -->
            <el-row :gutter="20" class="chart-section">
                <el-col :span="12">
                    <el-card class="chart-card" shadow="hover">
                        <div slot="header" class="card-header">
                            <span class="card-title">题目难度分析</span>
                        </div>
                        <div ref="difficultyChart" class="chart-container"></div>
                    </el-card>
                </el-col>
                <el-col :span="12">
                    <el-card class="chart-card" shadow="hover">
                        <div slot="header" class="card-header">
                            <span class="card-title">学生表现趋势</span>
                        </div>
                        <div ref="trendChart" class="chart-container"></div>
                    </el-card>
                </el-col>
            </el-row>

            <!-- 排名和统计数据 -->
            <el-row :gutter="20" class="data-section">
                <el-col :span="12">
                    <el-card class="data-card" shadow="hover">
                        <div slot="header" class="card-header">
                            <span class="card-title">表现最好的学生（Top 10）</span>
                        </div>
                        <el-table :data="topStudents" style="width: 100%" stripe
                            :header-cell-style="{ background: '#f5f7fa' }">
                            <el-table-column prop="student_username" label="用户名" width="120"></el-table-column>
                            <el-table-column prop="student_real_name" label="姓名" width="120"></el-table-column>
                            <el-table-column prop="total_score" label="总分" width="100" sortable
                                align="center"></el-table-column>
                            <el-table-column prop="solved_problems" label="解决题目数" width="120" sortable
                                align="center"></el-table-column>
                            <el-table-column prop="completion_rate" label="完成率(%)" width="120" sortable align="center">
                                <template slot-scope="scope">
                                    <el-progress :percentage="parseFloat(scope.row.completion_rate)" :show-text="false"
                                        :stroke-width="10">
                                    </el-progress>
                                    <div class="completion-text">{{ scope.row.completion_rate }}%</div>
                                </template>
                            </el-table-column>
                        </el-table>
                    </el-card>
                </el-col>
                <el-col :span="12">
                    <el-card class="data-card" shadow="hover">
                        <div slot="header" class="card-header">
                            <span class="card-title">题目统计</span>
                        </div>
                        <el-table :data="problemStats" style="width: 100%" stripe
                            :header-cell-style="{ background: '#f5f7fa' }">
                            <el-table-column prop="problem_id" label="题目ID" width="100"
                                align="center"></el-table-column>
                            <el-table-column prop="problem_title" label="题目名称" min-width="150"
                                show-overflow-tooltip></el-table-column>
                            <el-table-column prop="acceptance_rate" label="通过率(%)" width="120" sortable align="center">
                                <template slot-scope="scope">
                                    <el-tag :type="getAcceptanceRateType(scope.row.acceptance_rate)">
                                        {{ scope.row.acceptance_rate }}%
                                    </el-tag>
                                </template>
                            </el-table-column>
                            <el-table-column prop="average_score" label="平均分" width="100" sortable align="center">
                                <template slot-scope="scope">
                                    <span :class="getScoreClass(scope.row.average_score)">{{ scope.row.average_score
                                    }}</span>
                                </template>
                            </el-table-column>
                        </el-table>
                    </el-card>
                </el-col>
            </el-row>
        </div>
    </div>
</template>

<script>
import api from '../../api.js'
import * as echarts from 'echarts'

export default {
    name: 'AssignmentDashboard',
    data() {
        return {
            loading: true,
            assignmentId: '',
            assignment: {},
            summary: {
                total_students: 0,
                submitted_students: 0,
                average_score: 0,
                completion_percentage: 0
            },
            difficultyStats: [],
            trendData: [],
            topStudents: [],
            problemStats: [],
            difficultyChart: null,
            trendChart: null
        }
    },
    created() {
        this.assignmentId = this.$route.params.assignmentId
        this.loadData()
    },
    mounted() {
        this.$nextTick(() => {
            this.initCharts()
        })
    },
    beforeDestroy() {
        if (this.difficultyChart) {
            this.difficultyChart.dispose()
        }
        if (this.trendChart) {
            this.trendChart.dispose()
        }
    },
    methods: {
        loadData() {
            this.loading = true
            Promise.all([
                api.getAssignment(this.assignmentId),
                api.getAssignmentDetailedStatistics(this.assignmentId),
                api.getAssignmentProblemDifficultyStatistics(this.assignmentId),
                api.getAssignmentStudentPerformanceTrend(this.assignmentId),
                api.getAssignmentTopPerformingStudents(this.assignmentId),
                api.getAssignmentProblemStatistics(this.assignmentId)
            ]).then(responses => {
                this.assignment = responses[0].data.data
                this.summary = responses[1].data.data
                this.difficultyStats = responses[2].data.data
                this.trendData = responses[3].data.data
                this.topStudents = responses[4].data.data
                this.problemStats = responses[5].data.data

                this.loading = false
                this.$nextTick(() => {
                    this.updateCharts()
                })
            }).catch(() => {
                this.loading = false
                this.$message.error('数据加载失败')
            })
        },
        initCharts() {
            // 确保元素存在再初始化图表
            if (this.$refs.difficultyChart) {
                this.difficultyChart = echarts.init(this.$refs.difficultyChart)
            }
            if (this.$refs.trendChart) {
                this.trendChart = echarts.init(this.$refs.trendChart)
            }

            // 监听窗口大小变化，重新调整图表大小
            window.addEventListener('resize', this.resizeCharts)
        },
        resizeCharts() {
            if (this.difficultyChart) {
                this.difficultyChart.resize()
            }
            if (this.trendChart) {
                this.trendChart.resize()
            }
        },
        updateCharts() {
            this.updateDifficultyChart()
            this.updateTrendChart()
        },
        updateDifficultyChart() {
            if (this.difficultyChart && this.difficultyStats.length > 0) {
                const difficulties = this.difficultyStats.map(item => item.difficulty)
                const acceptanceRates = this.difficultyStats.map(item => item.acceptance_rate)
                const avgScores = this.difficultyStats.map(item => item.average_score)

                const option = {
                    tooltip: {
                        trigger: 'axis',
                        axisPointer: {
                            type: 'shadow'
                        }
                    },
                    legend: {
                        data: ['通过率', '平均分'],
                        top: '5%'
                    },
                    grid: {
                        left: '3%',
                        right: '4%',
                        bottom: '3%',
                        containLabel: true
                    },
                    xAxis: {
                        type: 'category',
                        data: difficulties
                    },
                    yAxis: [
                        {
                            type: 'value',
                            name: '通过率(%)',
                            position: 'left',
                            max: 100
                        },
                        {
                            type: 'value',
                            name: '平均分',
                            position: 'right'
                        }
                    ],
                    series: [
                        {
                            name: '通过率',
                            type: 'bar',
                            data: acceptanceRates,
                            yAxisIndex: 0,
                            barGap: '0%',
                            itemStyle: {
                                color: '#409EFF'
                            }
                        },
                        {
                            name: '平均分',
                            type: 'line',
                            data: avgScores,
                            yAxisIndex: 1,
                            smooth: true,
                            itemStyle: {
                                color: '#67C23A'
                            }
                        }
                    ]
                }

                this.difficultyChart.setOption(option)
            }
        },
        updateTrendChart() {
            if (this.trendChart && this.trendData.length > 0) {
                const dates = this.trendData.map(item => item.date)
                const submissions = this.trendData.map(item => item.submissions)
                const acceptanceRates = this.trendData.map(item => item.acceptance_rate)

                const option = {
                    tooltip: {
                        trigger: 'axis'
                    },
                    legend: {
                        data: ['提交数', '通过率'],
                        top: '5%'
                    },
                    grid: {
                        left: '3%',
                        right: '4%',
                        bottom: '3%',
                        containLabel: true
                    },
                    xAxis: {
                        type: 'category',
                        data: dates
                    },
                    yAxis: [
                        {
                            type: 'value',
                            name: '提交数',
                            position: 'left'
                        },
                        {
                            type: 'value',
                            name: '通过率(%)',
                            position: 'right',
                            max: 100
                        }
                    ],
                    series: [
                        {
                            name: '提交数',
                            type: 'line',
                            data: submissions,
                            yAxisIndex: 0,
                            smooth: true,
                            itemStyle: {
                                color: '#E6A23C'
                            }
                        },
                        {
                            name: '通过率',
                            type: 'line',
                            data: acceptanceRates,
                            yAxisIndex: 1,
                            smooth: true,
                            itemStyle: {
                                color: '#67C23A'
                            }
                        }
                    ]
                }

                this.trendChart.setOption(option)
            }
        },
        goBack() {
            this.$router.go(-1)
        },
        exportData() {
            // 获取所有需要导出的数据
            Promise.all([
                api.getAssignment(this.assignmentId),
                api.getAssignmentDetailedStatistics(this.assignmentId),
                api.getAssignmentTopPerformingStudents(this.assignmentId),
                api.getAssignmentProblemStatistics(this.assignmentId)
            ]).then(responses => {
                const assignment = responses[0].data.data;
                const statistics = responses[1].data.data;
                const topStudents = responses[2].data.data;
                const problemStats = responses[3].data.data;

                // 构造CSV内容
                let csvContent = '\uFEFF'; // 添加BOM以支持中文

                // 作业信息
                csvContent += '作业分析报告\n';
                csvContent += `作业名称: ${assignment.title}\n`;
                csvContent += `创建者: ${assignment.creator_username}\n`;
                csvContent += `开始时间: ${assignment.start_time}\n`;
                csvContent += `结束时间: ${assignment.end_time}\n`;
                csvContent += `规则类型: ${assignment.rule_type}\n`;
                csvContent += '\n';

                // 统计概览
                csvContent += '统计概览\n';
                csvContent += '总学生数,已提交学生,平均分,完成率\n';
                csvContent += `${statistics.total_students},${statistics.submitted_students},${statistics.average_score},${statistics.completion_percentage}%\n`;
                csvContent += '\n';

                // 表现最好的学生
                csvContent += '表现最好的学生(Top 10)\n';
                csvContent += '用户名,姓名,总分,解决题目数,完成率\n';
                topStudents.forEach(student => {
                    csvContent += `${student.student_username},${student.student_real_name},${student.total_score},${student.solved_problems},${student.completion_rate}%\n`;
                });
                csvContent += '\n';

                // 题目统计
                csvContent += '题目统计\n';
                csvContent += '题目ID,题目名称,通过率,平均分\n';
                problemStats.forEach(problem => {
                    csvContent += `${problem.problem_id},"${problem.problem_title}",${problem.acceptance_rate}%,${problem.average_score}\n`;
                });

                // 创建并下载CSV文件
                const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                const link = document.createElement('a');
                const url = URL.createObjectURL(blob);

                const fileName = `作业分析_${assignment.title}_${new Date().toISOString().slice(0, 10)}.csv`;
                link.setAttribute('href', url);
                link.setAttribute('download', fileName);
                link.style.visibility = 'hidden';

                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);

                this.$message.success('数据导出成功');
            }).catch(() => {
                this.$message.error('数据导出失败');
            });
        },
        getAcceptanceRateType(rate) {
            const rateValue = parseFloat(rate);
            if (rateValue >= 80) return 'success';
            if (rateValue >= 60) return 'warning';
            return 'danger';
        },
        getScoreClass(score) {
            const scoreValue = parseFloat(score);
            if (scoreValue >= 90) return 'high-score';
            if (scoreValue >= 70) return 'medium-score';
            if (scoreValue >= 60) return 'low-score';
            return 'fail-score';
        }
    }
}
</script>

<style scoped>
.assignment-dashboard {
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

.summary-cards {
    margin-bottom: 20px;
}

.summary-card {
    height: 120px;
    border-radius: 8px;
    transition: all 0.3s ease;
}

.summary-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.summary-content {
    display: flex;
    align-items: center;
    height: 100%;
    padding: 20px;
}

.summary-icon {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    color: white;
    margin-right: 20px;
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

.summary-text {
    text-align: center;
    flex: 1;
}

.summary-value {
    font-size: 28px;
    font-weight: bold;
    margin: 0;
    color: #303133;
}

.summary-label {
    margin: 5px 0 0 0;
    color: #909399;
    font-size: 14px;
}

.chart-section,
.data-section {
    margin-bottom: 20px;
}

.chart-card,
.data-card {
    border-radius: 8px;
    overflow: hidden;
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

.chart-container {
    width: 100%;
    height: 300px;
}

.completion-text {
    text-align: center;
    font-size: 12px;
    color: #606266;
    margin-top: 5px;
}

.high-score {
    color: #67C23A;
    font-weight: bold;
}

.medium-score {
    color: #E6A23C;
    font-weight: bold;
}

.low-score {
    color: #F56C6C;
    font-weight: bold;
}

.fail-score {
    color: #909399;
    font-weight: bold;
}
</style>