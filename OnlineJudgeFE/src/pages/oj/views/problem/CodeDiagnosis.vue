<template>
    <div class="code-diagnosis-container">
        <Row type="flex" justify="space-around">
            <Col :span="22">
            <div v-if="loading" class="loading-container">
                <Spin size="large" fix />
                <p>{{ loadingText }}</p>
            </div>

            <div v-else>
                <!-- 诊断结果部分 -->
                <Panel shadow v-if="diagnosis" class="diagnosis-section diagnosis-panel">
                    <div slot="title" class="panel-title">
                        <Icon type="md-medical" class="title-icon" /> {{ $t('m.Code_Diagnosis') }}
                    </div>
                    <div class="diagnosis-content">
                        <div class="diagnosis-item">
                            <h3 class="diagnosis-title">
                                <Icon type="md-warning" class="item-icon" /> {{ $t('m.Error_Analysis') }}
                            </h3>
                            <p class="diagnosis-text">{{ diagnosis.error_analysis }}</p>
                        </div>

                        <div class="diagnosis-item">
                            <h3 class="diagnosis-title">
                                <Icon type="md-hammer" class="item-icon" /> {{ $t('m.Fix_Suggestions') }}
                            </h3>
                            <p class="diagnosis-text">{{ diagnosis.fix_suggestions }}</p>
                        </div>

                        <div class="diagnosis-item">
                            <h3 class="diagnosis-title">
                                <Icon type="md-code" class="item-icon" /> {{ $t('m.Example_Code') }}
                            </h3>
                            <pre class="code-example">{{ diagnosis.example_code }}</pre>
                        </div>

                        <div class="diagnosis-item">
                            <h3 class="diagnosis-title">
                                <Icon type="md-school" class="item-icon" /> {{ $t('m.Learning_Tips') }}
                            </h3>
                            <p class="diagnosis-text">{{ diagnosis.learning_tips }}</p>
                        </div>

                        <div class="diagnosis-actions">
                            <Button @click="goBackToProblem" type="primary" class="action-btn back-btn">
                                <Icon type="md-arrow-back" /> {{ $t('m.Back_to_Problem') }}
                            </Button>
                            <Button @click="goToSubmission" class="action-btn submission-btn">
                                <Icon type="md-document" /> {{ $t('m.View_Submission') }}
                            </Button>
                        </div>
                    </div>
                </Panel>

                <!-- 无诊断结果部分 -->
                <Panel shadow v-else class="no-diagnosis-section diagnosis-panel">
                    <div class="no-diagnosis-content">
                        <Icon type="md-information-circle" size="48" class="no-data-icon" />
                        <h2>{{ $t('m.Unable_to_generate_diagnosis') }}</h2>
                        <p>{{ $t('m.Failed_to_get_diagnosis') }}</p>
                        <Button @click="goBackToProblem" type="primary" class="action-btn back-btn">
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
.code-diagnosis-container {
    padding: 20px 0;
}

.loading-container {
    text-align: center;
    padding: 50px 0;
    background: linear-gradient(120deg, #f0f8ff 0%, #e6f7ff 100%);
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(24, 144, 255, 0.15);
    border: 1px solid #e8f4ff;

    p {
        margin-top: 20px;
        font-size: 16px;
        color: #515a6e;
        font-weight: 500;
    }

    /deep/ .ivu-spin-fix {
        background-color: rgba(255, 255, 255, 0.8);
    }
}

.diagnosis-panel {
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(24, 144, 255, 0.15);
    border: 1px solid #e8f4ff;
    transition: all 0.3s ease;
    margin-bottom: 20px;

    &:hover {
        box-shadow: 0 6px 16px rgba(24, 144, 255, 0.25);
        transform: translateY(-2px);
    }

    /deep/ .ivu-card-head {
        border-bottom: 1px solid #e8f4ff;
        padding: 16px 24px;
        background: linear-gradient(120deg, #f0f8ff 0%, #e6f7ff 100%);
        border-radius: 8px 8px 0 0;

        .panel-title {
            display: flex;
            align-items: center;
            font-size: 20px;
            font-weight: 600;
            color: #1890ff;

            .title-icon {
                margin-right: 10px;
                font-size: 22px;
            }
        }
    }

    /deep/ .ivu-card-body {
        padding: 25px;
    }
}

.diagnosis-section {
    .diagnosis-content {
        .diagnosis-item {
            margin-bottom: 25px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 6px;
            border: 1px solid #e8f4ff;
            transition: all 0.3s ease;

            &:hover {
                background: #f0f8ff;
                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
            }

            .diagnosis-title {
                margin: 0 0 15px 0;
                color: #1890ff;
                font-size: 18px;
                font-weight: 600;
                display: flex;
                align-items: center;

                .item-icon {
                    margin-right: 10px;
                    font-size: 20px;
                }
            }

            .diagnosis-text {
                margin: 0;
                color: #515a6e;
                line-height: 1.7;
                font-size: 15px;
            }

            .code-example {
                background-color: #fff;
                padding: 18px;
                border-radius: 6px;
                overflow-x: auto;
                font-family: 'Monaco', 'Consolas', 'Courier New', monospace;
                white-space: pre-wrap;
                border: 1px solid #e8f4ff;
                box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.05);
                font-size: 14px;
                line-height: 1.5;
                margin: 0;
            }
        }

        .diagnosis-actions {
            text-align: center;
            padding-top: 25px;
            border-top: 1px solid #e8f4ff;
            display: flex;
            justify-content: center;
            gap: 15px;
            flex-wrap: wrap;

            .action-btn {
                border-radius: 20px;
                font-weight: 500;
                transition: all 0.3s ease;
                padding: 8px 20px;
                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);

                &:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                }
            }

            .back-btn {
                background: linear-gradient(120deg, #1890ff 0%, #096dd9 100%);
                border: none;
                color: white;

                &:hover {
                    box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
                }
            }

            .submission-btn {
                border: 1px solid #1890ff;
                color: #1890ff;
                background: transparent;

                &:hover {
                    background: #1890ff;
                    color: white;
                    box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
                }
            }
        }
    }
}

.no-diagnosis-section {
    .no-diagnosis-content {
        text-align: center;
        padding: 60px 20px;

        .no-data-icon {
            color: #1890ff;
            margin-bottom: 25px;
            opacity: 0.7;
        }

        h2 {
            margin: 0 0 15px 0;
            color: #1890ff;
            font-weight: 600;
        }

        p {
            margin-bottom: 30px;
            color: #515a6e;
            font-size: 16px;
        }

        .action-btn {
            border-radius: 20px;
            font-weight: 500;
            transition: all 0.3s ease;
            padding: 8px 20px;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
            background: linear-gradient(120deg, #1890ff 0%, #096dd9 100%);
            border: none;
            color: white;

            &:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
            }
        }
    }
}

// 响应式设计
@media (max-width: 1200px) {
    .code-diagnosis-container {
        padding: 18px 0;
    }

    .diagnosis-panel {
        /deep/ .ivu-card-head {
            padding: 14px 20px;
        }

        /deep/ .ivu-card-body {
            padding: 20px;
        }

        .panel-title {
            font-size: 18px;

            .title-icon {
                font-size: 20px;
            }
        }
    }

    .diagnosis-section {
        .diagnosis-content {
            .diagnosis-item {
                margin-bottom: 20px;
                padding: 15px;

                .diagnosis-title {
                    font-size: 16px;
                    margin-bottom: 12px;

                    .item-icon {
                        font-size: 18px;
                    }
                }

                .diagnosis-text {
                    font-size: 14px;
                }

                .code-example {
                    padding: 15px;
                    font-size: 13px;
                }
            }

            .diagnosis-actions {
                padding-top: 20px;
                gap: 12px;

                .action-btn {
                    padding: 6px 16px;
                    font-size: 14px;
                }
            }
        }
    }

    .no-diagnosis-section {
        .no-diagnosis-content {
            padding: 50px 15px;

            .no-data-icon {
                font-size: 40px;
            }

            h2 {
                font-size: 20px;
            }

            p {
                font-size: 15px;
                margin-bottom: 25px;
            }

            .action-btn {
                padding: 6px 16px;
                font-size: 14px;
            }
        }
    }
}

@media (max-width: 768px) {
    .code-diagnosis-container {
        padding: 15px 0;
    }

    .diagnosis-panel {
        /deep/ .ivu-card-head {
            padding: 12px 16px;
        }

        /deep/ .ivu-card-body {
            padding: 15px;
        }

        .panel-title {
            font-size: 16px;

            .title-icon {
                font-size: 18px;
            }
        }
    }

    .diagnosis-section {
        .diagnosis-content {
            .diagnosis-item {
                margin-bottom: 15px;
                padding: 12px;

                .diagnosis-title {
                    font-size: 15px;
                    margin-bottom: 10px;

                    .item-icon {
                        font-size: 16px;
                    }
                }

                .diagnosis-text {
                    font-size: 13px;
                }

                .code-example {
                    padding: 12px;
                    font-size: 12px;
                }
            }

            .diagnosis-actions {
                padding-top: 15px;
                flex-direction: column;
                gap: 10px;

                .action-btn {
                    width: 100%;
                    padding: 8px;
                    font-size: 13px;
                }
            }
        }
    }

    .no-diagnosis-section {
        .no-diagnosis-content {
            padding: 40px 10px;

            .no-data-icon {
                font-size: 36px;
                margin-bottom: 20px;
            }

            h2 {
                font-size: 18px;
                margin-bottom: 10px;
            }

            p {
                font-size: 14px;
                margin-bottom: 20px;
            }

            .action-btn {
                padding: 8px;
                font-size: 13px;
            }
        }
    }
}

@media (max-width: 576px) {
    .code-diagnosis-container {
        padding: 10px 0;
    }

    .diagnosis-panel {
        /deep/ .ivu-card-head {
            padding: 10px 12px;
        }

        /deep/ .ivu-card-body {
            padding: 12px;
        }

        .panel-title {
            font-size: 15px;

            .title-icon {
                font-size: 16px;
                margin-right: 8px;
            }
        }
    }

    .diagnosis-section {
        .diagnosis-content {
            .diagnosis-item {
                margin-bottom: 12px;
                padding: 10px;

                .diagnosis-title {
                    font-size: 14px;
                    margin-bottom: 8px;

                    .item-icon {
                        font-size: 14px;
                        margin-right: 6px;
                    }
                }

                .diagnosis-text {
                    font-size: 12px;
                }

                .code-example {
                    padding: 10px;
                    font-size: 11px;
                }
            }

            .diagnosis-actions {
                padding-top: 12px;
                gap: 8px;

                .action-btn {
                    padding: 6px;
                    font-size: 12px;
                }
            }
        }
    }

    .no-diagnosis-section {
        .no-diagnosis-content {
            padding: 30px 8px;

            .no-data-icon {
                font-size: 32px;
                margin-bottom: 15px;
            }

            h2 {
                font-size: 16px;
                margin-bottom: 8px;
            }

            p {
                font-size: 13px;
                margin-bottom: 15px;
            }

            .action-btn {
                padding: 6px;
                font-size: 12px;
            }
        }
    }
}
</style>