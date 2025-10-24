<template>
    <div class="problem">
        <el-row :gutter="20">
            <!-- 左侧配置面板 -->
            <el-col :span="12">
                <Panel class="config-panel">
                    <div slot="title">{{ $t('m.AI_Generate_Problem') }}</div>
                    <div class="config-content">
                        <el-form ref="form" :model="form" label-position="top" label-width="120px">
                            <el-form-item :label="$t('m.Knowledge_Point')" required>
                                <el-input v-model="form.knowledgePoint"
                                    :placeholder="$t('m.Knowledge_Point_Placeholder')" required>
                                </el-input>
                            </el-form-item>

                            <el-form-item :label="$t('m.Difficulty')">
                                <el-select class="difficulty-select" size="small" :placeholder="$t('m.Difficulty')"
                                    v-model="form.difficulty" style="width: 100%;">
                                    <el-option :label="$t('m.Low')" value="Low"></el-option>
                                    <el-option :label="$t('m.Mid')" value="Mid"></el-option>
                                    <el-option :label="$t('m.High')" value="High"></el-option>
                                </el-select>
                            </el-form-item>

                            <el-row :gutter="15">
                                <el-col :span="12">
                                    <el-checkbox v-model="form.autoAdjust">{{ $t('m.Auto_Adjust_Difficulty')
                                    }}</el-checkbox>
                                </el-col>
                                <el-col :span="12">
                                    <el-checkbox v-model="form.generateTestCases">{{ $t('m.Auto_Generate_Test_Cases')
                                    }}</el-checkbox>
                                </el-col>
                            </el-row>

                            <el-form-item v-if="form.generateTestCases" :label="$t('m.Test_Case_Count')">
                                <el-input-number v-model="form.testCaseCount" :min="1" :max="20" size="small">
                                </el-input-number>
                            </el-form-item>

                            <el-form-item>
                                <el-button type="primary" :loading="generating" @click="generateProblem"
                                    icon="el-icon-magic-stick" style="width: 100%;">
                                    {{ generating ? $t('m.Generating') : $t('m.Generate_Problem') }}
                                </el-button>
                            </el-form-item>
                        </el-form>
                    </div>
                </Panel>
            </el-col>

            <!-- 右侧结果面板 -->
            <el-col :span="12">
                <div v-if="generatedProblem" class="result-container">
                    <Panel class="result-panel">
                        <div slot="title">{{ $t('m.Generated_Problem') }}</div>

                        <el-alert v-if="error" :title="error" type="error" show-icon :closable="false" class="alert">
                        </el-alert>

                        <el-alert v-if="successMessage" :title="successMessage" type="success" show-icon
                            :closable="false" class="alert">
                        </el-alert>

                        <div v-if="!error" class="result-content">
                            <el-scrollbar style="height: 100%;">
                                <div class="scroll-content">
                                    <el-form ref="problemForm" :model="generatedProblem" label-position="top"
                                        label-width="120px">
                                        <el-form-item :label="$t('m.Title')" required>
                                            <el-input v-model="generatedProblem.title"></el-input>
                                        </el-form-item>

                                        <el-form-item :label="$t('m.Description')" required>
                                            <MarkdownEditor v-model="generatedProblem.description" :height="200">
                                            </MarkdownEditor>
                                        </el-form-item>

                                        <el-form-item :label="$t('m.Input_Description')" required>
                                            <MarkdownEditor v-model="generatedProblem.input_description" :height="150">
                                            </MarkdownEditor>
                                        </el-form-item>

                                        <el-form-item :label="$t('m.Output_Description')" required>
                                            <MarkdownEditor v-model="generatedProblem.output_description" :height="150">
                                            </MarkdownEditor>
                                        </el-form-item>

                                        <el-row :gutter="15">
                                            <el-col :span="8">
                                                <el-form-item :label="$t('m.Time_Limit') + ' (ms)'" required>
                                                    <el-input-number v-model="generatedProblem.time_limit" :min="100"
                                                        :step="100" style="width: 100%;"></el-input-number>
                                                </el-form-item>
                                            </el-col>
                                            <el-col :span="8">
                                                <el-form-item :label="$t('m.Memory_limit') + ' (MB)'" required>
                                                    <el-input-number v-model="generatedProblem.memory_limit" :min="4"
                                                        :step="4" style="width: 100%;"></el-input-number>
                                                </el-form-item>
                                            </el-col>
                                            <el-col :span="8">
                                                <el-form-item :label="$t('m.Difficulty')">
                                                    <el-select class="difficulty-select" size="small"
                                                        v-model="generatedProblem.difficulty" style="width: 100%;">
                                                        <el-option :label="$t('m.Low')" value="Low"></el-option>
                                                        <el-option :label="$t('m.Mid')" value="Mid"></el-option>
                                                        <el-option :label="$t('m.High')" value="High"></el-option>
                                                    </el-select>
                                                </el-form-item>
                                            </el-col>
                                        </el-row>

                                        <div class="samples-section">
                                            <h4>{{ $t('m.Samples') }}</h4>
                                            <el-form-item v-for="(sample, index) in generatedProblem.samples"
                                                :key="'sample' + index">
                                                <Accordion :title="$t('m.Sample') + (index + 1)">
                                                    <el-button type="warning" size="small" icon="el-icon-delete"
                                                        slot="header" @click="removeSample(index)">
                                                        {{ $t('m.Delete') }}
                                                    </el-button>
                                                    <el-row :gutter="15">
                                                        <el-col :span="12">
                                                            <el-form-item :label="$t('m.Input_Samples')" required>
                                                                <el-input :rows="4" type="textarea"
                                                                    :placeholder="$t('m.Input_Samples')"
                                                                    v-model="sample.input">
                                                                </el-input>
                                                            </el-form-item>
                                                        </el-col>
                                                        <el-col :span="12">
                                                            <el-form-item :label="$t('m.Output_Samples')" required>
                                                                <el-input :rows="4" type="textarea"
                                                                    :placeholder="$t('m.Output_Samples')"
                                                                    v-model="sample.output">
                                                                </el-input>
                                                            </el-form-item>
                                                        </el-col>
                                                    </el-row>
                                                </Accordion>
                                            </el-form-item>
                                        </div>

                                        <div class="add-sample-btn">
                                            <el-button type="primary" icon="el-icon-plus" @click="addSample()"
                                                size="small">
                                                {{ $t('m.Add_Sample') }}
                                            </el-button>
                                        </div>

                                        <el-form-item :label="$t('m.Hint')">
                                            <MarkdownEditor v-model="generatedProblem.hint" :height="150">
                                            </MarkdownEditor>
                                        </el-form-item>

                                        <div class="button-group">
                                            <el-button type="success" @click="saveProblem" icon="el-icon-check"
                                                :loading="saving">
                                                {{ saving ? $t('m.Saving') : $t('m.Save_Problem') }}
                                            </el-button>
                                            <el-button @click="resetForm" icon="el-icon-refresh">
                                                {{ $t('m.Reset') }}
                                            </el-button>
                                        </div>
                                    </el-form>
                                </div>
                            </el-scrollbar>
                        </div>
                    </Panel>
                </div>

                <!-- 空状态占位 -->
                <div v-else class="empty-placeholder">
                    <Panel>
                        <div slot="title">{{ $t('m.Generated_Problem') }}</div>
                        <div class="placeholder-content">
                            <i class="el-icon-document"></i>
                            <p>{{ $t('m.Generate_Problem_Placeholder') }}</p>
                        </div>
                    </Panel>
                </div>
            </el-col>
        </el-row>
    </div>
</template>

<script>
import api from '@admin/api'
import Panel from '@admin/components/Panel.vue'
import Accordion from '@admin/components/Accordion.vue'
import MarkdownEditor from '@admin/components/MarkdownEditor.vue'

export default {
    name: 'AIGenerateProblem',
    components: {
        Panel,
        Accordion,
        MarkdownEditor
    },
    data() {
        return {
            form: {
                knowledgePoint: '',
                difficulty: 'Mid',
                autoAdjust: true,
                generateTestCases: true,
                testCaseCount: 5
            },
            generating: false,
            generatedProblem: null,
            error: '',
            successMessage: '',
            saving: false
        }
    },
    methods: {
        async generateProblem() {
            // 更严格的验证逻辑
            if (!this.form.knowledgePoint ||
                typeof this.form.knowledgePoint !== 'string' ||
                this.form.knowledgePoint.trim().length === 0) {
                this.error = this.$t('m.Knowledge_Point_Required')
                console.log('Debug - Validation failed: knowledge point is required');
                return
            }

            console.log('Debug - Validation passed, proceeding with generation');

            this.generating = true
            this.error = ''
            this.successMessage = ''

            try {
                const requestData = {
                    knowledge_point: this.form.knowledgePoint.trim(),
                    difficulty: this.form.difficulty,
                    auto_adjust: this.form.autoAdjust,
                    generate_test_cases: this.form.generateTestCases,
                    test_case_count: this.form.testCaseCount
                };

                console.log('Debug - Request data:', requestData);

                const res = await api.generateAIProblem(requestData)
                console.log('Debug - API response:', res);

                // 检查响应中是否有错误
                if (res.data && res.data.error !== null) {
                    // 后端返回了错误
                    this.error = res.data.data || this.$t('m.Failed_to_Generate_Problem');
                    // 特殊处理AI模型未配置的情况
                    if (this.error.includes("没有激活的AI模型")) {
                        this.error += "，请在AI模型管理中配置并激活一个AI模型后再试";
                    }
                } else {
                    // 成功响应
                    this.generatedProblem = res.data.data
                    this.successMessage = this.$t('m.Problem_Generated_Successfully')
                }
            } catch (err) {
                console.error('Debug - Error generating problem:', err);
                // 网络错误或其他异常
                if (err.response) {
                    // 服务器返回了错误状态码
                    console.log('Debug - Error response:', err.response);
                    if (err.response.data) {
                        console.log('Debug - Error response data:', err.response.data);
                        if (err.response.data.data) {
                            this.error = err.response.data.data;
                        } else if (err.response.data.error) {
                            this.error = err.response.data.error;
                        } else {
                            this.error = `${err.response.status}: ${err.response.statusText}`;
                        }
                    } else {
                        this.error = `${err.response.status}: ${err.response.statusText}`;
                    }
                } else if (err.request) {
                    // 请求已发出但没有收到响应
                    this.error = "网络错误或服务器无响应";
                } else {
                    // 其他错误
                    this.error = err.message || this.$t('m.Failed_to_Generate_Problem');
                }
            } finally {
                this.generating = false
            }
        },

        addSample() {
            if (!this.generatedProblem.samples) {
                this.$set(this.generatedProblem, 'samples', [])
            }
            this.generatedProblem.samples.push({
                input: '',
                output: ''
            })
        },

        removeSample(index) {
            this.generatedProblem.samples.splice(index, 1)
        },

        async saveProblem() {
            this.saving = true;
            this.successMessage = '';
            this.error = '';

            try {
                // 生成一个随机的题目ID
                const randomId = 'AI-' + Math.random().toString(36).substr(2, 8).toUpperCase();

                // 准备题目数据
                const problemData = {
                    _id: randomId,
                    title: this.generatedProblem.title,
                    description: this.generatedProblem.description,
                    input_description: this.generatedProblem.input_description,
                    output_description: this.generatedProblem.output_description,
                    time_limit: this.generatedProblem.time_limit,
                    memory_limit: this.generatedProblem.memory_limit,
                    difficulty: this.generatedProblem.difficulty,
                    visible: true,
                    share_submission: false,
                    tags: [this.form.knowledgePoint],
                    languages: [], // 默认为空，后续可以让用户选择
                    samples: this.generatedProblem.samples,
                    hint: this.generatedProblem.hint,
                    rule_type: "ACM",
                    io_mode: { "io_mode": "Standard IO", "input": "input.txt", "output": "output.txt" },
                    source: `AI Generated - ${this.form.knowledgePoint}`,
                    spj: false,
                    spj_language: null,
                    spj_code: null,
                    testcase: "",
                    test_case_id: "test-case" + randomId.toLowerCase(),
                    test_case_score: [],
                    template: {}
                };

                // 调用API创建题目
                const res = await api.createProblem(problemData);

                if (res.status === 200 || res.status === 201) {
                    this.successMessage = this.$t('m.Problem_Saved_Successfully');
                } else {
                    this.error = this.$t('m.Failed_to_Save_Problem');
                }
            } catch (err) {
                // 更详细地处理错误信息
                if (err.response) {
                    // 服务器返回了错误状态码
                    if (err.response.data) {
                        if (err.response.data.data) {
                            this.error = err.response.data.data;
                        } else {
                            this.error = `${err.response.status}: ${err.response.statusText}`;
                        }
                    } else {
                        this.error = `${err.response.status}: ${err.response.statusText}`;
                    }
                } else if (err.request) {
                    // 请求已发出但没有收到响应
                    this.error = "网络错误或服务器无响应";
                } else {
                    // 其他错误
                    this.error = err.message || this.$t('m.Failed_to_Save_Problem');
                }
            } finally {
                this.saving = false;
            }
        },

        resetForm() {
            // 重置表单数据
            this.form = {
                knowledgePoint: '',
                difficulty: 'Mid',
                autoAdjust: true,
                generateTestCases: true,
                testCaseCount: 5
            };
            this.generatedProblem = null;
            this.error = '';
            this.successMessage = '';
            this.saving = false;
        }
    }
}
</script>

<style scoped lang="less">
.problem {
    height: 100%;

    .config-panel,
    .result-panel,
    .info-panel {
        height: 100%;

        /deep/ .panel-body {
            height: calc(100% - 50px);
        }
    }

    .config-content {
        padding: 20px;
    }

    .info-content {
        padding: 20px;

        p {
            margin-bottom: 10px;
            color: #606266;

            i {
                color: #409eff;
                margin-right: 5px;
            }
        }
    }

    .result-container {
        height: 100%;

        /deep/ .panel-body {
            height: calc(100% - 50px);
            padding: 0;
        }

        .result-content {
            height: 100%;
            padding: 20px;

            .el-scrollbar {
                height: calc(100% - 50px);

                .scroll-content {
                    padding-right: 15px;
                }
            }
        }
    }

    .alert {
        margin-bottom: 20px;
    }

    .samples-section {
        margin: 20px 0;

        h4 {
            margin-bottom: 15px;
            color: #606266;
            font-weight: bold;
        }

        /deep/ .accordion {
            margin-bottom: 15px;

            .header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px 15px;
                background-color: #f5f5f5;
                border-radius: 4px;

                .title {
                    font-weight: bold;
                }
            }

            .content {
                padding: 15px;
                border: 1px solid #ebeef5;
                border-top: none;
                border-radius: 0 0 4px 4px;
            }
        }
    }

    .add-sample-btn {
        margin: 15px 0;
    }

    .button-group {
        margin-top: 20px;
        display: flex;
        gap: 10px;
    }

    /deep/ .el-form-item {
        margin-bottom: 20px;
    }

    /deep/ .el-form-item__label {
        font-weight: bold;
        color: #606266;
    }

    .empty-placeholder {
        height: 100%;

        /deep/ .panel-body {
            display: flex;
            align-items: center;
            justify-content: center;
            height: calc(100% - 50px);
        }

        .placeholder-content {
            text-align: center;
            color: #909399;

            i {
                font-size: 48px;
                margin-bottom: 15px;
                color: #c0c4cc;
            }

            p {
                font-size: 14px;
            }
        }
    }
}
</style>