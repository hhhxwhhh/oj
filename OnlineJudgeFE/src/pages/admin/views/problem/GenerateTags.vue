<template>
    <div class="view">
        <Panel :title="$t('m.Generate_Problem_Tags')">
            <div class="content">
                <el-alert v-if="!hasActiveAIModel" :title="$t('m.No_Active_AI_Model')" type="error" show-icon
                    :description="$t('m.Please_configure_active_AI_model')" :closable="false">
                </el-alert>

                <div class="options-section">
                    <el-checkbox v-model="forceRegenerate" disabled>
                        {{ $t('m.Process_All_Problems') }}
                    </el-checkbox>
                    <p class="description">
                        {{ $t('m.Process_All_Problems_Description') }}
                    </p>
                </div>

                <div class="stats-section">
                    <el-row :gutter="20">
                        <el-col :span="12">
                            <el-card class="stat-card">
                                <div class="stat-item">
                                    <p class="stat-title">{{ $t('m.Total_Problems') }}</p>
                                    <p class="stat-value">{{ stats.total }}</p>
                                </div>
                            </el-card>
                        </el-col>
                        <el-col :span="12">
                            <el-card class="stat-card">
                                <div class="stat-item">
                                    <p class="stat-title">{{ $t('m.Active_AI_Models') }}</p>
                                    <p class="stat-value">{{ stats.activeAIModels }}</p>
                                </div>
                            </el-card>
                        </el-col>
                    </el-row>
                </div>

                <div class="actions-section">
                    <el-button type="primary" @click="generateTags" :loading="loading"
                        :disabled="!hasActiveAIModel || loading" size="medium">
                        <i class="el-icon-refresh"></i>
                        {{ $t('m.Generate_Tags_For_All') }}
                    </el-button>
                </div>

                <div v-if="taskOutput" class="output-section">
                    <el-divider content-position="left">{{ $t('m.Task_Output') }}</el-divider>
                    <pre class="output">{{ taskOutput }}</pre>
                </div>
            </div>
        </Panel>
    </div>
</template>

<script>
import api from '../../api'

export default {
    name: 'GenerateTags',
    data() {
        return {
            loading: false,
            forceRegenerate: true, // 默认处理所有题目
            stats: {
                total: 0,
                activeAIModels: 0
            },
            taskOutput: '',
            hasActiveAIModel: false
        }
    },

    mounted() {
        this.loadStats()
    },

    methods: {
        async loadStats() {
            try {
                const res = await api.getProblemTagsStats()
                this.stats = {
                    total: res.data.data.total_problems,
                    activeAIModels: res.data.data.active_ai_models
                }
                this.hasActiveAIModel = res.data.data.active_ai_models > 0
            } catch (error) {
                console.error('Failed to load stats:', error)
                this.$error('获取统计信息失败')
            }
        },

        async generateTags() {
            if (!this.hasActiveAIModel) {
                this.$error(this.$t('m.No_Active_AI_Model'))
                return
            }

            this.loading = true
            this.taskOutput = ''

            try {
                const res = await api.generateProblemTags({
                    force: this.forceRegenerate
                })

                this.$success(this.$t('m.Tags_Generation_Completed'))
                this.taskOutput = res.data.data.output
                this.loadStats() // 重新加载统计信息
            } catch (error) {
                console.error('Failed to generate tags:', error)
                this.$error(this.$t('m.Tags_Generation_Failed'))
                if (error.response && error.response.data) {
                    this.taskOutput = error.response.data.data || error.response.data.message
                }
            } finally {
                this.loading = false
            }
        }
    }
}
</script>

<style scoped lang="less">
.view {
    .content {
        padding: 20px;

        .options-section {
            margin-bottom: 30px;
            padding: 15px;
            background-color: #f8f8f9;
            border-radius: 4px;

            .description {
                margin-top: 10px;
                color: #808695;
                font-size: 12px;
            }
        }

        .stats-section {
            margin-bottom: 30px;

            .stat-card {
                border: 1px solid #ebeef5;

                .stat-item {
                    text-align: center;

                    .stat-title {
                        font-size: 14px;
                        color: #808695;
                        margin-bottom: 10px;
                    }

                    .stat-value {
                        font-size: 24px;
                        font-weight: 500;
                        color: #409eff;
                    }
                }
            }
        }

        .actions-section {
            text-align: center;
            margin-bottom: 30px;
        }

        .output-section {
            margin-top: 20px;

            .output {
                background-color: #f8f8f9;
                padding: 15px;
                border-radius: 4px;
                max-height: 300px;
                overflow-y: auto;
                white-space: pre-wrap;
                font-family: monospace;
                font-size: 12px;
                margin: 0;
            }
        }
    }
}
</style>