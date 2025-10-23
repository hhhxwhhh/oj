<template>
    <div class="knowledge-point-problems">
        <Row type="flex" justify="space-around">
            <Col :span="22">
            <Panel shadow class="problems-panel">
                <div slot="title" class="panel-title">
                    <Icon type="ios-bookmarks" class="title-icon" />
                    {{ knowledgePoint ? knowledgePoint.name : '知识点题目' }}
                </div>

                <!-- 知识点信息 -->
                <div v-if="knowledgePoint" class="knowledge-point-info">
                    <Card>
                        <div slot="title" class="info-title">
                            <Icon type="ios-information-circle" /> 知识点信息
                        </div>
                        <div class="info-content">
                            <div class="info-row">
                                <span class="label">名称:</span>
                                <span class="value">{{ knowledgePoint.name }}</span>
                            </div>
                            <div class="info-row">
                                <span class="label">分类:</span>
                                <span class="value">{{ knowledgePoint.category }}</span>
                            </div>
                            <div class="info-row">
                                <span class="label">难度:</span>
                                <span class="value">{{ getDifficultyText(knowledgePoint.difficulty) }}</span>
                            </div>
                            <div class="info-row" v-if="knowledgePoint.description">
                                <span class="label">描述:</span>
                                <span class="value">{{ knowledgePoint.description }}</span>
                            </div>
                        </div>
                        <div class="info-actions">
                            <Button @click="goToKnowledgeGraph" type="primary" size="small">
                                <Icon type="ios-git-network" /> 返回知识图谱
                            </Button>
                        </div>
                    </Card>
                </div>

                <!-- 题目列表 -->
                <div class="problems-list">
                    <Panel>
                        <div slot="title">{{ $t('m.Problem_List') }}</div>
                        <Table style="width: 100%; font-size: 16px;" :columns="problemTableColumns" :data="problemList"
                            :loading="loading" disabled-hover>
                        </Table>
                    </Panel>
                    <Pagination :total="total" :page-size.sync="limit" @on-change="getProblemList" :current.sync="page"
                        show-sizer>
                    </Pagination>
                </div>
            </Panel>
            </Col>
        </Row>
    </div>
</template>

<script>
import api from '@oj/api'
import Panel from '@oj/components/Panel.vue'
import Pagination from '@oj/components/Pagination'
import utils from '@/utils/utils'

export default {
    name: 'KnowledgePointProblems',
    components: {
        Panel,
        Pagination
    },
    data() {
        return {
            knowledgePoint: null,
            knowledgePointId: null,
            problemList: [],
            problemTableColumns: [
                {
                    title: '#',
                    key: '_id',
                    width: 80,
                    render: (h, params) => {
                        return h('Button', {
                            props: {
                                type: 'text',
                                size: 'large'
                            },
                            on: {
                                click: () => {
                                    this.$router.push({ name: 'problem-details', params: { problemID: params.row._id } })
                                }
                            },
                            style: {
                                padding: '2px 0'
                            }
                        }, params.row._id)
                    }
                },
                {
                    title: this.$i18n.t('m.Title'),
                    width: 400,
                    render: (h, params) => {
                        return h('Button', {
                            props: {
                                type: 'text',
                                size: 'large'
                            },
                            on: {
                                click: () => {
                                    this.$router.push({ name: 'problem-details', params: { problemID: params.row._id } })
                                }
                            },
                            style: {
                                padding: '2px 0',
                                overflowX: 'auto',
                                textAlign: 'left',
                                width: '100%'
                            }
                        }, params.row.title)
                    }
                },
                {
                    title: this.$i18n.t('m.Level'),
                    render: (h, params) => {
                        let t = params.row.difficulty
                        let color = 'blue'
                        if (t === 'Low') color = 'green'
                        else if (t === 'High') color = 'yellow'
                        return h('Tag', {
                            props: {
                                color: color
                            }
                        }, this.$i18n.t('m.' + params.row.difficulty))
                    }
                },
                {
                    title: this.$i18n.t('m.Total'),
                    key: 'submission_number'
                },
                {
                    title: this.$i18n.t('m.AC_Rate'),
                    render: (h, params) => {
                        return h('span', this.getACRate(params.row.accepted_number, params.row.submission_number))
                    }
                }
            ],
            loading: true,
            page: 1,
            limit: 20,
            total: 0
        }
    },
    mounted() {
        this.knowledgePointId = this.$route.params.knowledgePointId || this.$route.query.knowledge_point
        if (this.knowledgePointId) {
            this.getKnowledgePoint()
            this.getProblemList()
        } else {
            this.$error('缺少知识点参数')
            this.$router.push('/knowledge-points')
        }
    },
    methods: {
        async getKnowledgePoint() {
            try {
                const res = await api.getKnowledgePoint(this.knowledgePointId)
                this.knowledgePoint = res.data.data
            } catch (err) {
                this.$error('获取知识点信息失败')
            }
        },

        async getProblemList() {
            this.loading = true
            try {
                const offset = (this.page - 1) * this.limit
                const res = await api.getKnowledgePointProblems(this.knowledgePointId, offset, this.limit)
                this.total = res.data.data.total
                this.problemList = res.data.data.results
                this.loading = false
            } catch (err) {
                this.loading = false
                this.$error('获取题目列表失败')
            }
        },

        getDifficultyText(difficulty) {
            const difficultyMap = {
                1: '入门',
                2: '简单',
                3: '中等',
                4: '困难',
                5: '专家'
            }
            return difficultyMap[difficulty] || '未知'
        },

        goToKnowledgeGraph() {
            this.$router.push('/knowledge-graph')
        },

        getACRate(acceptedCount, submissionCount) {
            if (submissionCount === 0) return '0%'
            return Math.round(acceptedCount / submissionCount * 100) + '%'
        }
    }
}
</script>

<style lang="less" scoped>
.knowledge-point-problems {
    padding: 20px;

    .problems-panel {
        border-radius: 8px;
        box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);

        .panel-title {
            display: flex;
            align-items: center;

            .title-icon {
                margin-right: 8px;
                font-size: 18px;
                color: #2d8cf0;
            }
        }
    }

    .knowledge-point-info {
        margin-bottom: 20px;

        .info-title {
            display: flex;
            align-items: center;
            font-size: 16px;
            font-weight: bold;
        }

        .info-content {
            .info-row {
                display: flex;
                margin-bottom: 10px;
                padding-bottom: 10px;
                border-bottom: 1px solid #f0f0f0;

                .label {
                    font-weight: 500;
                    min-width: 80px;
                    color: #515a6e;
                }

                .value {
                    flex: 1;
                    color: #17233d;
                }
            }
        }

        .info-actions {
            text-align: right;
            margin-top: 10px;
        }
    }

    .problems-list {
        .ivu-table-wrapper {
            border-radius: 4px;
        }
    }
}
</style>