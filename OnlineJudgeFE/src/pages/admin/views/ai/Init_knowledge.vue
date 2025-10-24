<template>
    <div class="knowledge-point-management">
        <Panel>
            <div slot="title">知识点管理</div>
            <div class="management-actions">
                <el-button type="primary" @click="initializeKnowledgePoints" :loading="initializing">
                    {{ initializing ? '初始化中...' : '初始化知识点数据' }}
                </el-button>
                <p class="description">
                    点击此按钮将根据现有题目标签创建知识点，并建立知识点与题目的关联关系。
                </p>
            </div>

            <div v-if="initializationResult" class="result-section">
                <h3>初始化结果</h3>
                <pre>{{ JSON.stringify(initializationResult, null, 2) }}</pre>
            </div>

            <div v-if="errorMessage" class="error-section">
                <h3>错误信息</h3>
                <p class="error-message">{{ errorMessage }}</p>
                <div v-if="errorMessage.includes('login') || errorMessage.includes('登录')">
                    <p>您可能需要登录管理员账户才能执行此操作。</p>
                </div>
            </div>
        </Panel>
    </div>
</template>

<script>
import api from '@admin/api'
import Panel from '@admin/components/Panel.vue'

export default {
    name: 'KnowledgePointManagement',
    components: {
        Panel
    },
    data() {
        return {
            initializing: false,
            initializationResult: null,
            errorMessage: null
        }
    },
    methods: {
        async initializeKnowledgePoints() {
            this.initializing = true;
            this.errorMessage = null;
            try {
                const res = await api.initializeKnowledgePoints();
                this.initializationResult = res.data.data;
                this.$message.success('知识点初始化成功');
            } catch (err) {
                // 更详细地处理错误信息
                if (err.response && err.response.data && err.response.data.data) {
                    this.errorMessage = err.response.data.data;
                    this.$message.error('知识点初始化失败: ' + err.response.data.data);
                } else if (err.response && err.response.status === 401) {
                    this.errorMessage = '未授权访问，请确保您已登录管理员账户';
                    this.$message.error('知识点初始化失败: 未授权访问');
                } else if (err.response && err.response.status === 403) {
                    this.errorMessage = '权限不足，请确保您已登录管理员账户';
                    this.$message.error('知识点初始化失败: 权限不足');
                } else {
                    this.errorMessage = '未知错误，请查看控制台获取详细信息';
                    this.$message.error('知识点初始化失败: 未知错误');
                    console.error('Initialization error:', err);
                }
            } finally {
                this.initializing = false;
            }
        }
    }
}
</script>