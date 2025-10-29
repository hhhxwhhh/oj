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
                    <el-button type="primary" @click="submitForm('assignmentForm')">
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
            api.getAssignment(this.assignmentId).then(res => {
                const data = res.data.data
                this.assignmentForm = {
                    title: data.title,
                    description: data.description,
                    rule_type: data.rule_type,
                    is_personalized: data.is_personalized,
                    start_time: data.start_time,
                    end_time: data.end_time
                }
            })
        },
        submitForm(formName) {
            this.$refs[formName].validate((valid) => {
                if (valid) {
                    if (this.isEdit) {
                        // 更新作业
                        api.updateAssignment(this.assignmentId, this.assignmentForm).then(res => {
                            this.$message({
                                type: 'success',
                                message: this.$t('m.Update_Successfully')
                            })
                            this.goBack()
                        })
                    } else {
                        // 创建作业
                        api.createAssignment(this.assignmentForm).then(res => {
                            this.$message({
                                type: 'success',
                                message: this.$t('m.Create_Successfully')
                            })
                            this.goBack()
                        })
                    }
                }
            })
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