<template>
    <div class="problem">
        <Panel>
            <span slot="title">{{ $t('m.AI_Generate_Problem') }}</span>
            <el-form ref="form" :model="form" label-position="top" label-width="120px">
                <el-row :gutter="20">
                    <el-col :span="18">
                        <el-form-item :label="$t('m.Knowledge_Point')" required>
                            <el-input v-model="form.knowledgePoint" :placeholder="$t('m.Knowledge_Point_Placeholder')"
                                required>
                            </el-input>
                        </el-form-item>
                    </el-col>
                </el-row>

                <el-row :gutter="20">
                    <el-col :span="18">
                        <el-form-item :label="$t('m.Difficulty')">
                            <el-select class="difficulty-select" size="small" :placeholder="$t('m.Difficulty')"
                                v-model="form.difficulty">
                                <el-option :label="$t('m.Low')" value="Low"></el-option>
                                <el-option :label="$t('m.Mid')" value="Mid"></el-option>
                                <el-option :label="$t('m.High')" value="High"></el-option>
                            </el-select>
                        </el-form-item>
                    </el-col>
                </el-row>

                <el-row :gutter="20">
                    <el-col :span="18">
                        <el-checkbox v-model="form.autoAdjust">{{ $t('m.Auto_Adjust_Difficulty') }}</el-checkbox>
                    </el-col>
                </el-row>

                <el-row :gutter="20">
                    <el-col :span="18">
                        <el-checkbox v-model="form.generateTestCases">{{ $t('m.Auto_Generate_Test_Cases')
                            }}</el-checkbox>
                    </el-col>
                </el-row>

                <el-row :gutter="20" v-if="form.generateTestCases">
                    <el-col :span="18">
                        <el-form-item :label="$t('m.Test_Case_Count')">
                            <el-input-number v-model="form.testCaseCount" :min="1" :max="20" size="small">
                            </el-input-number>
                        </el-form-item>
                    </el-col>
                </el-row>

                <el-row :gutter="20">
                    <el-col :span="18">
                        <el-button type="primary" :loading="generating" @click="generateProblem"
                            icon="el-icon-magic-stick">
                            {{ generating ? $t('m.Generating') : $t('m.Generate_Problem') }}
                        </el-button>
                    </el-col>
                </el-row>
            </el-form>
        </Panel>

        <div v-if="generatedProblem">
            <Panel>
                <span slot="title">{{ $t('m.Generated_Problem') }}</span>
                <el-alert v-if="error" :title="error" type="error" show-icon :closable="false">
                </el-alert>

                <el-alert v-if="successMessage" :title="successMessage" type="success" show-icon :closable="false">
                </el-alert>

                <div v-if="!error">
                    <el-form ref="problemForm" :model="generatedProblem" label-position="top" label-width="120px">
                        <el-row :gutter="20">
                            <el-col :span="18">
                                <el-form-item :label="$t('m.Title')" required>
                                    <el-input v-model="generatedProblem.title"></el-input>
                                </el-form-item>
                            </el-col>
                        </el-row>

                        <el-row :gutter="20">
                            <el-col :span="24">
                                <el-form-item :label="$t('m.Description')" required>
                                    <MarkdownEditor v-model="generatedProblem.description"></MarkdownEditor>
                                </el-form-item>
                            </el-col>
                        </el-row>

                        <el-row :gutter="20">
                            <el-col :span="24">
                                <el-form-item :label="$t('m.Input_Description')" required>
                                    <MarkdownEditor v-model="generatedProblem.input_description"></MarkdownEditor>
                                </el-form-item>
                            </el-col>
                        </el-row>

                        <el-row :gutter="20">
                            <el-col :span="24">
                                <el-form-item :label="$t('m.Output_Description')" required>
                                    <MarkdownEditor v-model="generatedProblem.output_description"></MarkdownEditor>
                                </el-form-item>
                            </el-col>
                        </el-row>

                        <el-row :gutter="20">
                            <el-col :span="8">
                                <el-form-item :label="$t('m.Time_Limit') + ' (ms)'" required>
                                    <el-input-number v-model="generatedProblem.time_limit" :min="100"
                                        :step="100"></el-input-number>
                                </el-form-item>
                            </el-col>
                            <el-col :span="8">
                                <el-form-item :label="$t('m.Memory_limit') + ' (MB)'" required>
                                    <el-input-number v-model="generatedProblem.memory_limit" :min="4"
                                        :step="4"></el-input-number>
                                </el-form-item>
                            </el-col>
                            <el-col :span="8">
                                <el-form-item :label="$t('m.Difficulty')">
                                    <el-select class="difficulty-select" size="small"
                                        v-model="generatedProblem.difficulty">
                                        <el-option :label="$t('m.Low')" value="Low"></el-option>
                                        <el-option :label="$t('m.Mid')" value="Mid"></el-option>
                                        <el-option :label="$t('m.High')" value="High"></el-option>
                                    </el-select>
                                </el-form-item>
                            </el-col>
                        </el-row>

                        <div>
                            <el-form-item v-for="(sample, index) in generatedProblem.samples" :key="'sample' + index">
                                <Accordion :title="$t('m.Sample') + (index + 1)">
                                    <el-button type="warning" size="small" icon="el-icon-delete" slot="header"
                                        @click="removeSample(index)">
                                        {{ $t('m.Delete') }}
                                    </el-button>
                                    <el-row :gutter="20">
                                        <el-col :span="12">
                                            <el-form-item :label="$t('m.Input_Samples')" required>
                                                <el-input :rows="5" type="textarea" :placeholder="$t('m.Input_Samples')"
                                                    v-model="sample.input">
                                                </el-input>
                                            </el-form-item>
                                        </el-col>
                                        <el-col :span="12">
                                            <el-form-item :label="$t('m.Output_Samples')" required>
                                                <el-input :rows="5" type="textarea"
                                                    :placeholder="$t('m.Output_Samples')" v-model="sample.output">
                                                </el-input>
                                            </el-form-item>
                                        </el-col>
                                    </el-row>
                                </Accordion>
                            </el-form-item>
                        </div>

                        <div class="add-sample-btn">
                            <button type="button" class="add-samples" @click="addSample()">
                                <i class="el-icon-plus"></i>{{ $t('m.Add_Sample') }}
                            </button>
                        </div>

                        <el-row :gutter="20">
                            <el-col :span="24">
                                <el-form-item :label="$t('m.Hint')">
                                    <MarkdownEditor v-model="generatedProblem.hint"></MarkdownEditor>
                                </el-form-item>
                            </el-col>
                        </el-row>

                        <el-row :gutter="20">
                            <el-col :span="24">
                                <div class="button-group">
                                    <el-button type="success" @click="saveProblem" icon="el-icon-check">
                                        {{ $t('m.Save_Problem') }}
                                    </el-button>
                                    <el-button @click="resetForm" icon="el-icon-refresh">
                                        {{ $t('m.Reset') }}
                                    </el-button>
                                </div>
                            </el-col>
                        </el-row>
                    </el-form>
                </div>
            </Panel>
        </div>
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
            // 更严格的验证逻辑，确保正确检查知识点输入
            console.log('Debug - Form data:', this.form);
            console.log('Debug - Knowledge point value:', this.form.knowledgePoint);
            console.log('Debug - Knowledge point type:', typeof this.form.knowledgePoint);
            console.log('Debug - Knowledge point length:', this.form.knowledgePoint ? this.form.knowledgePoint.length : 0);
            console.log('Debug - Knowledge point truthy:', !!this.form.knowledgePoint);
            console.log('Debug - Knowledge point trimmed:', this.form.knowledgePoint.trim());
            console.log('Debug - Knowledge point trimmed length:', this.form.knowledgePoint.trim().length);

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

                this.generatedProblem = res.data.data
                this.successMessage = this.$t('m.Problem_Generated_Successfully')
            } catch (err) {
                console.error('Debug - Error generating problem:', err);
                this.error = err.message || this.$t('m.Failed_to_Generate_Problem')
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
                // 准备题目数据
                const problemData = {
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
                    testcase: ""
                };

                // 调用API创建题目
                const res = await api.createProblem(problemData);

                if (res.status === 200 || res.status === 201) {
                    this.successMessage = this.$t('m.Problem_Saved_Successfully');
                    // 可以考虑重置表单或跳转到题目列表
                    // this.resetForm();
                } else {
                    this.error = this.$t('m.Failed_to_Save_Problem');
                }
            } catch (err) {
                this.error = err.message || this.$t('m.Failed_to_Save_Problem');
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
.button-group {
    margin-top: 20px;
}

.add-sample-btn {
    margin-bottom: 10px;

    .add-samples {
        border: none;
        background-color: #fff;
        color: #495060;
        padding: 0;

        &:hover {
            color: #2d8cf0;
            background-color: #fff;
        }
    }
}
</style>