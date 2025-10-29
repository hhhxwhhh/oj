<template>
    <div class="create-assignment">
        <el-card class="box-card">
            <div slot="header" class="clearfix">
                <span>{{ isEdit ? $t('m.Edit_Assignment') : $t('m.Create_Assignment') }}</span>
                <el-button style="float: right;" @click="goBack">
                    {{ $t('m.Back') }}
                </el-button>
            </div>

            <el-form :model="assignmentForm" :rules="rules" ref="assignmentForm" label-width="120px">
                <el-form-item :label="$t('m.Title')" prop="title">
                    <el-input v-model="assignmentForm.title" :placeholder="$t('m.Title')" />
                </el-form-item>

                <el-form-item :label="$t('m.Description')" prop="description">
                    <el-input v-model="assignmentForm.description" type="textarea" :rows="4"
                        :placeholder="$t('m.Description')" />
                </el-form-item>

                <el-form-item :label="$t('m.Rule_Type')" prop="rule_type">
                    <el-select v-model="assignmentForm.rule_type" :placeholder="$t('m.Rule_Type')">
                        <el-option label="ACM" value="ACM" />
                        <el-option label="OI" value="OI" />
                    </el-select>
                </el-form-item>

                <el-form-item :label="$t('m.Is_Personalized')" prop="is_personalized">
                    <el-switch v-model="assignmentForm.is_personalized" active-color="#13ce66"
                        inactive-color="#ff4949" />
                </el-form-item>

                <el-form-item :label="$t('m.Start_Time')" prop="start_time">
                    <el-date-picker v-model="assignmentForm.start_time" type="datetime"
                        :placeholder="$t('m.Start_Time')" style="width: 100%" />
                </el-form-item>

                <el-form-item :label="$t('m.End_Time')" prop="end_time">
                    <el-date-picker v-model="assignmentForm.end_time" type="datetime" :placeholder="$t('m.End_Time')"
                        style="width: 100%" />
                </el-form-item>

                <el-form-item>
                    <el-button type="primary" @click="submitForm('assignmentForm')" :loading="loading">
                        {{ isEdit ? $t('m.Update') : $t('m.Create') }}
                    </el-button>
                    <el-button @click="resetForm('assignmentForm')">{{ $t('m.Reset') }}</el-button>
                </el-form-item>
            </el-form>
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
</style>