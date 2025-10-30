<template>
    <div class="view">
        <Panel :title="$t('m.Assignment_List')">
            <div slot="header">
                <el-input v-model="keyword" prefix-icon="el-icon-search" :placeholder="$t('m.Keyword_Search')"
                    style="width: 200px; margin-right: 10px;">
                </el-input>
                <el-button type="primary" icon="el-icon-plus" @click="createAssignment" size="small">
                    {{ $t('m.Create') }}
                </el-button>
            </div>
            <el-table v-loading="loading" :data="assignments" element-loading-text="loading" style="width: 100%;" stripe
                :header-cell-style="{ background: '#fafafa' }">
                <el-table-column prop="id" label="ID" width="60" />
                <el-table-column prop="title" :label="$t('m.Title')" min-width="200" show-overflow-tooltip />
                <el-table-column prop="creator_username" :label="$t('m.Creator')" width="100" />
                <el-table-column :label="$t('m.Rule_Type')" width="90" align="center">
                    <template slot-scope="scope">
                        <el-tag :type="scope.row.rule_type === 'ACM' ? 'primary' : 'success'" size="mini">
                            {{ scope.row.rule_type }}
                        </el-tag>
                    </template>
                </el-table-column>
                <el-table-column :label="$t('m.Is_Personalized')" width="100" align="center">
                    <template slot-scope="scope">
                        <el-tag :type="scope.row.is_personalized ? 'success' : 'info'" size="mini">
                            {{ scope.row.is_personalized ? $t('m.Yes') : $t('m.No') }}
                        </el-tag>
                    </template>
                </el-table-column>
                <el-table-column :label="$t('m.Start_Time')" width="150">
                    <template slot-scope="scope">
                        {{ scope.row.start_time | localtime }}
                    </template>
                </el-table-column>
                <el-table-column :label="$t('m.End_Time')" width="150">
                    <template slot-scope="scope">
                        {{ scope.row.end_time | localtime }}
                    </template>
                </el-table-column>
                <el-table-column :label="$t('m.Operation')" width="220">
                    <template slot-scope="scope">
                        <el-button size="mini" type="primary" @click="handleEdit(scope.row)" style="margin: 2px;">
                            {{ $t('m.Edit') }}
                        </el-button>
                        <el-button size="mini" type="success" @click="handleAssign(scope.row)" style="margin: 2px;">
                            {{ $t('m.Assign') }}
                        </el-button>
                        <el-button size="mini" @click="handleDetail(scope.row)" style="margin: 2px;">
                            {{ $t('m.Detail') }}
                        </el-button>
                        <el-button size="mini" type="danger" @click="handleDelete(scope.row)" style="margin: 2px;">
                            {{ $t('m.Delete') }}
                        </el-button>
                    </template>
                </el-table-column>
                <el-table-column :label="$t('m.Actions')" width="100" align="center">
                    <template slot-scope="scope">
                        <el-button size="mini" type="info" @click="viewProgress(scope.row)">查看进度</el-button>
                    </template>
                </el-table-column>
            </el-table>

            <div class="panel-options">
                <el-pagination class="page" :page-size="pageSize" :total="total" :current-page="currentPage"
                    @current-change="handleCurrentChange" layout="prev, pager, next" />
            </div>
        </Panel>
    </div>
</template>

<script>
import api from '../../api.js'
import moment from 'moment'

export default {
    name: 'AssignmentList',
    filters: {
        localtime(date) {
            if (!date) return ''
            return moment(date).format('YYYY-MM-DD HH:mm')
        }
    },
    data() {
        return {
            assignments: [],
            loading: false,
            currentPage: 1,
            total: 0,
            pageSize: 10,
            keyword: ''
        }
    },
    watch: {
        keyword() {
            // 当搜索关键词变化时，重置到第一页
            this.currentPage = 1
            this.getAssignments()
        }
    },
    created() {
        this.getAssignments()
    },
    methods: {
        getAssignments() {
            this.loading = true
            api.getAssignmentList(this.currentPage, this.pageSize, this.keyword)
                .then(res => {
                    this.loading = false
                    if (res.data.results) {
                        this.assignments = res.data.results
                        this.total = res.data.count
                    } else {
                        this.assignments = res.data.data.results
                        this.total = res.data.data.total
                    }
                })
                .catch(() => {
                    this.loading = false
                })
        },
        handleCurrentChange(page) {
            this.currentPage = page
            this.getAssignments()
        },
        createAssignment() {
            this.$router.push({ name: 'create-assignment' })
        },
        handleEdit(row) {
            this.$router.push({
                name: 'edit-assignment',
                params: { assignmentId: row.id }
            })
        },
        handleAssign(row) {
            this.$router.push({
                name: 'assignment-detail',
                params: { assignmentId: row.id }
            })
        },
        handleDetail(row) {
            this.$router.push({
                name: 'assignment-detail',
                params: { assignmentId: row.id }
            })
        },
        viewProgress(row) {
            // 跳转到作业详情页面，然后在详情页面中可以查看已分配学生的进度
            this.$router.push({
                name: 'assignment-detail',
                params: { assignmentId: row.id }
            })
        },
        handleDelete(row) {
            this.$confirm(this.$t('m.Delete_Assignment_Tips'), this.$t('m.Warning'), {
                confirmButtonText: this.$t('m.OK'),
                cancelButtonText: this.$t('m.Cancel'),
                type: 'warning'
            }).then(() => {
                api.deleteAssignment(row.id).then(res => {
                    this.getAssignments()
                    this.$message({
                        type: 'success',
                        message: this.$t('m.Delete_Successfully')
                    })
                }).catch(() => {
                    this.$message({
                        type: 'error',
                        message: this.$t('m.Delete_Failed')
                    })
                })
            }).catch(() => {
                this.$message({
                    type: 'info',
                    message: this.$t('m.Delete_Cancelled')
                })
            })
        }
    }
}
</script>

<style scoped>
.panel-options {
    display: flex;
    justify-content: center;
    margin-top: 20px;
}
</style>