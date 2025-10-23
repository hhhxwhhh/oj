<template>
    <div>
        <Row type="flex" justify="space-around">
            <Col :span="22">
            <Panel shadow>
                <div slot="title">
                    <Icon type="md-git-network" /> 知识点图谱
                </div>
                <div class="graph-container">
                    <div class="graph-header">
                        <h3>知识点依赖关系图</h3>
                        <p>展示各知识点之间的依赖关系，帮助您更好地规划学习路径</p>
                    </div>

                    <div class="graph-controls">
                        <ButtonGroup>
                            <Button @click="zoomIn">
                                <Icon type="md-add" /> 放大
                            </Button>
                            <Button @click="zoomOut">
                                <Icon type="md-remove" /> 缩小
                            </Button>
                            <Button @click="resetView">
                                <Icon type="md-refresh" /> 重置
                            </Button>
                        </ButtonGroup>

                        <div class="category-filters">
                            <span>分类筛选:</span>
                            <CheckboxGroup v-model="selectedCategories" @on-change="filterGraph">
                                <Checkbox v-for="category in categories" :key="category" :label="category">
                                    {{ category }}
                                </Checkbox>
                            </CheckboxGroup>
                        </div>
                    </div>

                    <div id="knowledge-graph" class="graph-content"></div>

                    <div class="graph-info" v-if="selectedNode">
                        <Card>
                            <div slot="title">
                                <Icon type="md-information-circle" /> {{ selectedNode.name }}
                            </div>
                            <div class="node-details">
                                <p><strong>分类:</strong> {{ selectedNode.category }}</p>
                                <p><strong>难度:</strong> {{ getDifficultyText(selectedNode.difficulty) }}</p>
                                <p><strong>描述:</strong> {{ selectedNode.description }}</p>
                                <p><strong>相关题目数:</strong> {{ selectedNode.size - 20 }}</p>
                                <p><strong>推荐权重:</strong> {{ selectedNode.value }}</p>
                            </div>
                        </Card>
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
import echarts from 'echarts'

export default {
    name: 'KnowledgeGraph',
    components: {
        Panel
    },
    data() {
        return {
            chart: null,
            graphData: {
                nodes: [],
                edges: []
            },
            categories: [],
            selectedCategories: [],
            selectedNode: null,
            zoomLevel: 1
        }
    },
    mounted() {
        this.initGraph()
    },
    beforeDestroy() {
        if (this.chart) {
            this.chart.dispose()
        }
    },
    methods: {
        async initGraph() {
            try {
                const res = await api.getKnowledgePointGraph()
                this.graphData = res.data.data

                // 提取所有分类
                this.categories = [...new Set(this.graphData.nodes.map(node => node.category))]
                this.selectedCategories = [...this.categories]

                this.renderGraph()
            } catch (err) {
                this.$error('获取知识点图谱数据失败')
            }
        },

        renderGraph() {
            const chartDom = document.getElementById('knowledge-graph')
            this.chart = echarts.init(chartDom)

            const option = {
                title: {
                    text: '知识点依赖关系图',
                    subtext: '箭头方向表示依赖关系',
                    top: 'bottom',
                    left: 'right'
                },
                tooltip: {
                    formatter: (params) => {
                        if (params.dataType === 'node') {
                            return `
                <strong>${params.data.name}</strong><br/>
                分类: ${params.data.category}<br/>
                难度: ${this.getDifficultyText(params.data.difficulty)}<br/>
                相关题目数: ${params.data.size - 20}
              `
                        } else {
                            return `${params.data.relation}`
                        }
                    }
                },
                legend: [{
                    data: this.categories
                }],
                animationDuration: 1500,
                animationEasingUpdate: 'quinticInOut',
                series: [{
                    name: '知识点图谱',
                    type: 'graph',
                    layout: 'force',
                    force: {
                        repulsion: 100,
                        gravity: 0.1,
                        edgeLength: 200,
                        layoutAnimation: true
                    },
                    data: this.graphData.nodes,
                    links: this.graphData.edges,
                    categories: this.categories.map(category => ({ name: category })),
                    roam: true,
                    draggable: true,
                    focusNodeAdjacency: true,
                    nodeScaleRatio: 0.6,
                    label: {
                        show: true,
                        position: 'right',
                        formatter: '{b}'
                    },
                    lineStyle: {
                        color: 'source',
                        curveness: 0
                    },
                    emphasis: {
                        lineStyle: {
                            width: 10
                        }
                    }
                }]
            }

            this.chart.setOption(option)

            // 监听节点点击事件
            this.chart.on('click', (params) => {
                if (params.dataType === 'node') {
                    this.selectedNode = params.data
                }
            })

            // 监听缩放事件
            this.chart.on('zoom', (params) => {
                this.zoomLevel = params.zoom
            })
        },

        filterGraph() {
            // 根据选中的分类过滤图谱数据
            const filteredNodes = this.graphData.nodes.filter(node =>
                this.selectedCategories.includes(node.category)
            )

            // 过滤边数据，只保留连接选中节点的边
            const nodeIds = new Set(filteredNodes.map(node => node.id))
            const filteredEdges = this.graphData.edges.filter(edge =>
                nodeIds.has(edge.source) && nodeIds.has(edge.target)
            )

            // 更新图表数据
            this.chart.setOption({
                series: [{
                    data: filteredNodes,
                    links: filteredEdges
                }]
            })
        },

        zoomIn() {
            this.chart.dispatchAction({
                type: 'zoom',
                zoom: 1.2
            })
        },

        zoomOut() {
            this.chart.dispatchAction({
                type: 'zoom',
                zoom: 0.8
            })
        },

        resetView() {
            this.chart.dispatchAction({
                type: 'restore'
            })
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
        }
    }
}
</script>

<style lang="less" scoped>
.graph-container {
    .graph-header {
        text-align: center;
        margin-bottom: 20px;

        h3 {
            font-size: 20px;
            margin-bottom: 10px;
        }

        p {
            color: #808695;
        }
    }

    .graph-controls {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        padding: 10px;
        background-color: #f8f8f9;
        border-radius: 4px;

        .category-filters {
            display: flex;
            align-items: center;

            span {
                margin-right: 10px;
                font-weight: bold;
            }

            .ivu-checkbox-group {
                display: flex;
                flex-wrap: wrap;

                .ivu-checkbox-group-item {
                    margin-right: 15px;
                    margin-bottom: 5px;
                }
            }
        }
    }

    .graph-content {
        width: 100%;
        height: 600px;
        border: 1px solid #e8eaec;
        border-radius: 4px;
    }

    .graph-info {
        margin-top: 20px;

        .node-details {
            p {
                margin: 8px 0;
            }
        }
    }
}
</style>