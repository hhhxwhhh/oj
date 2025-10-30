<template>
    <div class="assignment-student-progress-list">
        <div class="page-header">
            <el-button icon="el-icon-arrow-left" @click="goBack">返回</el-button>
            <h2>{{ assignment.title }} - 学生进度列表</h2>
        </div>

        <el-card class="filter-card">
            <div slot="header">
                <span>筛选</span>
            </div>
            <el-form :inline="true" :model="filterForm" class="filter-form">
                <el-form-item label="学生姓名">
                    <el-input v-model="filterForm.keyword" placeholder="请输入学生姓名或用户名" clearable></el-input>
                </el-form-item>
                <el-form-item label="状态">
                    <el-select v-model="filterForm.status" clearable placeholder="请选择状态">
                        <el-option label="已分配" value="assigned"></el-option>
                        <el-option label="进行中" value="in_progress"></el-option>
                        <el-option label="已完成" value="completed"></el-option>
                    </el-select>
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" icon="el-icon-search" @click="handleSearch">搜索</el-button>
                </el-form-item>
            </el-form>
        </el-card>

        <el-card class="progress-list-card">
            <div slot="header">
                <span>学生进度</span>
            </div>
            <el-table :data="studentAssignments" v-loading="loading" stripe style="width: 100%">
                <el-table-column prop="student_username" label="用户名" width="150"></el-table-column>
                <el-table-column prop="student_realname" label="姓名" width="150"></el-table-column>
                <el-table-column label="状态" width="120">
                    <template slot-scope="scope">
                        <el-tag :type="getStatusType(scope.row.status)">
                            {{ formatStatus(scope.row.status) }}
                        </el-tag>
                    </template>
                </el-table-column>
                <el-table-column label="分配时间" width="180">
                    <template slot-scope="scope">
                        {{ scope.row.assigned_time | localtime }}
                    </template>
                </el-table-column>
                <el-table-column label="完成时间" width="180">
                    <template slot-scope="scope">
                        {{ scope.row.completed_time | localtime }}
                    </template>
                </el-table-column>
                <el-table-column prop="score" label="得分" width="100"></el-table-column>
                <el-table-column prop="max_score" label="总分" width="100"></el-table-column>
                <el-table-column label="操作" width="150" fixed="right">
                    <template slot-scope="scope">
                        <el-button size="mini" type="primary" @click="viewProgress(scope.row)">查看详情</el-button>
                    </template>
                </el-table-column>
            </el-table>

            <div class="pagination-container">
                <el-pagination @current-change="handlePageChange" :current-page="currentPage" :page-size="pageSize"
                    :total="total" layout="prev, pager, next" background>
                </el-pagination>
            </div>
        </el-card>
    </div>
</template>

<script>
import api from '../../api.js'
import moment from 'moment'

export default {
    name: 'AssignmentStudentProgressList',
    filters: {
        localtime(date) {
            if (!date) return ''
            return moment(date).format('YYYY-MM-DD HH:mm')
        }
    },
    data() {
        return {
            assignmentId: '',
            assignment: {},
            studentAssignments: [],
            loading: false,
            currentPage: 1,
            pageSize: 10,
            total: 0,
            filterForm: {
                keyword: '',
                status: ''
            }
        }
    },
    created() {
        this.assignmentId = this.$route.params.assignmentId
        this.getAssignmentDetail()
        this.getStudentAssignments()
    },
    methods: {
        getAssignmentDetail() {
            api.getAssignment(this.assignmentId).then(res => {
                this.assignment = res.data.data
            })
        },
        getStudentAssignments() {
            this.loading = true
            const params = {
                page: this.currentPage,
                page_size: this.pageSize,
                keyword: this.filterForm.keyword,
                status: this.filterForm.status
            }

            // 使用ajax直接调用API，因为api.js中没有专门的方法
            api.$http.get(`/api/admin/assignments/${this.assignmentId}/student-assignments/`, { params })
                .then(res => {
                    this.loading = false
                    this.studentAssignments = res.data.data.results
                    this.total = res.data.data.count
                })
                .catch(() => {
                    this.loading = false
                    this.$message.error('获取学生作业列表失败')
                })
        },
        handleSearch() {
            this.currentPage = 1
            this.getStudentAssignments()
        },
        handlePageChange(page) {
            this.currentPage = page
            this.getStudentAssignments()
        },
        viewProgress(row) {
            this.$router.push({
                name: 'student-progress',
                params: {
                    assignmentId: this.assignmentId,
                    studentAssignmentId: row.id
                }
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
.assignment-student-progress-list {
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

.filter-card {
    margin-bottom: 20px;
}

.filter-form {
    display: flex;
    align-items: center;
}

.progress-list-card {
    margin-bottom: 20px;
}

.pagination-container {
    display: flex;
    justify-content: center;
    margin-top: 20px;
}
</style>