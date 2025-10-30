<template>
    <div class="student-progress">
        <div class="page-header">
            <el-button icon="el-icon-arrow-left" @click="goBack">返回</el-button>
            <h2>{{ assignment.title }} - 学生进度详情</h2>
        </div>

        <el-card class="student-info-card">
            <div slot="header">
                <span>学生信息</span>
            </div>
            <div class="student-info">
                <el-row :gutter="20">
                    <el-col :span="8">
                        <p><strong>学生:</strong> {{ studentAssignment.student_username }} ({{
                            studentAssignment.student_realname }})</p>
                    </el-col>
                    <el-col :span="8">
                        <p><strong>状态:</strong>
                            <el-tag :type="getStatusType(studentAssignment.status)">
                                {{ formatStatus(studentAssignment.status) }}
                            </el-tag>
                        </p>
                    </el-col>
                    <el-col :span="8">
                        <p><strong>分配时间:</strong> {{ studentAssignment.assigned_time | localtime }}</p>
                    </el-col>
                </el-row>
                <el-row :gutter="20" v-if="studentAssignment.completed_time">
                    <el-col :span="8">
                        <p><strong>完成时间:</strong> {{ studentAssignment.completed_time | localtime }}</p>
                    </el-col>
                    <el-col :span="8" v-if="studentAssignment.score !== null">
                        <p><strong>得分:</strong> {{ studentAssignment.score }} / {{ studentAssignment.max_score }}</p>
                    </el-col>
                </el-row>
            </div>
        </el-card>

        <el-card class="progress-summary-card">
            <div slot="header">
                <span>进度概览</span>
            </div>
            <div class="progress-summary">
                <el-row :gutter="20">
                    <el-col :span="6">
                        <div class="summary-item">
                            <p class="summary-value">{{ progressData.total_problems }}</p>
                            <p class="summary-label">总题目数</p>
                        </div>
                    </el-col>
                    <el-col :span="6">
                        <div class="summary-item">
                            <p class="summary-value">{{ progressData.solved_problems }}</p>
                            <p class="summary-label">已解决题目数</p>
                        </div>
                    </el-col>
                    <el-col :span="6">
                        <div class="summary-item">
                            <p class="summary-value">{{ progressData.completion_rate }}%</p>
                            <p class="summary-label">完成率</p>
                        </div>
                    </el-col>
                    <el-col :span="6">
                        <div class="summary-item">
                            <el-progress type="circle" :percentage="parseFloat(progressData.completion_rate)"
                                :width="80"></el-progress>
                        </div>
                    </el-col>
                </el-row>
            </div>
        </el-card>

        <el-card class="problems-progress-card">
            <div slot="header">
                <span>题目详情</span>
            </div>
            <div class="problems-progress">
                <el-table :data="progressData.problems" style="width: 100%" v-loading="loading" stripe>
                    <el-table-column prop="id" label="题目ID" width="100"></el-table-column>
                    <el-table-column prop="title" label="题目名称"></el-table-column>
                    <el-table-column prop="submission_count" label="提交次数" width="100"></el-table-column>
                    <el-table-column prop="accepted_count" label="通过次数" width="100"></el-table-column>
                    <el-table-column prop="best_score" label="最高分数" width="100"></el-table-column>
                    <el-table-column label="状态" width="100">
                        <template slot-scope="scope">
                            <el-tag :type="scope.row.is_solved ? 'success' : 'danger'">
                                {{ scope.row.is_solved ? '已解决' : '未解决' }}
                            </el-tag>
                        </template>
                    </el-table-column>
                </el-table>
            </div>
        </el-card>
    </div>
</template>

<script>
import api from '../../api.js'
import moment from 'moment'

export default {
    name: 'StudentProgress',
    filters: {
        localtime(date) {
            if (!date) return ''
            return moment(date).format('YYYY-MM-DD HH:mm:ss')
        }
    },
    data() {
        return {
            loading: true,
            assignmentId: '',
            studentAssignmentId: '',
            assignment: {},
            studentAssignment: {},
            progressData: {
                total_problems: 0,
                solved_problems: 0,
                completion_rate: 0,
                problems: []
            }
        }
    },
    created() {
        this.assignmentId = this.$route.params.assignmentId
        this.studentAssignmentId = this.$route.params.studentAssignmentId
        this.getAssignmentDetail()
        this.getStudentAssignmentDetail()
        this.getProgressData()
    },
    methods: {
        getAssignmentDetail() {
            api.getAssignment(this.assignmentId).then(res => {
                this.assignment = res.data.data
            })
        },
        getStudentAssignmentDetail() {
            // 获取学生作业详情
            api.getStudentAssignment(this.studentAssignmentId).then(res => {
                this.studentAssignment = res.data.data
            }).catch(() => {
                // 错误处理
            })
        },
        getProgressData() {
            api.getStudentAssignmentProgress(this.studentAssignmentId).then(res => {
                this.loading = false
                this.progressData = res.data.data
            }).catch(() => {
                this.loading = false
            })
        },
        goBack() {
            this.$router.go(-1)
        },
        formatStatus(status) {
            const statusMap = {
                'assigned': '已分配',
                'in_progress': '进行中',
                'completed': '已完成'
            }
            return statusMap[status] || status
        },
        getStatusType(status) {
            const typeMap = {
                'assigned': 'info',
                'in_progress': 'warning',
                'completed': 'success'
            }
            return typeMap[status] || 'info'
        }
    }
}
</script>

<style scoped>
.student-progress {
    margin: 20px;
}

.page-header {
    display: flex;
    align-items: center;
    margin-bottom: 20px;
}

.page-header h2 {
    margin-left: 15px;
}

.student-info-card,
.progress-summary-card,
.problems-progress-card {
    margin-bottom: 20px;
}

.student-info {
    padding: 10px 0;
}

.progress-summary {
    padding: 10px 0;
}

.summary-item {
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}

.summary-value {
    font-size: 24px;
    font-weight: bold;
    margin: 0;
    color: #409EFF;
}

.summary-label {
    margin: 5px 0 0 0;
    color: #999;
}

.problems-progress {
    padding: 10px 0;
}

.el-progress {
    margin-top: 10px;
}
</style>