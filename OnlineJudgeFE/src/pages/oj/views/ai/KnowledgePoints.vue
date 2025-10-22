<template>
    <div>
        <Row type="flex" justify="space-around">
            <Col :span="22">
            <Panel shadow>
                <div slot="title">
                    <Icon type="md-bookmarks" /> 知识点掌握情况
                </div>
                <div class="knowledge-points-container">
                    <div class="knowledge-points-header">
                        <h3>您的知识点掌握情况</h3>
                        <p>系统根据您的答题情况分析您的知识点掌握程度</p>
                    </div>

                    <div class="knowledge-points-stats">
                        <Row :gutter="20">
                            <Col span="8">
                            <Card class="stat-card">
                                <div class="stat-item">
                                    <Icon type="md-checkmark-circle" size="24" color="#19be6b" />
                                    <div class="stat-text">
                                        <div class="stat-number">{{ masteredPoints }}</div>
                                        <div class="stat-label">已掌握</div>
                                    </div>
                                </div>
                            </Card>
                            </Col>
                            <Col span="8">
                            <Card class="stat-card">
                                <div class="stat-item">
                                    <Icon type="md-time" size="24" color="#ff9900" />
                                    <div class="stat-text">
                                        <div class="stat-number">{{ learningPoints }}</div>
                                        <div class="stat-label">学习中</div>
                                    </div>
                                </div>
                            </Card>
                            </Col>
                            <Col span="8">
                            <Card class="stat-card">
                                <div class="stat-item">
                                    <Icon type="md-warning" size="24" color="#ed4014" />
                                    <div class="stat-text">
                                        <div class="stat-number">{{ needImprovementPoints }}</div>
                                        <div class="stat-label">需加强</div>
                                    </div>
                                </div>
                            </Card>
                            </Col>
                        </Row>
                    </div>

                    <div class="knowledge-points-list">
                        <h3>详细掌握情况</h3>
                        <Table :columns="columns" :data="knowledgePoints" :loading="loading"></Table>
                    </div>

                    <div class="recommendations-section" v-if="recommendations.length > 0">
                        <h3>学习建议</h3>
                        <div class="recommendations-list">
                            <Card v-for="(rec, index) in recommendations" :key="index" class="recommendation-card">
                                <div class="recommendation-header">
                                    <Icon type="md-bulb" color="#ff9900" />
                                    <strong>{{ rec.knowledge_point }}</strong>
                                    <Tag color="red">需加强</Tag>
                                </div>
                                <div class="recommendation-content">
                                    <p>掌握程度: {{ parseFloat(((rec.proficiency_level || 0) * 100).toFixed(2)) }}%</p>
                                    <div class="recommended-problems">
                                        <p>推荐练习题目:</p>
                                        <ul>
                                            <li v-for="problem in rec.recommended_problems" :key="problem.id">
                                                <a @click="goToProblem(problem.id)">{{ problem.title }}</a>
                                            </li>
                                        </ul>
                                    </div>
                                </div>
                            </Card>
                        </div>
                    </div>
                </div>
            </Panel>
            </Col>
        </Row>
    </div>
</template>

<script>
import api from '@oj/api'
import Panel from '@oj/components/Panel.vue'

export default {
    name: 'KnowledgePoints',
    components: {
        Panel
    },
    data() {
        return {
            loading: false,
            knowledgePoints: [],
            recommendations: [],
            columns: [
                {
                    title: '知识点',
                    key: 'knowledge_point',
                    sortable: true
                },
                {
                    title: '掌握程度',
                    key: 'proficiency_level',
                    sortable: true,
                    render: (h, params) => {
                        // 强制处理掌握程度值
                        let level = params.row.proficiency_level || 0;

                        // 强制类型转换和边界处理
                        if (typeof level !== 'number' || isNaN(level)) {
                            level = 0;
                        }

                        // 强制边界处理
                        level = Math.max(0, Math.min(1, level));

                        // 强制精度处理 - 这是关键修改
                        level = parseFloat(level.toFixed(4));

                        let color = 'red';
                        if (level >= 0.8) color = 'green';
                        else if (level >= 0.5) color = 'orange';

                        return h('div', {
                            style: {
                                display: 'flex',
                                alignItems: 'center',
                                width: '100%'
                            }
                        }, [
                            h('Progress', {
                                props: {
                                    percent: parseFloat((level * 100).toFixed(2)),  // 强制保留2位小数
                                    status: level >= 0.8 ? 'success' : 'normal',
                                    strokeColor: color,
                                    showInfo: false
                                },
                                style: {
                                    width: '100%'
                                }
                            })
                        ])
                    }
                },
                {
                    title: '正确/总计',
                    key: 'attempts',
                    render: (h, params) => {
                        return h('span', `${params.row.correct_attempts}/${params.row.total_attempts}`)
                    }
                },
                {
                    title: '最后更新',
                    key: 'last_updated',
                    render: (h, params) => {
                        const lastUpdated = params.row.last_updated;
                        if (!lastUpdated) {
                            return h('span', '暂无记录');
                        }

                        try {
                            // 确保moment.js已经引入
                            if (this.$moment && typeof this.$moment === 'function') {
                                return h('span', this.$moment(lastUpdated).format('YYYY-MM-DD HH:mm'));
                            } else {
                                // 如果moment不可用，使用原生日期处理
                                const date = new Date(lastUpdated);
                                return h('span', date.toLocaleString('zh-CN'));
                            }
                        } catch (e) {
                            console.error('日期格式化错误:', e);
                            return h('span', '时间解析失败');
                        }
                    }

                }
            ]
        }
    },
    computed: {
        masteredPoints() {
            // 强制处理计算属性
            return this.knowledgePoints.filter(kp => {
                const level = typeof kp.proficiency_level === 'number' && !isNaN(kp.proficiency_level)
                    ? kp.proficiency_level
                    : 0;
                return level >= 0.8;
            }).length
        },
        learningPoints() {
            // 强制处理计算属性
            return this.knowledgePoints.filter(kp => {
                const level = typeof kp.proficiency_level === 'number' && !isNaN(kp.proficiency_level)
                    ? kp.proficiency_level
                    : 0;
                return level >= 0.5 && level < 0.8;
            }).length
        },
        needImprovementPoints() {
            // 强制处理计算属性
            return this.knowledgePoints.filter(kp => {
                const level = typeof kp.proficiency_level === 'number' && !isNaN(kp.proficiency_level)
                    ? kp.proficiency_level
                    : 0;
                return level < 0.5;
            }).length
        }
    },
    mounted() {
        this.loadKnowledgePoints()
        this.loadRecommendations()
    },
    methods: {
        formatPercentage(value) {
            if (typeof value !== 'number' || isNaN(value)) {
                return '0.00';
            }

            // 边界值处理
            if (value < 0) value = 0;
            if (value > 1) value = 1;

            // 特殊处理接近边界值的情况
            if (value > 0.9999) value = 1;
            if (value < 0.0001) value = 0;

            // 转换为百分比并格式化为2位小数
            const percentage = value * 100;
            return percentage.toFixed(2);
        },
        fixFloatPrecision(value) {
            if (typeof value !== 'number' || isNaN(value)) {
                return 0;
            }

            // 使用高精度处理
            return Math.round(value * 10000) / 10000;
        },
        async loadKnowledgePoints() {
            this.loading = true
            try {
                const res = await api.getKnowledgePoints()
                const rawData = res.data.data || res.data || []

                // 强制数据处理
                this.knowledgePoints = rawData.map(item => {
                    let proficiency_level = item.proficiency_level;

                    // 强制类型检查和默认值
                    if (typeof proficiency_level !== 'number' || isNaN(proficiency_level)) {
                        proficiency_level = 0;
                    }

                    // 强制边界处理
                    proficiency_level = Math.max(0, Math.min(1, proficiency_level));

                    // 强制精度处理 - 关键修改
                    proficiency_level = parseFloat(proficiency_level.toFixed(4));

                    return {
                        ...item,
                        proficiency_level: proficiency_level
                    };
                });
            } catch (err) {
                console.error('获取知识点掌握情况失败:', err)
                this.$error('获取知识点掌握情况失败: ' + (err.message || '未知错误'))
                this.knowledgePoints = []
            } finally {
                this.loading = false
            }
        },
        async loadRecommendations() {
            try {
                const res = await api.getKnowledgeRecommendations()
                this.recommendations = res.data.data || res.data
            } catch (err) {
                this.$error('获取学习建议失败')
            }
        },

        goToProblem(problemId) {
            this.$router.push({
                name: 'problem-details',
                params: { problemID: problemId }
            })
        }
    }
}
</script>

<style lang="less" scoped>
.knowledge-points-container {
    .knowledge-points-header {
        text-align: center;
        margin-bottom: 30px;

        h3 {
            font-size: 24px;
            margin-bottom: 10px;
        }

        p {
            color: #808695;
        }
    }

    .knowledge-points-stats {
        margin-bottom: 30px;

        .stat-card {
            text-align: center;

            .stat-item {
                display: flex;
                align-items: center;
                justify-content: center;

                .stat-text {
                    margin-left: 10px;

                    .stat-number {
                        font-size: 24px;
                        font-weight: bold;
                        color: #2d8cf0;
                    }

                    .stat-label {
                        font-size: 12px;
                        color: #808695;
                    }
                }
            }
        }
    }

    .knowledge-points-list {
        margin-bottom: 30px;

        h3 {
            margin-bottom: 15px;
        }
    }

    .recommendations-section {
        h3 {
            margin-bottom: 15px;
        }

        .recommendations-list {
            .recommendation-card {
                margin-bottom: 15px;

                .recommendation-header {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    margin-bottom: 10px;

                    strong {
                        font-size: 16px;
                    }
                }

                .recommendation-content {
                    p {
                        margin: 5px 0;
                    }

                    .recommended-problems {
                        ul {
                            padding-left: 20px;

                            li {
                                margin: 3px 0;

                                a {
                                    color: #2d8cf0;
                                    cursor: pointer;

                                    &:hover {
                                        text-decoration: underline;
                                    }
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