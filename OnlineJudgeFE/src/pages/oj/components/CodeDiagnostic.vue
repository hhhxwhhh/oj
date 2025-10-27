<template>
    <div class="code-diagnostic">
        <!-- 实时诊断和建议面板 -->
        <div v-if="visible" class="diagnostic-panel" ref="diagnosticPanel"
            :class="{ 'minimized': minimized, 'docked': docked }" :style="panelStyle">
            <div class="diagnostic-panel-header" @mousedown="startDrag">
                <Icon type="md-medical"></Icon>
                <span>{{ $t('m.Real_Time_Diagnostic') }}</span>
                <div class="diagnostic-panel-actions">
                    <Button type="text" size="small" @click="toggleDock">
                        <Icon :type="docked ? 'md-square-outline' : 'md-move'"></Icon>
                    </Button>
                    <Button type="text" size="small" @click="toggleMinimize">
                        <Icon :type="minimized ? 'plus-round' : 'minus-round'"></Icon>
                    </Button>
                    <Button type="text" size="small" @click="visible = false">
                        <Icon type="close"></Icon>
                    </Button>
                </div>
            </div>

            <div v-show="!minimized" class="diagnostic-panel-content">
                <Tabs value="diagnosis" @on-click="handleTabChange" :animated="false">
                    <TabPane :label="diagnosisTabLabel" name="diagnosis">
                        <div v-if="diagnosisIssues.length > 0" class="real-time-diagnosis">
                            <div class="diagnosis-content">
                                <div v-for="(group, type) in groupedDiagnosisIssues" :key="type" class="diagnosis-group"
                                    :class="type">
                                    <div class="group-header">
                                        <Icon :type="getIssueIcon(type)" :style="{ color: getIssueColor(type) }"></Icon>
                                        <span class="group-title">{{ getIssueTypeName(type) }}</span>
                                        <Tag :color="getIssueColor(type)">{{ group.length }}</Tag>
                                    </div>
                                    <ul class="issue-list">
                                        <li v-for="(issue, index) in group" :key="index" class="issue-item">
                                            {{ issue.message }}
                                        </li>
                                    </ul>
                                </div>
                            </div>
                            <div class="panel-footer">
                                <Button size="small" @click="handleRefreshDiagnosis" type="ghost">
                                    <Icon type="refresh"></Icon>
                                    {{ $t('m.Refresh') }}
                                </Button>
                            </div>
                        </div>
                        <div v-else class="no-issues">
                            <Icon type="ios-checkmark-circle" size="30" color="#19be6b"></Icon>
                            <p>{{ $t('m.No_issues_found') }}</p>
                        </div>
                    </TabPane>
                    <TabPane :label="suggestionsTabLabel" name="suggestions">
                        <div v-if="organizedSuggestions.length > 0" class="real-time-suggestions">
                            <div class="suggestions-content">
                                <div v-for="(category, index) in organizedSuggestions" :key="index"
                                    class="suggestion-category">
                                    <div class="category-header">
                                        <Icon :type="getCategoryIcon(category.type)"
                                            :style="{ color: getCategoryColor(category.type) }"></Icon>
                                        <span class="category-title">{{ getCategoryName(category.type) }}</span>
                                        <Tag :color="getCategoryColor(category.type)">{{ category.items.length }}</Tag>
                                    </div>
                                    <div class="category-items">
                                        <!-- 使用 Markdown 渲染建议内容 -->
                                        <div v-if="isSimpleList(category.items)" class="simple-list">
                                            <div v-for="(item, itemIndex) in category.items" :key="itemIndex"
                                                class="simple-item">
                                                <Icon type="ios-checkmark" class="check-icon"></Icon>
                                                <span v-if="typeof item === 'string'">{{ item }}</span>
                                                <span v-else>{{ item.text || item.description }}</span>
                                            </div>
                                        </div>
                                        <!-- 对于复杂内容，仍然使用原有格式 -->
                                        <div v-else>
                                            <div v-for="(item, itemIndex) in category.items" :key="itemIndex"
                                                class="suggestion-item">
                                                <div class="suggestion-content">
                                                    <div class="suggestion-text">{{ item.text || item }}</div>
                                                    <div v-if="item.description" class="suggestion-description">{{
                                                        item.description }}</div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="panel-footer">
                                <Button size="small" @click="handleRefreshSuggestions" type="ghost">
                                    <Icon type="refresh"></Icon>
                                    {{ $t('m.Refresh') }}
                                </Button>
                            </div>
                        </div>
                        <div v-else class="no-issues">
                            <Icon type="ios-checkmark-circle" size="30" color="#19be6b"></Icon>
                            <p>{{ $t('m.No_suggestions_available') }}</p>
                        </div>
                    </TabPane>
                </Tabs>
            </div>
        </div>

        <!-- 面板显示按钮 -->
        <div v-if="!visible" class="show-panel-button" @click="showPanel">
            <Button type="primary" shape="circle" icon="md-medical">
                {{ $t('m.Diagnostics') }}
                <Badge v-if="issueCount > 0" :count="issueCount" :overflow-count="99" />
            </Button>
        </div>
    </div>
</template>
<script>
export default {
    name: 'CodeDiagnostic',
    props: {
        // 诊断和建议相关属性
        diagnosisIssues: {
            type: Array,
            default: () => []
        },
        suggestions: {
            type: Array,
            default: () => []
        }
    },
    data() {
        return {
            visible: false,
            minimized: false,
            docked: true,
            // 拖拽相关数据
            isDragging: false,
            dragOffset: { x: 0, y: 0 },
            // 面板位置
            position: {
                right: '20px',
                top: '100px'
            }
        }
    },
    mounted() {
        this.initPanelPosition()
        // 监听窗口大小变化
        window.addEventListener('resize', this.handleWindowResize)
    },
    computed: {
        groupedDiagnosisIssues() {
            const groups = {}
            this.diagnosisIssues.forEach(issue => {
                if (!groups[issue.type]) {
                    groups[issue.type] = []
                }
                groups[issue.type].push(issue)
            })
            return groups
        },
        diagnosisTabLabel() {
            const count = this.diagnosisIssues.length;
            return () => {
                return this.$createElement('div', [
                    this.$createElement('span', this.$t('m.Real_Time_Diagnosis')),
                    count > 0 ? this.$createElement('Badge', {
                        props: {
                            count: count,
                            type: 'error'
                        },
                        style: {
                            marginLeft: '5px'
                        }
                    }) : null
                ])
            }
        },
        suggestionsTabLabel() {
            const count = this.suggestions.length;
            return () => {
                return this.$createElement('div', [
                    this.$createElement('span', this.$t('m.Real_Time_Suggestions')),
                    count > 0 ? this.$createElement('Badge', {
                        props: {
                            count: count,
                            type: 'primary'
                        },
                        style: {
                            marginLeft: '5px'
                        }
                    }) : null
                ])
            }
        },
        issueCount() {
            return this.diagnosisIssues.length + this.suggestions.length
        },
        panelStyle() {
            return {
                right: this.position.right,
                left: this.position.left,
                top: this.position.top
            }
        },
        organizedSuggestions() {
            // 对suggestions进行分类组织
            if (!this.suggestions || this.suggestions.length === 0) {
                return [];
            }

            // 检查suggestions是否是已分类的结构
            if (this.suggestions.length > 0 &&
                (typeof this.suggestions[0] === 'object') &&
                (this.suggestions[0].hasOwnProperty('completions') ||
                    this.suggestions[0].hasOwnProperty('suggestions') ||
                    this.suggestions[0].hasOwnProperty('issues') ||
                    this.suggestions[0].hasOwnProperty('knowledge_points'))) {

                // 已经是分类结构，直接使用
                const categories = [];

                this.suggestions.forEach(suggestionGroup => {
                    if (suggestionGroup.completions && suggestionGroup.completions.length) {
                        categories.push({
                            type: 'completions',
                            items: suggestionGroup.completions
                        });
                    }

                    if (suggestionGroup.suggestions && suggestionGroup.suggestions.length) {
                        categories.push({
                            type: 'suggestions',
                            items: suggestionGroup.suggestions
                        });
                    }

                    if (suggestionGroup.issues && suggestionGroup.issues.length) {
                        categories.push({
                            type: 'issues',
                            items: suggestionGroup.issues
                        });
                    }

                    if (suggestionGroup.knowledge_points && suggestionGroup.knowledge_points.length) {
                        categories.push({
                            type: 'knowledge_points',
                            items: suggestionGroup.knowledge_points
                        });
                    }
                });

                return categories;
            } else {
                // 简单数组，归类为通用建议
                return [{
                    type: 'general',
                    items: this.suggestions
                }];
            }
        }
    },
    methods: {
        showPanel() {
            this.visible = true
            this.minimized = false
        },
        toggleMinimize() {
            this.minimized = !this.minimized
        },
        handleTabChange(tab) {
            // 处理标签页切换
        },
        handleRefreshDiagnosis() {
            // 刷新诊断
            this.$emit('refresh-diagnosis')
        },
        handleRefreshSuggestions() {
            // 刷新建议
            this.$emit('refresh-suggestions')
        },
        getIssueIcon(type) {
            const icons = {
                'syntax': 'ios-close-circle',
                'logic': 'ios-bug',
                'performance': 'ios-speedometer',
                'best_practice': 'ios-thumbs-up'
            }
            return icons[type] || 'ios-information-circle'
        },
        getIssueColor(type) {
            const colors = {
                'syntax': '#ed4014',
                'logic': '#ff9900',
                'performance': '#2d8cf0',
                'best_practice': '#19be6b'
            }
            return colors[type] || '#2d8cf0'
        },
        getIssueTypeName(type) {
            const names = {
                'syntax': this.$t('m.Syntax_Errors'),
                'logic': this.$t('m.Logic_Errors'),
                'performance': this.$t('m.Performance_Issues'),
                'best_practice': this.$t('m.Best_Practices')
            }
            return names[type] || type
        },
        // 新增方法：获取建议分类的图标
        getCategoryIcon(type) {
            const icons = {
                'completions': 'ios-code',
                'suggestions': 'ios-bulb',
                'issues': 'ios-warning',
                'knowledge_points': 'ios-book',
                'general': 'ios-information-circle'
            }
            return icons[type] || 'ios-information-circle'
        },
        // 新增方法：获取建议分类的颜色
        getCategoryColor(type) {
            const colors = {
                'completions': '#2d8cf0',
                'suggestions': '#ff9900',
                'issues': '#ed4014',
                'knowledge_points': '#19be6b',
                'general': '#515a6e'
            }
            return colors[type] || '#515a6e'
        },
        // 新增方法：获取建议分类的名称
        getCategoryName(type) {
            const names = {
                'completions': this.$t('m.Code_Completions'),
                'suggestions': this.$t('m.Improvement_Suggestions'),
                'issues': this.$t('m.Potential_Issues'),
                'knowledge_points': this.$t('m.Knowledge_Points'),
                'general': this.$t('m.General_Suggestions')
            }
            return names[type] || type
        },
        // 判断是否为简单列表（用于决定渲染方式）
        isSimpleList(items) {
            // 如果所有项目都是简单字符串或只包含text属性且无description，则认为是简单列表
            return items.every(item => {
                if (typeof item === 'string') {
                    return true;
                }
                if (typeof item === 'object') {
                    return item.text && !item.description;
                }
                return false;
            });
        },
        // 拖拽功能实现
        initPanelPosition() {
            // 设置默认位置
            this.position = {
                right: '20px',
                top: '100px'
            }
        },
        startDrag(event) {
            if (this.docked) return; // 停靠状态下不能拖拽

            const panel = this.$refs.diagnosticPanel
            if (!panel) return

            this.isDragging = true
            const rect = panel.getBoundingClientRect()
            this.dragOffset.x = event.clientX - rect.left
            this.dragOffset.y = event.clientY - rect.top

            document.addEventListener('mousemove', this.onDrag)
            document.addEventListener('mouseup', this.stopDrag)

            // 防止文本选择
            event.preventDefault()
        },
        onDrag(event) {
            if (!this.isDragging || this.docked) return

            const panel = this.$refs.diagnosticPanel
            if (!panel) return

            const x = event.clientX - this.dragOffset.x
            const y = event.clientY - this.dragOffset.y

            // 限制拖拽范围
            const maxX = window.innerWidth - panel.offsetWidth
            const maxY = window.innerHeight - panel.offsetHeight

            this.position = {
                left: Math.max(0, Math.min(maxX, x)) + 'px',
                top: Math.max(0, Math.min(maxY, y)) + 'px',
                right: 'auto'
            }
        },
        stopDrag() {
            this.isDragging = false
            document.removeEventListener('mousemove', this.onDrag)
            document.removeEventListener('mouseup', this.stopDrag)
        },
        // 停靠功能
        toggleDock() {
            this.docked = !this.docked
            if (this.docked) {
                // 停靠到右侧
                this.position = {
                    right: '20px',
                    top: '100px',
                    left: 'auto'
                }
            }
        },
        // 窗口大小变化处理
        handleWindowResize() {
            // 确保面板在窗口大小变化后仍在视窗内
            const panel = this.$refs.diagnosticPanel
            if (!panel || this.docked) return

            const rect = panel.getBoundingClientRect()
            const maxX = window.innerWidth - panel.offsetWidth
            const maxY = window.innerHeight - panel.offsetHeight

            // 如果面板超出了边界，调整位置
            if (rect.left > maxX) {
                this.position.left = maxX + 'px'
                this.position.right = 'auto'
            }

            if (rect.top > maxY) {
                this.position.top = maxY + 'px'
            }
        }
    },
    beforeDestroy() {
        // 清理事件监听器
        document.removeEventListener('mousemove', this.onDrag)
        document.removeEventListener('mouseup', this.stopDrag)
        window.removeEventListener('resize', this.handleWindowResize)
    },
    watch: {
        // 当有新的诊断或建议时自动显示面板
        issueCount: {
            handler(newVal, oldVal) {
                if (newVal > 0 && oldVal === 0 && !this.visible) {
                    this.visible = true
                }
            }
        }
    }
}
</script>
<style lang="less" scoped>
.code-diagnostic {
    .diagnostic-panel {
        position: fixed;
        width: 400px;
        max-width: calc(100% - 40px);
        background: white;
        border-radius: 8px;
        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.2);
        z-index: 999;
        display: flex;
        flex-direction: column;
        overflow: hidden;
        transition: all 0.3s ease;

        &.minimized {
            height: auto;

            .diagnostic-panel-content {
                display: none;
            }
        }

        &.docked {
            // 停靠状态样式
        }

        .diagnostic-panel-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 15px;
            background: linear-gradient(to right, #4a90e2, #5e6eb6);
            color: white;
            cursor: move;
            user-select: none;
            border-radius: 8px 8px 0 0;

            i {
                margin-right: 8px;
            }

            .diagnostic-panel-actions {
                display: flex;

                button {
                    color: white;
                    min-width: 36px;
                    text-align: center;

                    &:hover {
                        background-color: rgba(255, 255, 255, 0.2);
                    }
                }
            }
        }

        .diagnostic-panel-content {
            flex: 1;
            overflow: hidden;
            background-color: #fff;

            /deep/ .ivu-tabs {
                display: flex;
                flex-direction: column;
                height: 100%;

                .ivu-tabs-bar {
                    margin-bottom: 0;
                    border-radius: 0;
                }

                .ivu-tabs-content {
                    flex: 1;
                    overflow: auto;

                    .ivu-tabs-tabpane {
                        height: 100%;
                        padding: 10px;
                    }
                }
            }

            .real-time-diagnosis,
            .real-time-suggestions {
                height: 100%;
                display: flex;
                flex-direction: column;

                .diagnosis-content,
                .suggestions-content {
                    flex: 1;
                    overflow-y: auto;
                    padding: 10px;

                    .diagnosis-group {
                        margin-bottom: 20px;
                        border: 1px solid #eee;
                        border-radius: 4px;
                        overflow: hidden;

                        .group-header {
                            display: flex;
                            align-items: center;
                            padding: 10px;
                            background-color: #f8f8f9;

                            i {
                                margin-right: 8px;
                                font-size: 16px;
                            }

                            .group-title {
                                font-weight: bold;
                                margin-right: 10px;
                                flex: 1;
                            }

                            .ivu-tag {
                                margin: 0;
                            }
                        }

                        .issue-list {
                            padding: 10px;
                            background-color: #fff;

                            .issue-item {
                                margin-bottom: 8px;
                                line-height: 1.4;
                                padding: 5px;
                                border-left: 2px solid #eee;
                                padding-left: 10px;

                                &:hover {
                                    background-color: #f8f8f9;
                                }
                            }
                        }

                        &.syntax {
                            .group-header {
                                border-left: 3px solid #ed4014;
                            }
                        }

                        &.logic {
                            .group-header {
                                border-left: 3px solid #ff9900;
                            }
                        }

                        &.performance {
                            .group-header {
                                border-left: 3px solid #2d8cf0;
                            }
                        }

                        &.best_practice {
                            .group-header {
                                border-left: 3px solid #19be6b;
                            }
                        }
                    }

                    .suggestion-category {
                        margin-bottom: 20px;
                        border: 1px solid #eee;
                        border-radius: 4px;
                        overflow: hidden;

                        .category-header {
                            display: flex;
                            align-items: center;
                            padding: 10px;
                            background-color: #f8f8f9;

                            i {
                                margin-right: 8px;
                                font-size: 16px;
                            }

                            .category-title {
                                font-weight: bold;
                                margin-right: 10px;
                                flex: 1;
                            }

                            .ivu-tag {
                                margin: 0;
                            }
                        }

                        .category-items {
                            padding: 10px;
                            background-color: #fff;

                            // 简单列表样式（用于渲染短建议）
                            .simple-list {
                                .simple-item {
                                    display: flex;
                                    align-items: flex-start;
                                    margin-bottom: 8px;
                                    padding: 6px 10px;
                                    border-radius: 4px;
                                    background-color: #f9f9f9;
                                    line-height: 1.4;

                                    &:last-child {
                                        margin-bottom: 0;
                                    }

                                    &:hover {
                                        background-color: #f0f0f0;
                                    }

                                    .check-icon {
                                        color: #19be6b;
                                        margin-right: 8px;
                                        margin-top: 2px;
                                        font-size: 14px;
                                    }
                                }
                            }

                            // 复杂建议项样式（保留原有样式）
                            .suggestion-item {
                                margin-bottom: 12px;
                                padding: 12px;
                                border-left: 3px solid #eee;
                                border-radius: 4px;
                                background-color: #fafafa;

                                &:last-child {
                                    margin-bottom: 0;
                                }

                                &:hover {
                                    background-color: #f0f0f0;
                                }

                                .suggestion-content {
                                    .suggestion-text {
                                        font-weight: 500;
                                        margin-bottom: 5px;
                                        color: #515a6e;
                                    }

                                    .suggestion-description {
                                        font-size: 13px;
                                        color: #808695;
                                        line-height: 1.4;
                                    }
                                }
                            }
                        }
                    }
                }

                .panel-footer {
                    padding: 10px 15px;
                    border-top: 1px solid #eee;
                    text-align: right;
                    background-color: #f8f8f9;
                }
            }

            .no-issues {
                text-align: center;
                padding: 30px 20px;
                color: #999;

                i {
                    margin-bottom: 10px;
                }

                p {
                    margin: 10px 0 0;
                }
            }
        }
    }

    .show-panel-button {
        position: fixed;
        right: 20px;
        top: 100px;
        z-index: 998;

        /deep/ .ivu-btn {
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
            transition: transform 0.2s ease;

            &:hover {
                transform: scale(1.1);
            }
        }

        /deep/ .ivu-badge {
            margin-left: 5px;
        }
    }
}
</style>