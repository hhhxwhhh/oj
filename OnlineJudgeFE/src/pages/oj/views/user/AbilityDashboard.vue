<template>
    <div class="container">
        <Card :padding="0">
            <div class="page-header">
                <h2>编程能力评估仪表盘</h2>
                <Button type="primary" @click="refreshAssessment" :loading="loading">
                    <Icon type="md-refresh" /> 重新评估
                </Button>
            </div>
        </Card>

        <!-- 能力总览 -->
        <Row :gutter="20" class="dashboard-section">
            <Col :span="8">
            <Card class="overall-score-card">
                <div class="score-display">
                    <div class="score-circle">
                        <span class="score-value">{{ abilityData.overall_score.toFixed(0) }}</span>
                        <span class="score-max">/100</span>
                    </div>
                    <div class="score-info">
                        <h3>综合能力评分</h3>
                        <Tag :color="getLevelColor(abilityData.level)">{{ getLevelDisplay(abilityData.level) }}</Tag>
                    </div>
                </div>
            </Card>
            </Col>
            <Col :span="8">
            <Card class="stats-card">
                <div class="stat-item">
                    <Icon type="md-trending-up" size="30" color="#2d8cf0" />
                    <div class="stat-content">
                        <p class="stat-value">{{ submissionStats.accepted }}</p>
                        <p class="stat-label">已解决题目</p>
                    </div>
                </div>
            </Card>
            </Col>
            <Col :span="8">
            <Card class="stats-card">
                <div class="stat-item">
                    <Icon type="md-document" size="30" color="#19be6b" />
                    <div class="stat-content">
                        <p class="stat-value">{{ submissionStats.total }}</p>
                        <p class="stat-label">总提交次数</p>
                    </div>
                </div>
            </Card>
            </Col>
        </Row>

        <!-- 能力雷达图 -->
        <Card class="dashboard-section">
            <div slot="title">
                <Icon type="md-analytics" />
                能力维度雷达图
            </div>
            <ECharts :options="radarChartOptions" :autoresize="true" style="height: 400px;"></ECharts>
        </Card>

        <!-- 能力详情 -->
        <Row :gutter="20" class="dashboard-section">
            <Col :span="12">
            <Card>
                <div slot="title">
                    <Icon type="md-speedometer" />
                    各维度能力详情
                </div>
                <div class="ability-details">
                    <div class="ability-item" v-for="(item, key) in abilityDetails" :key="key">
                        <div class="ability-header">
                            <span class="ability-name">{{ item.name }}</span>
                            <span class="ability-score">{{ item.score.toFixed(1) }}/40</span>
                        </div>
                        <Progress :percent="(item.score / 40) * 100" :stroke-color="getProgressColor(item.score)"
                            :status="getProgressStatus(item.score)" />
                        <p class="ability-description">{{ item.description }}</p>
                    </div>
                </div>
            </Card>
            </Col>
            <Col :span="12">
            <Card>
                <div slot="title">
                    <Icon type="md-clipboard" />
                    个性化学习建议
                </div>
                <div class="recommendations">
                    <div class="recommendation-item" v-for="(rec, index) in recommendations" :key="index">
                        <div class="recommendation-content">
                            <Tag :color="getRecommendationColor(rec.priority)">{{ getPriorityDisplay(rec.priority) }}
                            </Tag>
                            <p>{{ rec.content }}</p>
                        </div>
                    </div>
                </div>
            </Card>
            </Col>
        </Row>

        <!-- 能力对比 -->
        <Card class="dashboard-section">
            <div slot="title">
                <Icon type="md-git-compare" />
                能力对比分析
            </div>
            <ECharts :options="comparisonChartOptions" :autoresize="true" style="height: 300px;"></ECharts>
        </Card>

        <!-- 能力趋势 -->
        <Card class="dashboard-section">
            <div slot="title">
                <Icon type="md-trending-up" />
                能力发展趋势
            </div>
            <p class="coming-soon">能力发展趋势图表即将推出</p>
        </Card>
    </div>
</template>
<script>
import api from '@oj/api'

export default {
    name: 'AbilityDashboard',
    data() {
        return {
            loading: false,
            abilityData: {
                overall_score: 0,
                level: 'beginner',
                basic_programming_score: 0,
                data_structure_score: 0,
                algorithm_design_score: 0,
                problem_solving_score: 0,
                analysis_report: {}
            },
            submissionStats: {
                accepted: 0,
                total: 0
            },
            radarChartOptions: {
                title: {
                    text: '能力维度雷达图'
                },
                tooltip: {},
                radar: {
                    indicator: [
                        { name: '基础编程(40)', max: 40 },
                        { name: '数据结构(40)', max: 40 },
                        { name: '算法设计(40)', max: 40 },
                        { name: '问题解决(40)', max: 40 }
                    ]
                },
                series: [{
                    type: 'radar',
                    data: [
                        {
                            value: [0, 0, 0, 0],
                            name: '你的得分'
                        },
                        {
                            value: [20, 20, 20, 20],
                            name: '平均水平'
                        }
                    ]
                }]
            },
            comparisonChartOptions: {
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        type: 'shadow'
                    }
                },
                legend: {
                    data: ['你的得分', '平均水平']
                },
                grid: {
                    left: '3%',
                    right: '4%',
                    bottom: '3%',
                    containLabel: true
                },
                xAxis: {
                    type: 'value',
                    boundaryGap: [0, 0.01]
                },
                yAxis: {
                    type: 'category',
                    data: ['基础编程', '数据结构', '算法设计', '问题解决']
                },
                series: [
                    {
                        name: '你的得分',
                        type: 'bar',
                        data: [0, 0, 0, 0]
                    },
                    {
                        name: '平均水平',
                        type: 'bar',
                        data: [20, 20, 20, 20]
                    }
                ]
            },
            abilityDetails: {},
            recommendations: []
        }
    },
    async mounted() {
        await this.loadAbilityData()
    },
    methods: {
        async loadAbilityData() {
            try {
                this.loading = true
                const res = await api.getProgrammingAbilityReport()

                // 检查响应数据
                if (!res || !res.data || !res.data.data) {
                    throw new Error('无效的响应数据')
                }

                this.abilityData = res.data.data

                // 更新雷达图数据
                if (this.abilityData.basic_programming_score !== undefined) {
                    this.radarChartOptions.series[0].data[0].value = [
                        this.abilityData.basic_programming_score || 0,
                        this.abilityData.data_structure_score || 0,
                        this.abilityData.algorithm_design_score || 0,
                        this.abilityData.problem_solving_score || 0
                    ]
                }

                // 更新对比图数据
                if (this.abilityData.comparison) {
                    this.comparisonChartOptions.series[0].data = [
                        this.abilityData.basic_programming_score || 0,
                        this.abilityData.data_structure_score || 0,
                        this.abilityData.algorithm_design_score || 0,
                        this.abilityData.problem_solving_score || 0
                    ]

                    this.comparisonChartOptions.series[1].data = [
                        this.abilityData.comparison.average.basic_programming_score || 0,
                        this.abilityData.comparison.average.data_structure_score || 0,
                        this.abilityData.comparison.average.algorithm_design_score || 0,
                        this.abilityData.comparison.average.problem_solving_score || 0
                    ]
                }

                // 处理能力详情
                this.abilityDetails = {
                    basic_programming: {
                        name: '基础编程能力',
                        score: this.abilityData.basic_programming_score || 0,
                        description: '包括语法掌握、基本控制结构等'
                    },
                    data_structures: {
                        name: '数据结构能力',
                        score: this.abilityData.data_structure_score || 0,
                        description: '如数组、链表、树、图等数据结构的运用'
                    },
                    algorithm_design: {
                        name: '算法设计能力',
                        score: this.abilityData.algorithm_design_score || 0,
                        description: '包括复杂度分析、算法设计与优化等'
                    },
                    problem_solving: {
                        name: '问题解决能力',
                        score: this.abilityData.problem_solving_score || 0,
                        description: '包括问题建模、解决方案设计等'
                    }
                }

                // 处理推荐建议
                if (this.abilityData.analysis_report && this.abilityData.analysis_report.recommendations) {
                    this.recommendations = this.abilityData.analysis_report.recommendations
                } else if (this.abilityData.analysis_report && Array.isArray(this.abilityData.analysis_report)) {
                    this.recommendations = this.abilityData.analysis_report
                } else {
                    this.recommendations = []
                }

                // 获取用户提交统计数据
                if (this.abilityData.user_stats) {
                    this.submissionStats = {
                        accepted: this.abilityData.user_stats.accepted_number || 0,
                        total: this.abilityData.user_stats.submission_number || 0
                    }
                } else {
                    // 如果没有user_stats，尝试其他方式获取
                    this.submissionStats = {
                        accepted: 0,
                        total: 0
                    }
                }
            } catch (err) {
                console.error('获取能力评估数据失败:', err)
                this.$error('获取能力评估数据失败: ' + (err.message || err))
                // 设置默认值以避免页面完全空白
                this.abilityData = {
                    overall_score: 0,
                    level: 'beginner',
                    basic_programming_score: 0,
                    data_structure_score: 0,
                    algorithm_design_score: 0,
                    problem_solving_score: 0,
                    analysis_report: {
                        recommendations: []
                    }
                }
                this.submissionStats = {
                    accepted: 0,
                    total: 0
                }
            } finally {
                this.loading = false
            }
        },

        async refreshAssessment() {
            try {
                this.loading = true
                const res = await api.assessProgrammingAbility()
                if (res && res.data && res.data.data) {
                    await this.loadAbilityData()
                    this.$success('能力评估已完成')
                } else {
                    throw new Error('评估响应无效')
                }
            } catch (err) {
                console.error('能力评估失败:', err)
                this.$error('能力评估失败: ' + (err.message || err))
            } finally {
                this.loading = false
            }
        },

        getLevelColor(level) {
            const colors = {
                'beginner': 'red',
                'intermediate': 'blue',
                'advanced': 'green',
                'expert': 'gold'
            }
            return colors[level] || 'blue'
        },

        getLevelDisplay(level) {
            const displays = {
                'beginner': '入门',
                'intermediate': '中级',
                'advanced': '高级',
                'expert': '专家'
            }
            return displays[level] || level
        },

        getProgressColor(score) {
            if (score < 15) return '#ed4014'
            if (score < 25) return '#ff9900'
            if (score < 35) return '#2d8cf0'
            return '#19be6b'
        },

        getProgressStatus(score) {
            if (score < 15) return 'wrong'
            if (score < 25) return 'normal'
            return 'success'
        },

        getRecommendationColor(priority) {
            const colors = {
                'high': 'red',
                'medium': 'orange',
                'low': 'blue'
            }
            return colors[priority] || 'blue'
        },

        getPriorityDisplay(priority) {
            const displays = {
                'high': '高优先级',
                'medium': '中优先级',
                'low': '低优先级'
            }
            return displays[priority] || priority
        }
    }
}
</script>
<style scoped>
.page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
}

.dashboard-section {
    margin-bottom: 20px;
}

.overall-score-card {
    text-align: center;
}

.score-display {
    display: flex;
    justify-content: center;
    align-items: center;
}

.score-circle {
    width: 120px;
    height: 120px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    margin-right: 20px;
}

.score-value {
    font-size: 36px;
    font-weight: bold;
    color: white;
}

.score-max {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.8);
}

.score-info h3 {
    margin: 0 0 10px 0;
}

.stat-item {
    display: flex;
    align-items: center;
}

.stat-content {
    margin-left: 15px;
}

.stat-value {
    font-size: 24px;
    font-weight: bold;
    margin: 0;
}

.stat-label {
    margin: 5px 0 0 0;
    color: #808695;
}

.ability-details {
    padding: 10px 0;
}

.ability-item {
    margin-bottom: 20px;
}

.ability-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 5px;
}

.ability-name {
    font-weight: bold;
}

.ability-score {
    color: #808695;
}

.ability-description {
    margin: 5px 0 0 0;
    font-size: 12px;
    color: #808695;
}

.recommendations {
    max-height: 400px;
    overflow-y: auto;
}

.recommendation-item {
    margin-bottom: 15px;
    padding-bottom: 15px;
    border-bottom: 1px solid #e8eaec;
}

.recommendation-item:last-child {
    border-bottom: none;
    margin-bottom: 0;
    padding-bottom: 0;
}

.coming-soon {
    text-align: center;
    color: #808695;
    font-style: italic;
}
</style>