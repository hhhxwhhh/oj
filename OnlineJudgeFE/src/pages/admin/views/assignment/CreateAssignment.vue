<template>
    <div class="create-assignment">
        <div class="page-header">
            <el-page-header @back="goBack" :content="isEdit ? $t('m.Edit_Assignment') : $t('m.Create_Assignment')">
            </el-page-header>
        </div>

        <el-card class="form-card" shadow="hover">
            <div slot="header" class="card-header">
                <span class="card-title">{{ isEdit ? $t('m.Edit_Assignment') : $t('m.Create_Assignment') }}</span>
            </div>

            <el-form :model="assignmentForm" :rules="rules" ref="assignmentForm" label-width="120px"
                class="assignment-form">

                <el-row :gutter="20">
                    <el-col :span="24">
                        <el-form-item :label="$t('m.Title')" prop="title">
                            <el-input v-model="assignmentForm.title" :placeholder="$t('m.Title_Placeholder')"
                                prefix-icon="el-icon-edit-outline" clearable>
                            </el-input>
                        </el-form-item>
                    </el-col>
                </el-row>

                <el-row :gutter="20">
                    <el-col :span="24">
                        <el-form-item :label="$t('m.Description')" prop="description">
                            <el-input v-model="assignmentForm.description" type="textarea" :rows="4"
                                :placeholder="$t('m.Description_Placeholder')" resize="vertical">
                            </el-input>
                        </el-form-item>
                    </el-col>
                </el-row>

                <el-row :gutter="20">
                    <el-col :span="12">
                        <el-form-item :label="$t('m.Rule_Type')" prop="rule_type">
                            <el-select v-model="assignmentForm.rule_type" :placeholder="$t('m.Rule_Type_Placeholder')"
                                style="width: 100%;">
                                <el-option label="ACM" value="ACM">
                                    <span class="rule-option">
                                        <el-tag type="primary" size="small">ACM</el-tag>
                                        <span class="rule-desc">以通过题目数量计分</span>
                                    </span>
                                </el-option>
                                <el-option label="OI" value="OI">
                                    <span class="rule-option">
                                        <el-tag type="success" size="small">OI</el-tag>
                                        <span class="rule-desc">以题目得分总和计分</span>
                                    </span>
                                </el-option>
                            </el-select>
                        </el-form-item>
                    </el-col>

                    <el-col :span="12">
                        <el-form-item :label="$t('m.Is_Personalized')" prop="is_personalized">
                            <el-switch v-model="assignmentForm.is_personalized" active-color="#13ce66"
                                inactive-color="#ff4949" active-text="开启" inactive-text="关闭">
                            </el-switch>
                            <el-tooltip class="item" effect="dark" :content="$t('m.Personalized_Tip')" placement="top">
                                <i class="el-icon-info tooltip-icon"></i>
                            </el-tooltip>
                        </el-form-item>
                    </el-col>
                </el-row>

                <el-row :gutter="20">
                    <el-col :span="12">
                        <el-form-item :label="$t('m.Start_Time')" prop="start_time">
                            <el-date-picker v-model="assignmentForm.start_time" type="datetime"
                                :placeholder="$t('m.Start_Time_Placeholder')" value-format="yyyy-MM-dd HH:mm:ss"
                                format="yyyy-MM-dd HH:mm:ss" style="width: 100%;">
                            </el-date-picker>
                        </el-form-item>
                    </el-col>

                    <el-col :span="12">
                        <el-form-item :label="$t('m.End_Time')" prop="end_time">
                            <el-date-picker v-model="assignmentForm.end_time" type="datetime"
                                :placeholder="$t('m.End_Time_Placeholder')" value-format="yyyy-MM-dd HH:mm:ss"
                                format="yyyy-MM-dd HH:mm:ss" style="width: 100%;">
                            </el-date-picker>
                        </el-form-item>
                    </el-col>
                </el-row>

                <el-row :gutter="20">
                    <el-col :span="24">
                        <div class="form-actions">
                            <el-button type="primary" @click="submitForm('assignmentForm')" :loading="loading"
                                icon="el-icon-check">
                                {{ isEdit ? $t('m.Update') : $t('m.Create') }}
                            </el-button>
                            <el-button @click="resetForm('assignmentForm')" icon="el-icon-refresh">
                                {{ $t('m.Reset') }}
                            </el-button>
                            <el-button @click="goBack" icon="el-icon-arrow-left">
                                {{ $t('m.Back') }}
                            </el-button>
                        </div>
                    </el-col>
                </el-row>
            </el-form>
        </el-card>

        <el-card class="info-card" shadow="hover">
            <div slot="header" class="card-header">
                <span class="card-title">作业说明</span>
            </div>
            <div class="info-content">
                <ul>
                    <li><strong>ACM模式：</strong>按照通过的题目数量进行排名，所有题目分值相等</li>
                    <li><strong>OI模式：</strong>每道题目有具体分数，按照总得分进行排名</li>
                    <li><strong>个性化作业：</strong>开启后可为不同学生分配不同的题目</li>
                    <li><strong>时间设置：</strong>请确保结束时间晚于开始时间</li>
                </ul>
            </div>
        </el-card>
    </div>
</template>

<script>
import api from '../../api.js'

export default {
    name: 'CreateAssignment',
    data() {
        return {
            isEdit: false,
            assignmentId: '',
            loading: false,
            assignmentForm: {
                title: '',
                description: '',
                rule_type: 'ACM',
                is_personalized: false,
                start_time: '',
                end_time: ''
            },
            rules: {
                title: [
                    { required: true, message: this.$t('m.TitleIsRequired'), trigger: 'blur' }
                ],
                start_time: [
                    { required: true, message: this.$t('m.StartTimeIsRequired'), trigger: 'change' }
                ],
                end_time: [
                    { required: true, message: this.$t('m.EndTimeIsRequired'), trigger: 'change' }
                ]
            }
        }
    },
    created() {
        if (this.$route.name === 'edit-assignment') {
            this.isEdit = true
            this.assignmentId = this.$route.params.assignmentId
            this.getAssignmentDetail()
        }
    },
    methods: {
        getAssignmentDetail() {
            this.loading = true
            api.getAssignment(this.assignmentId).then(res => {
                this.loading = false
                const data = res.data.data
                this.assignmentForm = {
                    title: data.title,
                    description: data.description,
                    rule_type: data.rule_type,
                    is_personalized: data.is_personalized,
                    start_time: data.start_time,
                    end_time: data.end_time
                }
            }).catch(err => {
                this.loading = false
                this.handleError(err, '获取作业详情失败')
            })
        },

        submitForm(formName) {
            this.$refs[formName].validate((valid) => {
                if (valid) {
                    this.loading = true

                    // 根据是否为编辑模式选择不同的API方法
                    const apiMethod = this.isEdit ?
                        () => api.updateAssignment(this.assignmentId, this.assignmentForm) :
                        () => api.createAssignment(this.assignmentForm)

                    // 调用API
                    apiMethod().then(res => {
                        // 成功处理
                        this.loading = false
                        this.$message({
                            type: 'success',
                            message: this.isEdit ? this.$t('m.Update_Successfully') : this.$t('m.Create_Successfully')
                        })
                        this.goBack()
                    }).catch(err => {
                        this.loading = false
                        // 错误处理
                        const operation = this.isEdit ? '更新作业' : '创建作业'
                        this.handleError(err, operation)
                    })
                } else {
                    this.$message.error('请检查表单中的错误字段')
                    return false
                }
            })
        },

        handleError(err, operation) {
            console.error(`${operation}失败:`, err)

            let errorMsg = '未知错误'

            if (err && err.response) {
                const response = err.response
                if (response.data) {
                    // 优先使用具体的错误信息
                    if (response.data.data) {
                        errorMsg = typeof response.data.data === 'string' ?
                            response.data.data :
                            JSON.stringify(response.data.data)
                    } else if (response.data.error) {
                        errorMsg = response.data.error
                    } else if (response.data.detail) {
                        errorMsg = response.data.detail
                    } else if (response.data.message) {
                        errorMsg = response.data.message
                    } else {
                        errorMsg = response.statusText || '服务器错误'
                    }
                } else {
                    errorMsg = response.statusText || '服务器错误'
                }
            } else if (err && err.message) {
                errorMsg = err.message
            }

            this.$message.error(`${operation}失败: ${errorMsg}`)
        },

        resetForm(formName) {
            this.$refs[formName].resetFields()
        },

        goBack() {
            this.$router.push({ name: 'assignment-list' })
        }
    }
}
</script>

<style scoped>
.create-assignment {
    margin: 20px;
}

.page-header {
    margin-bottom: 20px;
}

.form-card,
.info-card {
    margin-bottom: 20px;
    border-radius: 8px;
}

.card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.card-title {
    font-weight: bold;
    font-size: 16px;
    color: #303133;
}

.assignment-form {
    padding: 20px 0;
}

.rule-option {
    display: flex;
    align-items: center;
}

.rule-desc {
    margin-left: 10px;
    color: #606266;
}

.tooltip-icon {
    margin-left: 10px;
    color: #909399;
    cursor: pointer;
}

.form-actions {
    display: flex;
    justify-content: center;
    padding: 20px 0;
}

.form-actions .el-button {
    margin: 0 10px;
}

.info-content ul {
    padding-left: 20px;
}

.info-content li {
    margin-bottom: 10px;
    line-height: 1.6;
    color: #606266;
}

.el-page-header__content {
    font-weight: bold;
    font-size: 18px;
}
</style>