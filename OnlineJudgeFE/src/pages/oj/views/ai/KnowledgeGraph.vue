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
                            <RadioGroup v-model="colorMode" @on-change="changeColorMode">
                                <Radio label="category">按分类着色</Radio>
                                <Radio label="difficulty">按难度着色</Radio>
                                <Radio label="weight">按权重着色</Radio>
                                <Radio label="proficiency">按掌握状态着色</Radio>
                                <Radio label="similarity">按相似度着色</Radio> <!-- 新增 -->
                            </RadioGroup>
                        </div>

                        <!-- 新增GNN功能控制 -->
                        <div class="control-group">
                            <div class="control-title">GNN功能</div>
                            <div class="gnn-controls">
                                <Button @click="findSimilarPoints" :disabled="!selectedNodeDetail" size="small">
                                    <Icon type="md-git-compare" /> 相似知识点
                                </Button>
                                <Button @click="showLearningPath" :disabled="!selectedNodeDetail" size="small"
                                    style="margin-left: 5px;">
                                    <Icon type="md-git-network" /> 学习路径
                                </Button>
                            </div>
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
                                    <div class="detail-item" v-if="selectedNodeDetail.proficiency_level !== undefined">
                                        <span class="label">掌握程度:</span>
                                        <span class="value">
                                            <Progress :percent="Math.round(selectedNodeDetail.proficiency_level * 100)"
                                                :stroke-width="8" />
                                            <span>{{ Math.round(selectedNodeDetail.proficiency_level * 100) }}%</span>
                                        </span>
                                    </div>
                                    <div class="detail-item"
                                        v-if="selectedNodeDetail.correct_attempts !== undefined && selectedNodeDetail.total_attempts !== undefined">
                                        <span class="label">答题情况:</span>
                                        <span class="value">{{ selectedNodeDetail.correct_attempts }}/{{
                                            selectedNodeDetail.total_attempts }}</span>
                                    </div>

                                    <!-- 新增GNN信息 -->
                                    <div class="detail-item" v-if="selectedNodeDetail.importance !== undefined">
                                        <span class="label">重要性:</span>
                                        <span class="value">{{ selectedNodeDetail.importance.toFixed(2) }}</span>
                                    </div>
                                    <div class="detail-item" v-if="selectedNodeDetail.frequency !== undefined">
                                        <span class="label">出现频率:</span>
                                        <span class="value">{{ selectedNodeDetail.frequency }}</span>
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

                            <!-- 新增相似知识点推荐 -->
                            <div class="detail-section" v-if="similarPoints.length > 0">
                                <h4>相似知识点 (基于GNN)</h4>
                                <div class="relations-list">
                                    <Tag v-for="point in similarPoints" :key="point.id"
                                        @click.native="showRelatedNodeDetail(point.id)" class="relation-tag"
                                        :color="getSimilarityColor(point.similarity)">
                                        {{ point.name }} ({{ (point.similarity * 100).toFixed(1) }}%)
                                    </Tag>
                                </div>
                            </div>

                            <div class="detail-actions">
                                <Button type="primary" @click="goToRelatedProblems">查看相关题目</Button>
                                <Button @click="addToLearningPath">添加到学习路径</Button>
                                <Button @click="findSimilarPoints" :loading="similarPointsLoading">查找相似知识点</Button>
                            </div>
                        </div>
                    </Modal>

                    <!-- 新增相似知识点弹窗 -->
                    <Modal v-model="similarPointsModalVisible" title="相似知识点推荐" width="800" :footer-hide="true">
                        <div v-if="similarPoints.length > 0">
                            <p>基于图神经网络计算的相似知识点：</p>
                            <Table :columns="similarPointsColumns" :data="similarPoints" />
                        </div>
                        <div v-else>
                            <p v-if="!similarPointsLoading">暂无相似知识点推荐</p>
                            <p v-else>正在计算相似知识点...</p>
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
import { Progress, Table } from 'iview'

export default {
    name: 'KnowledgeGraph',
    components: {
        Panel,
        Progress,
        Table
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
            colorMode: 'proficiency',

            similarPoints: [],
            similarPointsLoading: false,
            similarPointsModalVisible: false,
            similarPointsColumns: [
                {
                    title: '知识点',
                    key: 'name'
                },
                {
                    title: '相似度',
                    key: 'similarity',
                    render: (h, params) => {
                        return h('span', `${(params.row.similarity * 100).toFixed(1)}%`)
                    }
                },
                {
                    title: '难度',
                    key: 'difficulty',
                    render: (h, params) => {
                        return h('span', this.getDifficultyText(params.row.difficulty))
                    }
                },
                {
                    title: '分类',
                    key: 'category'
                }
            ]
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
        // 使用setTimeout确保DOM完全渲染后再初始化图表
        setTimeout(() => {
            this.initGraph()
        }, 500)
        window.addEventListener('resize', this.handleResize)
    },
    beforeDestroy() {
        // 移除窗口大小变化监听器
        window.removeEventListener('resize', this.handleResize)

        // 销毁图表实例
        if (this.chart) {
            this.chart.dispose()
            this.chart = null
        }
    },
    methods: {
        handleResize() {
            // 确保图表实例存在且容器有效
            if (this.chart && this.chart.getDom()) {
                try {
                    this.chart.resize()
                } catch (error) {
                    console.warn('图表resize操作失败:', error)
                }
            }
        },
        async initGraph() {
            try {
                const res = await api.getKnowledgePointGraph()
                this.graphData = res.data.data

                // 检查数据是否有效
                if (!this.graphData || !this.graphData.nodes || !this.graphData.edges) {
                    console.error('知识点图谱数据格式不正确:', this.graphData)
                    this.$error('知识点图谱数据格式不正确')
                    return
                }

                // 检查节点中的embedding数据
                console.log('获取到的节点数量:', this.graphData.nodes.length);
                const nodesWithEmbedding = this.graphData.nodes.filter(node => node.embedding).length;
                console.log('包含embedding数据的节点数量:', nodesWithEmbedding);

                if (this.graphData.nodes.length > 0) {
                    console.log('第一个节点的embedding:', this.graphData.nodes[0].embedding);
                }

                // 确保节点ID为字符串类型
                this.graphData.nodes = this.graphData.nodes.map(node => ({
                    ...node,
                    id: String(node.id)
                }))

                // 确保边的source和target为字符串类型
                this.graphData.edges = this.graphData.edges.map(edge => ({
                    ...edge,
                    source: String(edge.source),
                    target: String(edge.target)
                }))

                // 提取所有分类
                this.categories = [...new Set(this.graphData.nodes.map(node => node.category))]
                this.selectedCategories = [...this.categories]

                this.renderGraph()
            } catch (err) {
                this.$error('获取知识点图谱数据失败: ' + (err.message || err))
            }
        },
        renderGraph() {
            const chartDom = document.getElementById('knowledge-graph')
            if (!chartDom) {
                return
            }

            // 如果已存在图表实例，先销毁
            if (this.chart) {
                this.chart.dispose()
            }

            this.chart = echarts.init(chartDom)

            // 根据着色模式为节点分配颜色
            const nodesWithColors = this.getNodesWithColors()

            // 优化力导向布局参数
            const nodeCount = nodesWithColors.length
            let repulsion = 1000
            let edgeLength = 200

            // 根据节点数量调整布局参数
            if (nodeCount > 100) {
                repulsion = nodeCount * 10
                edgeLength = 100
            } else if (nodeCount > 50) {
                repulsion = nodeCount * 15
                edgeLength = 150
            }

            const option = {
                backgroundColor: '#fff',
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
                            let proficiencyInfo = '';
                            if (params.data.proficiency_level !== undefined) {
                                const proficiencyPercent = Math.round(params.data.proficiency_level * 100);
                                proficiencyInfo = `<div class="tooltip-item">掌握程度: ${proficiencyPercent}%</div>`;

                                if (params.data.correct_attempts !== undefined && params.data.total_attempts !== undefined) {
                                    proficiencyInfo += `<div class="tooltip-item">答题情况: ${params.data.correct_attempts}/${params.data.total_attempts}</div>`;
                                }
                            }

                            // 新增GNN信息
                            let gnnInfo = '';
                            if (params.data.importance !== undefined) {
                                gnnInfo = `<div class="tooltip-item">重要性: ${params.data.importance.toFixed(2)}</div>`;
                            }
                            if (params.data.frequency !== undefined) {
                                gnnInfo += `<div class="tooltip-item">出现频率: ${params.data.frequency}</div>`;
                            }

                            return `
                                <div class="tooltip-content">
                                    <div class="tooltip-title">${params.data.name}</div>
                                    <div class="tooltip-item">分类: ${params.data.category}</div>
                                    <div class="tooltip-item">难度: ${this.getDifficultyText(params.data.difficulty)}</div>
                                    <div class="tooltip-item">相关题目数: ${params.data.size - 20}</div>
                                    ${proficiencyInfo}
                                    ${gnnInfo}
                                </div>
                            `
                        } else {
                            return `<div class="tooltip-content">${params.data.relation}</div>`
                        }
                    }
                },
                legend: [{
                    data: this.colorMode === 'proficiency' ?
                        ['未掌握', '部分掌握', '已掌握'] :
                        (this.colorMode === 'similarity' ?
                            ['低相似度', '中相似度', '高相似度'] :
                            this.categories),
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
                        repulsion: repulsion,
                        gravity: 0.1,
                        edgeLength: edgeLength,
                        layoutAnimation: true,
                        preventOverlap: true
                    },
                    data: nodesWithColors,
                    links: this.graphData.edges,
                    categories: this.getCategoriesWithColors(),
                    roam: true,
                    draggable: true,
                    focusNodeAdjacency: true,
                    nodeScaleRatio: 0.6,
                    // 调整标签显示策略，避免标签重叠
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
                        width: 1.5,
                        opacity: 0.7
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
            this.chart.on('click', async (params) => {
                if (params.dataType === 'node') {
                    console.log('点击节点:', params.data);
                    // 确保选中的节点数据完整（从graphData中获取最新的数据）
                    const selectedNode = this.graphData.nodes.find(node => node.id === params.data.id);
                    if (selectedNode) {
                        this.showNodeDetail(selectedNode);
                    } else {
                        this.showNodeDetail(params.data);
                    }

                    // 如果当前处于相似度着色模式，重新加载相似节点数据
                    if (this.colorMode === 'similarity') {
                        console.log('重新计算相似度...');
                        await this.findSimilarPointsWithoutUI();
                        // 重新渲染以更新颜色
                        this.renderGraph();
                    }
                }
            })

            // 监听缩放事件
            this.chart.on('zoom', (params) => {
                this.zoomLevel = params.zoom
            })

            // 添加图表渲染完成事件监听
            this.chart.on('rendered', () => {
            })

            // 强制重新渲染
            setTimeout(() => {
                this.chart.resize()
            }, 100)
        },

        // 显示节点详情
        showNodeDetail(nodeData) {
            this.selectedNodeDetail = nodeData
            this.nodeDetailModalVisible = true

            // 清空之前的相似知识点
            this.similarPoints = []
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
                case 'proficiency':
                    return this.getNodesColoredByProficiency()
                case 'similarity': // 新增
                    return this.getNodesColoredBySimilarity()
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

        getNodesColoredByProficiency() {
            return this.graphData.nodes.map((node) => {
                let color = '#ee6666';
                let category = '未掌握'; // 默认分类

                if (node.proficiency_level !== undefined) {
                    if (node.proficiency_level >= 0.7) {
                        color = '#91cc75'; // 绿色，表示已掌握
                        category = '已掌握';
                    } else if (node.proficiency_level >= 0.3) {
                        color = '#fac858'; // 黄色，表示部分掌握
                        category = '部分掌握';
                    }
                }

                return {
                    ...node,
                    category: category, // 设置分类属性
                    itemStyle: {
                        color: color
                    }
                }
            })
        },
        getNodesColoredBySimilarity() {
            console.log('开始按相似度着色，选中节点:', this.selectedNodeDetail);

            // 如果没有选中节点，则使用默认颜色
            if (!this.selectedNodeDetail) {
                console.log('未选择节点，使用默认颜色');
                return this.graphData.nodes.map(node => ({
                    ...node,
                    category: '未选择节点',
                    itemStyle: {
                        color: '#5470c6'
                    }
                }));
            }

            // 检查选中节点是否有embedding数据
            console.log('选中节点所有字段:', Object.keys(this.selectedNodeDetail));
            console.log('选中节点embedding字段:', this.selectedNodeDetail.embedding);
            console.log('选中节点embedding类型:', typeof this.selectedNodeDetail.embedding);

            if (!this.selectedNodeDetail.embedding || this.selectedNodeDetail.embedding.length === 0) {
                this.$Message.warning('当前选中节点缺少向量数据，无法计算相似度');
                console.warn('当前选中节点缺少向量数据:', this.selectedNodeDetail);
                return this.graphData.nodes.map(node => ({
                    ...node,
                    category: '数据缺失',
                    itemStyle: {
                        color: '#cccccc'
                    }
                }));
            }

            console.log('开始计算相似度，选中节点ID:', this.selectedNodeDetail.id);
            const embeddingVector = this.selectedNodeDetail.embedding.split(',');
            console.log('选中节点embedding向量:', embeddingVector);
            console.log('选中节点embedding维度:', embeddingVector.length);

            // 为每个节点计算与选中节点的相似度
            const nodesWithSimilarity = this.graphData.nodes.map(node => {
                let color = '#cccccc'; // 默认灰色
                let category = '低相似度';

                if (node.id === this.selectedNodeDetail.id) {
                    // 选中节点使用特殊颜色
                    color = '#1890ff';
                    category = '当前节点';
                } else if (node.embedding && node.embedding.length > 0) {
                    // 计算基于嵌入向量的相似度
                    try {
                        const similarity = this.calculateEmbeddingSimilarity(
                            node.embedding,
                            this.selectedNodeDetail.embedding
                        );

                        console.log(`节点 ${node.id} 相似度:`, similarity);

                        if (similarity > 0.8) {
                            color = '#91cc75'; // 高相似度 - 绿色
                            category = '高相似度';
                        } else if (similarity > 0.5) {
                            color = '#fac858'; // 中相似度 - 黄色
                            category = '中相似度';
                        } else {
                            category = '低相似度';
                        }
                    } catch (e) {
                        console.error('计算节点相似度时出错:', node.id, e);
                        category = '计算错误';
                    }
                } else {
                    // 如果没有嵌入向量数据，则使用默认分类
                    console.warn('节点缺少向量数据:', node.id);
                    category = '无向量数据';
                }

                return {
                    ...node,
                    category: category,
                    itemStyle: {
                        color: color
                    }
                }
            });

            console.log('相似度计算完成，节点分类:',
                [...new Set(nodesWithSimilarity.map(n => n.category))]);

            return nodesWithSimilarity;
        },



        calculateEmbeddingSimilarity(embedding1, embedding2) {
            try {
                // 检查输入数据
                if (!embedding1 || !embedding2) {
                    throw new Error('向量数据为空');
                }

                const vec1 = embedding1.split(',').map(Number);
                const vec2 = embedding2.split(',').map(Number);

                // 检查向量维度是否一致
                if (vec1.length !== vec2.length) {
                    console.warn('向量维度不一致:', vec1.length, 'vs', vec2.length);
                    return 0;
                }

                // 检查是否有非数字值
                if (vec1.some(isNaN) || vec2.some(isNaN)) {
                    throw new Error('向量包含非数字值');
                }

                // 计算余弦相似度
                let dotProduct = 0;
                let norm1 = 0;
                let norm2 = 0;

                for (let i = 0; i < vec1.length; i++) {
                    dotProduct += vec1[i] * vec2[i];
                    norm1 += vec1[i] * vec1[i];
                    norm2 += vec2[i] * vec2[i];
                }

                if (norm1 === 0 || norm2 === 0) {
                    console.warn('向量模长为0');
                    return 0;
                }

                const similarity = dotProduct / (Math.sqrt(norm1) * Math.sqrt(norm2));
                console.log('计算得到的相似度:', similarity);
                return similarity;
            } catch (e) {
                console.error('计算嵌入向量相似度失败:', e);
                return 0;
            }
        },


        // 获取带颜色的分类
        getCategoriesWithColors() {
            if (this.colorMode === 'proficiency') {
                return [
                    { name: '未掌握', itemStyle: { color: '#ee6666' } },
                    { name: '部分掌握', itemStyle: { color: '#fac858' } },
                    { name: '已掌握', itemStyle: { color: '#91cc75' } }
                ]
            }

            if (this.colorMode === 'similarity') {
                return [
                    { name: '当前节点', itemStyle: { color: '#1890ff' } },
                    { name: '高相似度', itemStyle: { color: '#91cc75' } },
                    { name: '中相似度', itemStyle: { color: '#fac858' } },
                    { name: '低相似度', itemStyle: { color: '#cccccc' } }
                ]
            }

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
        async changeColorMode() {
            console.log('切换着色模式到:', this.colorMode);
            // 如果切换到相似度模式并且已有选中节点，则自动加载相似节点数据
            if (this.colorMode === 'similarity') {
                if (this.selectedNodeDetail) {
                    console.log('加载相似节点数据...');
                    await this.findSimilarPointsWithoutUI();
                } else {
                    this.$Message.info('请先选择一个节点以查看相似度着色');
                }
            }
            this.renderGraph();
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
                this.$router.push({
                    name: 'singleknowledge-point-problems',
                    params: { knowledgePointId: this.selectedNodeDetail.id }
                })
            }
        },


        addToLearningPath() {
            if (this.selectedNodeDetail) {
                this.$Message.success(`已将 "${this.selectedNodeDetail.name}" 添加到学习路径`)
                // 这里可以调用API将知识点添加到用户的学习路径中
            }
        },

        async findSimilarPointsWithoutUI() {
            if (!this.selectedNodeDetail) {
                return;
            }

            try {
                const res = await api.getRelatedKnowledgePoints({
                    knowledge_point_id: this.selectedNodeDetail.id,
                    top_k: 10
                });

                this.similarPoints = res.data.data.map(point => ({
                    ...point,
                    id: String(point.id) // 确保ID为字符串
                }));

                // 高亮显示相似节点
                this.highlightSimilarNodes();
            } catch (err) {
                console.error('获取相似知识点失败:', err);
            }
        },

        // 高亮显示相似节点（新增）
        highlightSimilarNodes() {
            if (!this.chart || !this.similarPoints.length) return;

            // 重置所有节点样式
            this.chart.setOption({
                series: [{
                    data: this.getNodesWithColors()
                }]
            });

            // 高亮相似节点
            const option = {
                series: [{
                    data: this.graphData.nodes.map(node => {
                        const isSimilar = this.similarPoints.some(point => point.id === node.id);
                        const isSelected = this.selectedNodeDetail && this.selectedNodeDetail.id === node.id;

                        if (isSimilar || isSelected) {
                            return {
                                ...node,
                                symbolSize: node.symbolSize * 1.5,
                                itemStyle: {
                                    ...node.itemStyle,
                                    borderWidth: isSelected ? 3 : 2,
                                    borderColor: isSelected ? '#1890ff' : '#52c41a'
                                }
                            };
                        }
                        return node;
                    })
                }]
            };

            this.chart.setOption(option);
        },

        // 获取相似度颜色（新增）
        getSimilarityColor(similarity) {
            if (similarity > 0.8) return 'green';
            if (similarity > 0.6) return 'blue';
            if (similarity > 0.4) return 'orange';
            return 'red';
        },

        // 显示学习路径（新增）
        showLearningPath() {
            if (!this.selectedNodeDetail) {
                this.$Message.warning('请先选择一个知识点');
                return;
            }

            this.$Message.info('学习路径功能将在后续版本中实现');
            // 这里可以调用API获取学习路径建议
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

                .gnn-controls {
                    display: flex;
                    gap: 5px;
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