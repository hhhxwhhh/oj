<template>
    <div class="problem-complexity">
        <Panel :padding="15" shadow>
            <div slot="title" class="card-title">
                <Icon type="md-analytics" />
                题目复杂度分析
            </div>

            <div v-if="loading" class="loading">
                <Spin size="large"></Spin>
                <p class="loading-text">正在分析题目复杂度...</p>
            </div>

            <div v-else-if="complexityData" class="complexity-content">
                <div class="complexity-overview">
                    <div class="complexity-score-container">
                        <div class="complexity-score">
                            <p class="score-label">复杂度评分</p>
                            <p class="score-value">{{ complexityData.complexity_score.toFixed(1) }}</p>
                        </div>

                        <div class="complexity-level">
                            <Tag :color="getComplexityLevelColor(complexityData.complexity_score)" class="level-tag">
                                {{ getComplexityLevel(complexityData.complexity_score) }}
                            </Tag>
                            <p class="level-label">复杂度等级</p>
                        </div>
                    </div>

                    <div class="complexity-indicator">
                        <div class="indicator-bar">
                            <div class="indicator-fill" :style="{ width: complexityData.complexity_score + '%' }"></div>
                        </div>
                        <div class="indicator-labels">
                            <span>0</span>
                            <span>25</span>
                            <span>50</span>
                            <span>75</span>
                            <span>100</span>
                        </div>
                    </div>
                </div>

                <div class="complexity-grid">
                    <div class="metric-item">
                        <Icon type="md-document" class="metric-icon" size="24" />
                        <div class="metric-value">{{ complexityData.word_count }}</div>
                        <div class="metric-label">词数</div>
                    </div>

                    <div class="metric-item">
                        <Icon type="md-list" class="metric-icon" size="24" />
                        <div class="metric-value">{{ complexityData.sentence_count }}</div>
                        <div class="metric-label">句子数</div>
                    </div>

                    <div class="metric-item">
                        <Icon type="md-book" class="metric-icon" size="24" />
                        <div class="metric-value">{{ complexityData.readability_score ?
                            complexityData.readability_score.toFixed(1) : 'N/A' }}</div>
                        <div class="metric-label">可读性分数</div>
                    </div>

                    <div class="metric-item">
                        <Icon type="md-school" class="metric-icon" size="24" />
                        <div class="metric-value">{{ complexityData.grade_level || 'N/A' }}</div>
                        <div class="metric-label">年级水平</div>
                    </div>
                </div>

                <div class="keywords-section">
                    <h4>关键词</h4>
                    <div class="keywords-list">
                        <Tag v-for="(keyword, index) in complexityData.keywords.slice(0, 15)" :key="index"
                            :color="getKeywordColor(index)" class="keyword-tag">
                            {{ keyword }}
                        </Tag>
                        <Tag v-if="complexityData.keywords.length > 15" color="default" class="keyword-tag">
                            +{{ complexityData.keywords.length - 15 }} 更多
                        </Tag>
                    </div>
                </div>

                <div v-if="complexityData.last_analysis_time" class="analysis-time">
                    最后分析时间: {{ complexityData.last_analysis_time | localtime }}
                </div>
            </div>

            <div v-else class="no-data">
                <Icon type="ios-alert-outline" size="40" class="no-data-icon" />
                <p>暂无复杂度分析数据</p>
                <Button v-if="isAdminRole" @click="analyzeComplexity" type="primary" :loading="analyzing"
                    class="analyze-btn">
                    <Icon type="md-analytics" />
                    分析题目复杂度
                </Button>
            </div>
        </Panel>
    </div>
</template>

<script>
import api from '@oj/api'
import { mapGetters } from 'vuex'
import Panel from './Panel.vue'

export default {
    name: 'ProblemComplexity',
    components: {
        Panel
    },
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
            if (score >= 80) return '#ed4014' // red
            if (score >= 60) return '#ff9900' // orange
            if (score >= 40) return '#2d8cf0' // blue
            if (score >= 20) return '#52c41a' // green
            return '#19be6b' // cyan
        },

        getKeywordColor(index) {
            const colors = ['#17b3a3', '#007cba', '#722ed1', '#eb2f96', '#fa8c16', '#f5222d', '#52c41a', '#13c2c2'];
            return colors[index % colors.length];
        }
    }
}
</script>

<style scoped lang="less">
.problem-complexity {
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

    .complexity-content {
        .complexity-overview {
            padding: 20px 0;
            border-bottom: 1px solid #e8eaec;
            margin-bottom: 20px;

            .complexity-score-container {
                display: flex;
                justify-content: space-around;
                align-items: center;
                margin-bottom: 20px;

                .complexity-score {
                    text-align: center;

                    .score-value {
                        font-size: 36px;
                        font-weight: 600;
                        color: #2d8cf0;
                        line-height: 1;
                    }

                    .score-label {
                        font-size: 14px;
                        color: #808695;
                        margin-top: 8px;
                    }
                }

                .complexity-level {
                    text-align: center;
                    min-width: 120px;

                    .level-tag {
                        font-size: 18px;
                        padding: 12px 24px;
                        margin-bottom: 8px;
                        font-weight: 500;
                        display: inline-block;
                        min-width: 120px;
                        white-space: normal;
                        word-break: break-word;
                        line-height: 1.4;
                    }

                    .level-label {
                        font-size: 14px;
                        color: #808695;
                    }
                }
            }

            .complexity-indicator {
                .indicator-bar {
                    height: 10px;
                    background-color: #f0f0f0;
                    border-radius: 5px;
                    overflow: hidden;
                    margin-bottom: 8px;
                    position: relative;

                    .indicator-fill {
                        height: 100%;
                        background: linear-gradient(90deg, #52c41a, #2d8cf0, #ff9900, #ed4014);
                        border-radius: 5px;
                        transition: width 0.5s ease;
                    }
                }

                .indicator-labels {
                    display: flex;
                    justify-content: space-between;
                    font-size: 12px;
                    color: #808695;
                }
            }
        }

        .complexity-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;

            .metric-item {
                text-align: center;
                padding: 15px;
                background-color: #fff;
                border-radius: 4px;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                border: 1px solid #e8f4ff;

                .metric-icon {
                    color: #2d8cf0;
                    margin-bottom: 10px;
                }

                .metric-value {
                    font-size: 20px;
                    font-weight: 500;
                    color: #495060;
                    margin-bottom: 5px;
                }

                .metric-label {
                    font-size: 12px;
                    color: #808695;
                }
            }
        }

        .keywords-section {
            margin-bottom: 20px;

            h4 {
                margin: 0 0 10px 0;
                font-size: 15px;
                font-weight: 500;
            }

            .keywords-list {
                .keyword-tag {
                    margin-right: 8px;
                    margin-bottom: 8px;
                    font-weight: 500;
                }
            }
        }

        .analysis-time {
            text-align: right;
            color: #808695;
            font-size: 12px;
            padding-top: 10px;
            border-top: 1px solid #f1f1f1;
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
            margin-bottom: 20px;
        }

        .analyze-btn {
            padding: 6px 20px;
        }
    }
}

// 响应式设计
@media screen and (max-width: 768px) {
    .problem-complexity {
        .complexity-content {
            .complexity-overview {
                .complexity-score-container {
                    flex-direction: column;
                    gap: 20px;
                }

                .complexity-indicator {
                    margin: 0 10px;
                }

                .complexity-level {
                    .level-tag {
                        min-width: 150px;
                    }
                }
            }

            .complexity-grid {
                grid-template-columns: 1fr;
            }
        }
    }
}
</style>