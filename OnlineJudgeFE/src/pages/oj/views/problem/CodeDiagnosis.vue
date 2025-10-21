<template>
    <div>
        <Row type="flex" justify="space-around">
            <Col :span="22">
            <div v-if="loading" class="loading-container">
                <Spin size="large" fix />
                <p>{{ loadingText }}</p>
            </div>

            <div v-else>
                <!-- 诊断结果部分 -->
                <Panel shadow v-if="diagnosis" class="diagnosis-section">
                    <div slot="title">
                        <Icon type="md-medical" /> {{ $t('m.Code_Diagnosis') }}
                    </div>
                    <div class="diagnosis-content">
                        <div class="diagnosis-item">
                            <h3>
                                <Icon type="md-warning" /> {{ $t('m.Error_Analysis') }}
                            </h3>
                            <p>{{ diagnosis.error_analysis }}</p>
                        </div>

                        <div class="diagnosis-item">
                            <h3>
                                <Icon type="md-hammer" /> {{ $t('m.Fix_Suggestions') }}
                            </h3>
                            <p>{{ diagnosis.fix_suggestions }}</p>
                        </div>

                        <div class="diagnosis-item">
                            <h3>
                                <Icon type="md-code" /> {{ $t('m.Example_Code') }}
                            </h3>
                            <pre class="code-example">{{ diagnosis.example_code }}</pre>
                        </div>

                        <div class="diagnosis-item">
                            <h3>
                                <Icon type="md-school" /> {{ $t('m.Learning_Tips') }}
                            </h3>
                            <p>{{ diagnosis.learning_tips }}</p>
                        </div>

                        <div class="diagnosis-actions">
                            <Button @click="goBackToProblem" type="primary">
                                <Icon type="md-arrow-back" /> {{ $t('m.Back_to_Problem') }}
                            </Button>
                            <Button @click="goToSubmission" style="margin-left: 10px;">
                                <Icon type="md-document" /> {{ $t('m.View_Submission') }}
                            </Button>
                        </div>
                    </div>
                </Panel>

                <!-- 无诊断结果部分 -->
                <Panel shadow v-else class="no-diagnosis-section">
                    <div class="no-diagnosis-content">
                        <Icon type="md-information-circle" size="40" />
                        <h2>{{ $t('m.Unable_to_generate_diagnosis') }}</h2>
                        <p>{{ $t('m.Failed_to_get_diagnosis') }}</p>
                        <Button @click="goBackToProblem" type="primary">
                            <Icon type="md-arrow-back" /> {{ $t('m.Back_to_Problem') }}
                        </Button>
                    </div>
                </Panel>
            </div>
            </Col>
        </Row>
    </div>
</template>

<script>
import api from '@oj/api'
import { mapGetters, mapActions } from 'vuex'
import Panel from '@oj/components/Panel.vue'

export default {
    name: 'CodeDiagnosis',
    components: {
        Panel
    },
    data() {
        return {
            loading: false,
            loadingText: '',
            diagnosis: null,
            submissionId: null,
            problemId: null
        }
    },
    computed: {
        ...mapGetters(['user'])
    },
    mounted() {
        this.submissionId = this.$route.query.submissionId
        this.problemId = this.$route.query.problemId

        if (this.submissionId) {
            this.generateDiagnosis()
        } else {
            this.$error(this.$t('m.Missing_Submission_Data'))
        }
    },
    methods: {
        ...mapActions(['changeDomTitle']),
        async generateDiagnosis() {
            if (!this.submissionId) return

            this.loading = true
            this.loadingText = this.$t('m.Generating_Diagnosis')

            try {
                const res = await api.getCodeDiagnosis(this.submissionId)
                if (res && res.data && res.data.error === null && res.data.data) {
                    this.diagnosis = res.data.data
                    this.changeDomTitle({ title: this.$t('m.Code_Diagnosis') })
                } else {
                    let errorMessage = this.$t('m.Failed_to_diagnose_code')
                    if (res && res.data) {
                        if (res.data.data) {
                            errorMessage = res.data.data
                        } else if (res.data.error) {
                            errorMessage = res.data.error
                        }
                    }
                    this.$error(errorMessage)
                    this.diagnosis = null
                }
            } catch (err) {
                // 更详细地处理错误信息
                let errorMessage = this.$t('m.Failed_to_diagnose_code')
                if (err && err.response && err.response.data) {
                    if (err.response.data.data) {
                        errorMessage = err.response.data.data
                    } else if (err.response.data.error) {
                        errorMessage = err.response.data.error
                    } else if (typeof err.response.data === 'string') {
                        errorMessage = err.response.data
                    } else {
                        errorMessage = JSON.stringify(err.response.data)
                    }
                } else if (err && err.message) {
                    errorMessage = err.message
                } else if (typeof err === 'object') {
                    errorMessage = JSON.stringify(err)
                } else if (typeof err === 'string') {
                    errorMessage = err
                }
                this.$error(errorMessage)
                console.error('Failed to get code diagnosis:', err)
                this.diagnosis = null
            } finally {
                this.loading = false
                this.loadingText = ''
            }
        },
        goBackToProblem() {
            if (this.problemId) {
                this.$router.push({
                    name: 'problem-details',
                    params: { problemID: this.problemId }
                })
            } else {
                this.$router.go(-1)
            }
        },

        goToSubmission() {
            if (this.submissionId) {
                this.$router.push({
                    name: 'submission-details',
                    params: { id: this.submissionId }
                })
            }
        },

        getDifficultyColor(difficulty) {
            switch (difficulty) {
                case 'Low': return 'success'
                case 'Mid': return 'warning'
                case 'High': return 'error'
                default: return 'default'
            }
        }
    }
}
</script>

<style lang="less" scoped>
.loading-container {
    text-align: center;
    padding: 50px 0;

    p {
        margin-top: 20px;
        font-size: 16px;
    }
}

.diagnosis-section {
    .diagnosis-content {
        .diagnosis-item {
            margin-bottom: 20px;

            h3 {
                margin-bottom: 10px;
                color: #2d8cf0;
            }

            .code-example {
                background-color: #f8f8f9;
                padding: 15px;
                border-radius: 4px;
                overflow-x: auto;
                font-family: monospace;
                white-space: pre-wrap;
            }
        }

        .diagnosis-actions {
            text-align: center;
            padding-top: 20px;
            border-top: 1px solid #e8eaec;
        }
    }
}

.no-diagnosis-section {
    .no-diagnosis-content {
        text-align: center;
        padding: 50px 0;

        h2 {
            margin: 20px 0 10px 0;
        }

        p {
            margin-bottom: 20px;
            color: #808695;
        }
    }
}
</style>