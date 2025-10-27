<template>
    <div class="problem-complexity">
        <div v-if="loading" class="loading">
            <Spin size="large" />
            <p>正在分析题目复杂度...</p>
        </div>

        <div v-else-if="complexityData" class="complexity-content">
            <Card class="complexity-card">
                <div slot="title" class="card-title">
                    <Icon type="md-analytics" />
                    题目复杂度分析
                </div>

                <div class="complexity-metrics">
                    <Row :gutter="16">
                        <Col :span="8">
                        <div class="metric-item">
                            <div class="metric-value">{{ complexityData.word_count }}</div>
                            <div class="metric-label">词数</div>
                        </div>
                        </Col>
                        <Col :span="8">
                        <div class="metric-item">
                            <div class="metric-value">{{ complexityData.sentence_count }}</div>
                            <div class="metric-label">句子数</div>
                        </div>
                        </Col>
                        <Col :span="8">
                        <div class="metric-item">
                            <div class="metric-value">{{ complexityData.complexity_score.toFixed(1) }}</div>
                            <div class="metric-label">复杂度评分</div>
                        </div>
                        </Col>
                    </Row>
                </div>

                <div class="complexity-details">
                    <div class="keywords-section">
                        <h4>关键词</h4>
                        <div class="keywords-list">
                            <Tag v-for="(keyword, index) in complexityData.keywords" :key="index" color="primary"
                                class="keyword-tag">
                                {{ keyword }}
                            </Tag>
                        </div>
                    </div>

                    <div v-if="complexityData.readability_score" class="readability-section">
                        <h4>可读性分析</h4>
                        <p>可读性分数: {{ complexityData.readability_score.toFixed(1) }}</p>
                        <p>年级水平: {{ complexityData.grade_level }}</p>
                    </div>

                    <div v-if="complexityData.last_analysis_time" class="analysis-time">
                        <p>最后分析时间: {{ complexityData.last_analysis_time | localtime }}</p>
                    </div>
                </div>
            </Card>

            <div class="complexity-visualization">
                <div class="visualization-header">
                    <h4>复杂度可视化</h4>
                </div>
                <div class="complexity-gauge">
                    <i-circle :percent="complexityData.complexity_score" stroke-color="#2d8cf0" :stroke-width="8"
                        :size="200">
                        <span class="gauge-text">
                            <p>复杂度</p>
                            <p class="gauge-score">{{ complexityData.complexity_score.toFixed(1) }}</p>
                        </span>
                    </i-circle>
                </div>
                <div class="complexity-level">
                    <p>复杂度等级:
                        <Tag :color="getComplexityLevelColor(complexityData.complexity_score)">
                            {{ getComplexityLevel(complexityData.complexity_score) }}
                        </Tag>
                    </p>
                </div>
            </div>
        </div>

        <div v-else class="no-data">
            <p>暂无复杂度分析数据</p>
            <Button v-if="isAdminRole" @click="analyzeComplexity" type="primary" :loading="analyzing">
                分析题目复杂度
            </Button>
        </div>
    </div>
</template>

<script>
import api from '@oj/api'
import { mapGetters } from 'vuex'

export default {
    name: 'ProblemComplexity',
    props: {
        problemId: {
            type: [String, Number],
            required: true
        }
    },
    data() {
        return {
            loading: false,
            analyzing: false,
            complexityData: null
        }
    },
    computed: {
        ...mapGetters(['isAdminRole'])
    },
    mounted() {
        this.loadComplexityData()
    },
    methods: {
        async loadComplexityData() {
            this.loading = true
            try {
                const res = await api.getProblemComplexity(this.problemId)
                this.complexityData = res.data.data
            } catch (err) {
                // 处理错误但不显示给用户
                console.error('Failed to load complexity data:', err)
            } finally {
                this.loading = false
            }
        },

        async analyzeComplexity() {
            if (!this.isAdminRole) return

            this.analyzing = true
            try {
                const res = await api.analyzeProblemComplexity(this.problemId)
                this.complexityData = res.data.data
                this.$success('分析完成')
            } catch (err) {
                this.$error(err.message || '分析失败')
            } finally {
                this.analyzing = false
            }
        },

        getComplexityLevel(score) {
            if (score >= 80) return '非常复杂'
            if (score >= 60) return '复杂'
            if (score >= 40) return '中等'
            if (score >= 20) return '简单'
            return '非常简单'
        },

        getComplexityLevelColor(score) {
            if (score >= 80) return 'red'
            if (score >= 60) return 'orange'
            if (score >= 40) return 'yellow'
            if (score >= 20) return 'green'
            return 'blue'
        }
    }
}
</script>

<style scoped>
.problem-complexity {
    margin-top: 20px;
}

.loading {
    text-align: center;
    padding: 40px 0;
}

.complexity-card {
    margin-bottom: 20px;
}

.card-title {
    font-size: 16px;
    font-weight: bold;
}

.metric-item {
    text-align: center;
    padding: 10px 0;
}

.metric-value {
    font-size: 24px;
    font-weight: bold;
    color: #2d8cf0;
}

.metric-label {
    font-size: 14px;
    color: #808695;
}

.keywords-list {
    margin-top: 10px;
}

.keyword-tag {
    margin-right: 8px;
    margin-bottom: 8px;
}

.complexity-gauge {
    text-align: center;
    margin: 20px 0;
}

.gauge-text p {
    margin: 5px 0;
}

.gauge-score {
    font-size: 24px;
    font-weight: bold;
    color: #2d8cf0;
}

.complexity-level {
    text-align: center;
    font-size: 16px;
}

.no-data {
    text-align: center;
    padding: 40px 0;
}

.analysis-time {
    margin-top: 20px;
    text-align: right;
    color: #808695;
    font-size: 12px;
}
</style>