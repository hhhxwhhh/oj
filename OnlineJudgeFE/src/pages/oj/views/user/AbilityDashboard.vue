<template>
    <div class="container">
        <Card :padding="0">
            <div class="page-header">
                <h2>编程能力评估仪表盘</h2>
                <div class="header-actions">
                    <span v-if="abilityData.last_assessed" class="last-assessed">
                        最后评估: {{ new Date(abilityData.last_assessed).toLocaleString() }}
                    </span>
                    <Button type="primary" @click="refreshAssessment" :loading="loading">
                        <Icon type="md-refresh" /> 重新评估
                    </Button>
                </div>
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
                            <span class="ability-score">{{ item.score.toFixed(1) }}/100</span>
                        </div>
                        <Progress :percent="(item.score / 100) * 100" :stroke-color="getProgressColor(item.score)"
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
            <div v-if="trendData.loading" class="trend-loading">
                <Spin size="large" />
                <p>正在分析能力趋势...</p>
            </div>
            <div v-else-if="trendData.error" class="trend-error">
                <Icon type="md-warning" size="30" color="#ff9900" />
                <p>趋势分析失败: {{ trendData.error }}</p>
                <Button @click="loadTrendData" size="small">重试</Button>
            </div>
            <div v-else-if="trendData.noData" class="trend-no-data">
                <Icon type="md-information-circle" size="30" color="#ccc" />
                <p>暂无足够数据进行趋势分析，请继续使用系统以积累数据</p>
            </div>
            <div v-else class="trend-content">
                <Tabs value="overall" @on-click="changeTrendTab">
                    <TabPane label="综合能力" name="overall">
                        <div class="trend-summary">
                            <div class="trend-indicator"
                                :class="(trendData.analysis && trendData.analysis.overall_score && trendData.analysis.overall_score.trend) || 'unknown'">
                                <Icon
                                    :type="getTrendIcon(trendData.analysis && trendData.analysis.overall_score && trendData.analysis.overall_score.trend)"
                                    :size="24"
                                    :color="getTrendColor(trendData.analysis && trendData.analysis.overall_score && trendData.analysis.overall_score.trend)" />
                                <span>{{ getTrendText(trendData.analysis && trendData.analysis.overall_score &&
                                    trendData.analysis.overall_score.trend) }}</span>
                            </div>
                            <div class="trend-stats">
                                <div class="stat-item">
                                    <span class="stat-label">变化率:</span>
                                    <span class="stat-value"
                                        :class="getSlopeClass(trendData.analysis && trendData.analysis.overall_score && trendData.analysis.overall_score.slope)">
                                        {{ ((trendData.analysis && trendData.analysis.overall_score &&
                                            trendData.analysis.overall_score.slope) || 0 * 24).toFixed(2) }}/天
                                    </span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-label">置信度:</span>
                                    <span class="stat-value">
                                        {{ ((trendData.analysis && trendData.analysis.overall_score &&
                                            trendData.analysis.overall_score.confidence) || 0 * 100).toFixed(1) }}%
                                    </span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-label">模型:</span>
                                    <span class="stat-value">{{
                                        getTrendModelText(trendData.analysis && trendData.analysis.overall_score &&
                                            trendData.analysis.overall_score.model_type) }}</span>
                                </div>
                            </div>
                        </div>
                        <ECharts :options="overallTrendChartOptions" :autoresize="true" style="height: 300px;">
                        </ECharts>
                    </TabPane>
                    <TabPane label="基础编程" name="basic_programming">
                        <ECharts :options="basicProgrammingTrendChartOptions" :autoresize="true" style="height: 300px;">
                        </ECharts>
                    </TabPane>
                    <TabPane label="数据结构" name="data_structure">
                        <ECharts :options="dataStructureTrendChartOptions" :autoresize="true" style="height: 300px;">
                        </ECharts>
                    </TabPane>
                    <TabPane label="算法设计" name="algorithm_design">
                        <ECharts :options="algorithmDesignTrendChartOptions" :autoresize="true" style="height: 300px;">
                        </ECharts>
                    </TabPane>
                    <TabPane label="问题解决" name="problem_solving">
                        <ECharts :options="problemSolvingTrendChartOptions" :autoresize="true" style="height: 300px;">
                        </ECharts>
                    </TabPane>
                </Tabs>
            </div>
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
                ability_breakdown: {},
                analysis_report: {},
                last_assessed: null
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
                        { name: '基础编程(100)', max: 100 },
                        { name: '数据结构(100)', max: 100 },
                        { name: '算法设计(100)', max: 100 },
                        { name: '问题解决(100)', max: 100 }
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
                            value: [50, 50, 50, 50],
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
                    boundaryGap: [0, 0.01],
                    max: 100
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
                        data: [50, 50, 50, 50]
                    }
                ]
            },

            abilityDetails: {},
            recommendations: [],
            trendData: {
                loading: false,
                error: null,
                noData: false,
                analysis: {
                    overall_score: {}
                },
                history: []
            },


            overallTrendChartOptions: {
                title: {
                    text: '综合能力趋势'
                },
                tooltip: {
                    trigger: 'axis'
                },
                legend: {
                    data: ['历史得分', '预测得分']
                },
                xAxis: {
                    type: 'category',
                    data: []
                },
                yAxis: {
                    type: 'value',
                    min: 0,
                    max: 100
                },
                series: [
                    {
                        name: '历史得分',
                        type: 'line',
                        data: [],
                        smooth: true
                    },
                    {
                        name: '预测得分',
                        type: 'line',
                        data: [],
                        smooth: true,
                        lineStyle: {
                            type: 'dashed'
                        }
                    }
                ]
            },
            basicProgrammingTrendChartOptions: {
                title: {
                    text: '基础编程能力趋势'
                },
                tooltip: {
                    trigger: 'axis'
                },
                xAxis: {
                    type: 'category',
                    data: []
                },
                yAxis: {
                    type: 'value',
                    min: 0,
                    max: 100
                },
                series: [
                    {
                        name: '历史得分',
                        type: 'line',
                        data: [],
                        smooth: true
                    },
                    {
                        name: '预测得分',
                        type: 'line',
                        data: [],
                        smooth: true,
                        lineStyle: {
                            type: 'dashed'
                        }
                    }
                ]
            },
            dataStructureTrendChartOptions: {
                title: {
                    text: '数据结构能力趋势'
                },
                tooltip: {
                    trigger: 'axis'
                },
                xAxis: {
                    type: 'category',
                    data: []
                },
                yAxis: {
                    type: 'value',
                    min: 0,
                    max: 100
                },
                series: [
                    {
                        name: '历史得分',
                        type: 'line',
                        data: [],
                        smooth: true
                    },
                    {
                        name: '预测得分',
                        type: 'line',
                        data: [],
                        smooth: true,
                        lineStyle: {
                            type: 'dashed'
                        }
                    }
                ]
            },
            algorithmDesignTrendChartOptions: {
                title: {
                    text: '算法设计能力趋势'
                },
                tooltip: {
                    trigger: 'axis'
                },
                xAxis: {
                    type: 'category',
                    data: []
                },
                yAxis: {
                    type: 'value',
                    min: 0,
                    max: 100
                },
                series: [
                    {
                        name: '历史得分',
                        type: 'line',
                        data: [],
                        smooth: true
                    },
                    {
                        name: '预测得分',
                        type: 'line',
                        data: [],
                        smooth: true,
                        lineStyle: {
                            type: 'dashed'
                        }
                    }
                ]
            },
            problemSolvingTrendChartOptions: {
                title: {
                    text: '问题解决能力趋势'
                },
                tooltip: {
                    trigger: 'axis'
                },
                xAxis: {
                    type: 'category',
                    data: []
                },
                yAxis: {
                    type: 'value',
                    min: 0,
                    max: 100
                },
                series: [
                    {
                        name: '历史得分',
                        type: 'line',
                        data: [],
                        smooth: true
                    },
                    {
                        name: '预测得分',
                        type: 'line',
                        data: [],
                        smooth: true,
                        lineStyle: {
                            type: 'dashed'
                        }
                    }
                ]
            }
        }
    },
    async mounted() {
        await this.loadAbilityData()
        await this.loadTrendData()
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

                // 更新雷达图数据 - 使用新的能力分解详情
                if (this.abilityData.ability_breakdown && Object.keys(this.abilityData.ability_breakdown).length > 0) {
                    const breakdown = this.abilityData.ability_breakdown;
                    this.radarChartOptions.series[0].data[0].value = [
                        (breakdown.basic_programming && breakdown.basic_programming.score) || 0,
                        (breakdown.data_structure && breakdown.data_structure.score) || 0,
                        (breakdown.algorithm_design && breakdown.algorithm_design.score) || 0,
                        (breakdown.problem_solving && breakdown.problem_solving.score) || 0
                    ]
                } else if (this.abilityData.basic_programming_score !== undefined) {
                    // 兼容旧格式
                    this.radarChartOptions.series[0].data[0].value = [
                        this.abilityData.basic_programming_score || 0,
                        this.abilityData.data_structure_score || 0,
                        this.abilityData.algorithm_design_score || 0,
                        this.abilityData.problem_solving_score || 0
                    ]
                }

                // 更新对比图数据
                if (this.abilityData.comparison) {
                    if (this.abilityData.ability_breakdown && Object.keys(this.abilityData.ability_breakdown).length > 0) {
                        const breakdown = this.abilityData.ability_breakdown;
                        this.comparisonChartOptions.series[0].data = [
                            (breakdown.basic_programming && breakdown.basic_programming.score) || 0,
                            (breakdown.data_structure && breakdown.data_structure.score) || 0,
                            (breakdown.algorithm_design && breakdown.algorithm_design.score) || 0,
                            (breakdown.problem_solving && breakdown.problem_solving.score) || 0
                        ]
                    } else {
                        this.comparisonChartOptions.series[0].data = [
                            this.abilityData.basic_programming_score || 0,
                            this.abilityData.data_structure_score || 0,
                            this.abilityData.algorithm_design_score || 0,
                            this.abilityData.problem_solving_score || 0
                        ]
                    }

                    this.comparisonChartOptions.series[1].data = [
                        (this.abilityData.comparison.average && this.abilityData.comparison.average.basic_programming_score) || 0,
                        (this.abilityData.comparison.average && this.abilityData.comparison.average.data_structure_score) || 0,
                        (this.abilityData.comparison.average && this.abilityData.comparison.average.algorithm_design_score) || 0,
                        (this.abilityData.comparison.average && this.abilityData.comparison.average.problem_solving_score) || 0
                    ]
                }

                // 处理能力详情 - 使用新的能力分解详情
                if (this.abilityData.ability_breakdown && Object.keys(this.abilityData.ability_breakdown).length > 0) {
                    const breakdown = this.abilityData.ability_breakdown;
                    this.abilityDetails = {
                        basic_programming: {
                            name: '基础编程能力',
                            score: (breakdown.basic_programming && breakdown.basic_programming.score) || 0,
                            description: '包括语法掌握、基本控制结构等'
                        },
                        data_structures: {
                            name: '数据结构能力',
                            score: (breakdown.data_structure && breakdown.data_structure.score) || 0,
                            description: '如数组、链表、树、图等数据结构的运用'
                        },
                        algorithm_design: {
                            name: '算法设计能力',
                            score: (breakdown.algorithm_design && breakdown.algorithm_design.score) || 0,
                            description: '包括复杂度分析、算法设计与优化等'
                        },
                        problem_solving: {
                            name: '问题解决能力',
                            score: (breakdown.problem_solving && breakdown.problem_solving.score) || 0,
                            description: '包括问题建模、解决方案设计等'
                        }
                    }
                } else {
                    // 兼容旧格式
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
                    ability_breakdown: {},
                    analysis_report: {
                        recommendations: []
                    },
                    last_assessed: null
                }
                this.submissionStats = {
                    accepted: 0,
                    total: 0
                }
            } finally {
                this.loading = false
            }
        },

        async loadTrendData() {
            try {
                this.trendData.loading = true
                this.trendData.error = null

                const res = await api.getUserAbilityTrend()

                if (!res || !res.data || !res.data.data) {
                    throw new Error('无效的响应数据')
                }

                const trendData = res.data.data

                // 检查是否有足够的数据
                if (!trendData.history_data || trendData.history_data.length === 0) {
                    this.trendData.noData = true
                    return
                }

                this.trendData.analysis = trendData.trend_analysis
                this.trendData.history = trendData.history_data
                this.trendData.noData = false

                // 更新图表数据
                this.updateTrendCharts()
            } catch (err) {
                console.error('获取能力趋势数据失败:', err)
                this.trendData.error = err.message || err
            } finally {
                this.trendData.loading = false
            }
        },
        updateTrendCharts() {
            // 更新综合能力趋势图
            this.updateSingleTrendChart(
                this.overallTrendChartOptions,
                'overall_score',
                '综合能力'
            )

            // 更新基础编程能力趋势图
            this.updateSingleTrendChart(
                this.basicProgrammingTrendChartOptions,
                'basic_programming_score',
                '基础编程'
            )

            // 更新数据结构能力趋势图
            this.updateSingleTrendChart(
                this.dataStructureTrendChartOptions,
                'data_structure_score',
                '数据结构'
            )

            // 更新算法设计能力趋势图
            this.updateSingleTrendChart(
                this.algorithmDesignTrendChartOptions,
                'algorithm_design_score',
                '算法设计'
            )

            // 更新问题解决能力趋势图
            this.updateSingleTrendChart(
                this.problemSolvingTrendChartOptions,
                'problem_solving_score',
                '问题解决'
            )
        },
        updateSingleTrendChart(chartOptions, dimension, dimensionName) {
            // 准备历史数据
            const historyData = this.trendData.history.map(record => ({
                date: new Date(record.recorded_at).toLocaleDateString(),
                score: record[dimension]
            }))

            // 准备预测数据
            const predictions = this.trendData.analysis[dimension]
                ? this.trendData.analysis[dimension].predictions || []
                : []

            const predictionData = predictions.map(pred => ({
                date: `预测+${Math.round(pred.timestamp / 24)}天`,
                score: pred.predicted_score
            }))

            // 合并所有数据点用于X轴
            const allDates = [
                ...historyData.map(d => d.date),
                ...predictionData.map(d => d.date)
            ]

            // 更新图表配置
            chartOptions.xAxis.data = allDates
            chartOptions.series[0].data = historyData.map(d => d.score)
            chartOptions.series[1].data = [
                ...new Array(historyData.length - 1).fill(null),
                historyData[historyData.length - 1].score, // 连接最后一个历史点
                ...predictionData.map(d => d.score)
            ]
            chartOptions.title.text = `${dimensionName}趋势`
        },
        changeTrendTab(tabName) {
            // 标签页切换时的处理
            console.log('切换到趋势标签页:', tabName)
        },

        getTrendIcon(trend) {
            if (!trend) return 'md-help';
            switch (trend) {
                case 'improving': return 'md-trending-up'
                case 'declining': return 'md-trending-down'
                case 'stable': return 'md-remove'
                default: return 'md-help'
            }
        },


        getTrendColor(trend) {
            if (!trend) return '#808695';
            switch (trend) {
                case 'improving': return '#19be6b'
                case 'declining': return '#ed4014'
                case 'stable': return '#ff9900'
                default: return '#808695'
            }
        },

        getTrendText(trend) {
            if (!trend) return '数据不足';
            switch (trend) {
                case 'improving': return '正在提升'
                case 'declining': return '正在下降'
                case 'stable': return '保持稳定'
                case 'insufficient_data': return '数据不足'
                default: return '未知'
            }
        },

        getSlopeClass(slope) {
            if (slope === undefined || slope === null) return 'stable';
            if (slope > 0.1) return 'improving'
            if (slope < -0.1) return 'declining'
            return 'stable'
        },

        getTrendModelText(modelType) {
            if (!modelType) return '未知模型';
            switch (modelType) {
                case 'linear': return '线性回归'
                case 'polynomial': return '多项式回归'
                default: return '未知模型'
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
            if (score < 40) return '#ed4014'
            if (score < 60) return '#ff9900'
            if (score < 80) return '#2d8cf0'
            return '#19be6b'
        },



        getProgressStatus(score) {
            if (score < 40) return 'wrong'
            if (score < 60) return 'normal'
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

.page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
}

.header-actions {
    display: flex;
    align-items: center;
    gap: 15px;
}

.last-assessed {
    font-size: 14px;
    color: #808695;
}

.trend-loading,
.trend-error,
.trend-no-data {
    text-align: center;
    padding: 40px 0;
}

.trend-loading p,
.trend-error p,
.trend-no-data p {
    margin: 10px 0 0 0;
    color: #808695;
}

.trend-error p {
    color: #ff9900;
}

.trend-no-data p {
    color: #ccc;
}

.trend-content {
    padding: 10px 0;
}

.trend-summary {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px;
    background-color: #f8f9fa;
    border-radius: 4px;
    margin-bottom: 20px;
}

.trend-indicator {
    display: flex;
    align-items: center;
    gap: 10px;
    font-weight: bold;
    font-size: 16px;
}

.trend-indicator.improving {
    color: #19be6b;
}

.trend-indicator.declining {
    color: #ed4014;
}

.trend-indicator.stable {
    color: #ff9900;
}

.trend-stats {
    display: flex;
    gap: 20px;
}

.stat-item {
    text-align: center;
}

.stat-label {
    display: block;
    font-size: 12px;
    color: #808695;
}

.stat-value {
    display: block;
    font-size: 16px;
    font-weight: bold;
}

.stat-value.improving {
    color: #19be6b;
}

.stat-value.declining {
    color: #ed4014;
}
</style>