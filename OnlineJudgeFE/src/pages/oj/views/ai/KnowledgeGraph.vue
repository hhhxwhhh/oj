<template>
    <div class="knowledge-graph-container">
        <Row type="flex" justify="space-around">
            <Col :span="22">
            <Panel shadow class="graph-panel">
                <div slot="title" class="panel-title">
                    <Icon type="ios-git-network" class="title-icon" /> 知识点图谱
                </div>
                <div class="graph-container">
                    <div class="graph-header">
                        <h3>知识点依赖关系图</h3>
                        <p>展示各知识点之间的依赖关系，帮助您更好地规划学习路径</p>
                    </div>

                    <div class="graph-controls">
                        <div class="control-group">
                            <div class="control-title">视图控制</div>
                            <ButtonGroup>
                                <Button @click="zoomIn" type="primary" size="small">
                                    <Icon type="md-add" /> 放大
                                </Button>
                                <Button @click="zoomOut" type="primary" size="small">
                                    <Icon type="md-remove" /> 缩小
                                </Button>
                                <Button @click="resetView" type="primary" size="small">
                                    <Icon type="md-refresh" /> 重置
                                </Button>
                            </ButtonGroup>
                        </div>

                        <div class="control-group">
                            <div class="control-title">分类筛选</div>
                            <div class="category-filters">
                                <CheckboxGroup v-model="selectedCategories" @on-change="filterGraph">
                                    <Checkbox v-for="category in categories" :key="category" :label="category">
                                        {{ category }}
                                    </Checkbox>
                                </CheckboxGroup>
                            </div>
                        </div>

                        <div class="control-group">
                            <div class="control-title">着色模式</div>
                            <RadioGroup v-model="colorMode" @on-change="changeColorMode" class="color-mode-selector"
                                type="button">
                                <Radio label="category">按分类</Radio>
                                <Radio label="difficulty">按难度</Radio>
                                <Radio label="weight">按权重</Radio>
                            </RadioGroup>
                        </div>
                    </div>

                    <div id="knowledge-graph" class="graph-content"></div>

                    <!-- 节点详细信息弹窗 -->
                    <Modal v-model="nodeDetailModalVisible" title="知识点详情" width="600" :footer-hide="true">
                        <div v-if="selectedNodeDetail" class="node-detail-content">
                            <div class="detail-header">
                                <h3>{{ selectedNodeDetail.name }}</h3>
                                <Tag :color="getCategoryColor(selectedNodeDetail.category)">{{
                                    selectedNodeDetail.category }}</Tag>
                            </div>

                            <div class="detail-section">
                                <h4>基本信息</h4>
                                <div class="detail-grid">
                                    <div class="detail-item">
                                        <span class="label">难度等级:</span>
                                        <span class="value">{{ getDifficultyText(selectedNodeDetail.difficulty)
                                            }}</span>
                                    </div>
                                    <div class="detail-item">
                                        <span class="label">推荐权重:</span>
                                        <span class="value">{{ selectedNodeDetail.value }}</span>
                                    </div>
                                    <div class="detail-item">
                                        <span class="label">相关题目数:</span>
                                        <span class="value">{{ selectedNodeDetail.size - 20 }}</span>
                                    </div>
                                    <div class="detail-item">
                                        <span class="label">知识点ID:</span>
                                        <span class="value">{{ selectedNodeDetail.id }}</span>
                                    </div>
                                </div>
                            </div>

                            <div class="detail-section" v-if="selectedNodeDetail.description">
                                <h4>描述</h4>
                                <p class="description">{{ selectedNodeDetail.description }}</p>
                            </div>

                            <div class="detail-section" v-if="nodeRelations.incoming.length > 0">
                                <h4>前置知识点</h4>
                                <div class="relations-list">
                                    <Tag v-for="relation in nodeRelations.incoming" :key="relation.source"
                                        @click.native="showRelatedNodeDetail(relation.source)" class="relation-tag">
                                        {{ getNodeName(relation.source) }}
                                    </Tag>
                                </div>
                            </div>

                            <div class="detail-section" v-if="nodeRelations.outgoing.length > 0">
                                <h4>后续知识点</h4>
                                <div class="relations-list">
                                    <Tag v-for="relation in nodeRelations.outgoing" :key="relation.target"
                                        @click.native="showRelatedNodeDetail(relation.target)" class="relation-tag">
                                        {{ getNodeName(relation.target) }}
                                    </Tag>
                                </div>
                            </div>

                            <div class="detail-actions">
                                <Button type="primary" @click="goToRelatedProblems">查看相关题目</Button>
                                <Button @click="addToLearningPath">添加到学习路径</Button>
                            </div>
                        </div>
                    </Modal>
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
            selectedNodeDetail: null,
            nodeDetailModalVisible: false,
            zoomLevel: 1,
            colorMode: 'category' // 默认按分类着色
        }
    },
    computed: {
        nodeRelations() {
            if (!this.selectedNodeDetail || !this.graphData.edges) {
                return { incoming: [], outgoing: [] }
            }

            const incoming = this.graphData.edges.filter(edge => edge.target === this.selectedNodeDetail.id)
            const outgoing = this.graphData.edges.filter(edge => edge.source === this.selectedNodeDetail.id)

            return { incoming, outgoing }
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

            // 根据着色模式为节点分配颜色
            const nodesWithColors = this.getNodesWithColors()

            const option = {
                title: {
                    text: '知识点依赖关系图',
                    subtext: '箭头方向表示依赖关系',
                    top: 'top',
                    left: 'center',
                    textStyle: {
                        fontSize: 16,
                        fontWeight: 'bold'
                    },
                    subtextStyle: {
                        fontSize: 12,
                        color: '#666'
                    }
                },
                tooltip: {
                    trigger: 'item',
                    triggerOn: 'mousemove',
                    backgroundColor: 'rgba(255, 255, 255, 0.9)',
                    borderColor: '#ddd',
                    borderWidth: 1,
                    borderRadius: 4,
                    padding: 10,
                    textStyle: {
                        color: '#333'
                    },
                    formatter: (params) => {
                        if (params.dataType === 'node') {
                            return `
                                <div class="tooltip-content">
                                    <div class="tooltip-title">${params.data.name}</div>
                                    <div class="tooltip-item">分类: ${params.data.category}</div>
                                    <div class="tooltip-item">难度: ${this.getDifficultyText(params.data.difficulty)}</div>
                                    <div class="tooltip-item">相关题目数: ${params.data.size - 20}</div>
                                </div>
                            `
                        } else {
                            return `<div class="tooltip-content">${params.data.relation}</div>`
                        }
                    }
                },
                legend: [{
                    data: this.categories,
                    bottom: 10,
                    left: 'center'
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
                    data: nodesWithColors,
                    links: this.graphData.edges,
                    categories: this.getCategoriesWithColors(),
                    roam: true,
                    draggable: true,
                    focusNodeAdjacency: true,
                    nodeScaleRatio: 0.6,
                    label: {
                        show: true,
                        position: 'right',
                        formatter: '{b}',
                        fontSize: 12,
                        color: '#333'
                    },
                    lineStyle: {
                        color: 'source',
                        curveness: 0,
                        width: 1.5
                    },
                    emphasis: {
                        lineStyle: {
                            width: 3
                        },
                        label: {
                            fontSize: 14,
                            fontWeight: 'bold'
                        }
                    }
                }]
            }

            this.chart.setOption(option)

            // 监听节点点击事件
            this.chart.on('click', (params) => {
                if (params.dataType === 'node') {
                    this.showNodeDetail(params.data)
                }
            })

            // 监听缩放事件
            this.chart.on('zoom', (params) => {
                this.zoomLevel = params.zoom
            })
        },

        // 显示节点详情
        showNodeDetail(nodeData) {
            this.selectedNodeDetail = nodeData
            this.nodeDetailModalVisible = true
        },

        // 显示相关节点详情
        showRelatedNodeDetail(nodeId) {
            const node = this.graphData.nodes.find(n => n.id === nodeId)
            if (node) {
                this.showNodeDetail(node)
            }
        },

        // 获取节点名称
        getNodeName(nodeId) {
            const node = this.graphData.nodes.find(n => n.id === nodeId)
            return node ? node.name : '未知节点'
        },

        // 获取分类颜色
        getCategoryColor(category) {
            const categoryColors = [
                'blue', 'green', 'yellow', 'red', 'cyan',
                'geekblue', 'orange', 'purple', 'pink', 'volcano'
            ]

            const categoryIndex = this.categories.indexOf(category)
            return categoryColors[categoryIndex % categoryColors.length]
        },

        // 根据着色模式获取带颜色的节点
        getNodesWithColors() {
            switch (this.colorMode) {
                case 'difficulty':
                    return this.getNodesColoredByDifficulty()
                case 'weight':
                    return this.getNodesColoredByWeight()
                case 'category':
                default:
                    return this.getNodesColoredByCategory()
            }
        },

        // 按分类着色
        getNodesColoredByCategory() {
            const categoryColors = [
                '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de',
                '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#2ab7ca'
            ]

            return this.graphData.nodes.map((node) => {
                const categoryIndex = this.categories.indexOf(node.category)
                return {
                    ...node,
                    itemStyle: {
                        color: categoryColors[categoryIndex % categoryColors.length]
                    }
                }
            })
        },

        // 按难度着色
        getNodesColoredByDifficulty() {
            const difficultyColors = {
                1: '#91cc75', // 入门 - 绿色
                2: '#fac858', // 简单 - 黄色
                3: '#5470c6', // 中等 - 蓝色
                4: '#fc8452', // 困难 - 橙色
                5: '#ee6666'  // 专家 - 红色
            }

            return this.graphData.nodes.map((node) => {
                return {
                    ...node,
                    itemStyle: {
                        color: difficultyColors[node.difficulty] || '#666'
                    }
                }
            })
        },

        // 按权重着色
        getNodesColoredByWeight() {
            // 计算权重范围
            const weights = this.graphData.nodes.map(node => node.value || 0)
            const minWeight = Math.min(...weights)
            const maxWeight = Math.max(...weights)
            const range = maxWeight - minWeight || 1

            return this.graphData.nodes.map((node) => {
                // 根据权重计算颜色（从浅蓝到深蓝）
                const ratio = (node.value - minWeight) / range
                const r = Math.floor(84 + (26 - 84) * ratio)   // 54 -> 1a
                const g = Math.floor(112 + (102 - 112) * ratio) // 70 -> 66
                const b = Math.floor(198 + (206 - 198) * ratio) // c6 -> ce
                const color = `rgb(${r}, ${g}, ${b})`

                return {
                    ...node,
                    itemStyle: {
                        color: color
                    }
                }
            })
        },

        // 获取带颜色的分类
        getCategoriesWithColors() {
            if (this.colorMode !== 'category') {
                return this.categories.map(category => ({ name: category }))
            }

            const categoryColors = [
                '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de',
                '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#2ab7ca'
            ]

            return this.categories.map((category, index) => ({
                name: category,
                itemStyle: {
                    color: categoryColors[index % categoryColors.length]
                }
            }))
        },

        // 改变着色模式
        changeColorMode() {
            this.renderGraph()
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
        },

        // 跳转到相关题目
        goToRelatedProblems() {
            if (this.selectedNodeDetail) {
                this.$router.push(`/problem?knowledge_point=${this.selectedNodeDetail.id}`)
            }
        },

        // 添加到学习路径
        addToLearningPath() {
            if (this.selectedNodeDetail) {
                this.$Message.success(`已将 "${this.selectedNodeDetail.name}" 添加到学习路径`)
                // 这里可以调用API将知识点添加到用户的学习路径中
            }
        }
    }
}
</script>

<style lang="less" scoped>
.knowledge-graph-container {
    padding: 20px;

    .graph-panel {
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

    .graph-container {
        .graph-header {
            text-align: center;
            margin-bottom: 20px;
            padding: 15px;
            background: linear-gradient(120deg, #f0f8ff, #e6f7ff);
            border-radius: 6px;

            h3 {
                font-size: 22px;
                margin-bottom: 10px;
                color: #17233d;
                font-weight: 600;
            }

            p {
                color: #515a6e;
                font-size: 14px;
            }
        }

        .graph-controls {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-bottom: 20px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 6px;
            border: 1px solid #e8eaec;

            .control-group {
                flex: 1;
                min-width: 200px;

                .control-title {
                    font-weight: 600;
                    margin-bottom: 8px;
                    color: #17233d;
                    font-size: 14px;
                }

                .category-filters {
                    .ivu-checkbox-group {
                        display: flex;
                        flex-wrap: wrap;
                        gap: 10px;

                        .ivu-checkbox-group-item {
                            margin-right: 0;
                        }
                    }
                }

                .color-mode-selector {
                    /deep/ .ivu-radio-group-button .ivu-radio-wrapper {
                        border-color: #dcdee2;
                        border-width: 1px;
                        border-radius: 4px !important;
                        margin-right: 5px;
                    }

                    /deep/ .ivu-radio-group-button .ivu-radio-wrapper-checked {
                        background: #2d8cf0;
                        border-color: #2d8cf0;
                        color: white;
                    }
                }
            }
        }

        .graph-content {
            width: 100%;
            height: 600px;
            border: 1px solid #e8eaec;
            border-radius: 6px;
            background-color: #fff;
        }
    }
}

// 节点详情弹窗样式
.node-detail-content {
    .detail-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        padding-bottom: 15px;
        border-bottom: 1px solid #e8eaec;

        h3 {
            margin: 0;
            font-size: 20px;
            color: #17233d;
        }
    }

    .detail-section {
        margin-bottom: 20px;

        h4 {
            margin: 0 0 10px 0;
            font-size: 16px;
            color: #17233d;
            font-weight: 600;
        }

        .detail-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;

            .detail-item {
                display: flex;
                padding: 8px 0;

                .label {
                    font-weight: 500;
                    color: #515a6e;
                    min-width: 100px;
                }

                .value {
                    flex: 1;
                    color: #17233d;
                }
            }
        }

        .description {
            color: #515a6e;
            line-height: 1.6;
            margin: 0;
        }

        .relations-list {
            .relation-tag {
                margin-right: 8px;
                margin-bottom: 8px;
                cursor: pointer;

                &:hover {
                    opacity: 0.8;
                }
            }
        }
    }

    .detail-actions {
        display: flex;
        justify-content: flex-end;
        gap: 10px;
        padding-top: 20px;
        border-top: 1px solid #e8eaec;
    }
}

// 自定义提示框样式
.tooltip-content {
    .tooltip-title {
        font-weight: bold;
        margin-bottom: 5px;
        color: #17233d;
    }

    .tooltip-item {
        margin: 3px 0;
        font-size: 12px;
    }
}

// 响应式设计
@media (max-width: 768px) {
    .knowledge-graph-container {
        padding: 10px;

        .graph-controls {
            flex-direction: column;
            gap: 15px;
        }

        .graph-content {
            height: 400px;
        }

        .node-detail-content {
            .detail-grid {
                grid-template-columns: 1fr;
            }
        }
    }
}
</style>