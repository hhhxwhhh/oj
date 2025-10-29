<template>
    <div class="assignment-list">
        <el-card class="box-card">
            <div slot="header" class="clearfix">
                <span>{{ $t('m.Assignment_List') }}</span>
                <el-button style="float: right;" type="primary" icon="el-icon-plus" @click="createAssignment">
                    {{ $t('m.Create') }}
                </el-button>
            </div>

            <el-table v-loading="loading" :data="assignments" element-loading-text="loading" style="width: 100%;">
                <el-table-column prop="title" :label="$t('m.Title')" />
                <el-table-column prop="creator_username" :label="$t('m.Creator')" />
                <el-table-column :label="$t('m.Rule_Type')">
                    <template slot-scope="scope">
                        {{ scope.row.rule_type }}
                    </template>
                </el-table-column>
                <el-table-column :label="$t('m.Is_Personalized')">
                    <template slot-scope="scope">
                        <el-tag :type="scope.row.is_personalized ? 'success' : 'info'">
                            {{ scope.row.is_personalized ? $t('m.Yes') : $t('m.No') }}
                        </el-tag>
                    </template>
                </el-table-column>
                <el-table-column :label="$t('m.Start_Time')" prop="start_time" />
                <el-table-column :label="$t('m.End_Time')" prop="end_time" />
                <el-table-column :label="$t('m.Operation')" fixed="right" width="250">
                    <template slot-scope="scope">
                        <el-button size="mini" type="primary" @click="handleEdit(scope.row)">
                            {{ $t('m.Edit') }}
                        </el-button>
                        <el-button size="mini" type="success" @click="handleAssign(scope.row)">
                            {{ $t('m.Assign') }}
                        </el-button>
                        <el-button size="mini" type="info" @click="handleDetail(scope.row)">
                            {{ $t('m.Detail') }}
                        </el-button>
                        <el-button size="mini" type="danger" @click="handleDelete(scope.row)">
                            {{ $t('m.Delete') }}
                        </el-button>
                    </template>
                </el-table-column>
            </el-table>

            <div class="panel-options">
                <el-pagination class="page" :page-size="pageSize" :total="total" :current-page="currentPage"
                    @current-change="handleCurrentChange" layout="prev, pager, next" />
            </div>
        </el-card>
    </div>
</template>

<script>
import api from '../../api.js'

export default {
    name: 'AssignmentList',
    data() {
        return {
            assignments: [],
            loading: false,
            currentPage: 1,
            total: 0,
            pageSize: 10
        }
    },
    created() {
        this.getAssignments()
    },
    methods: {
        getAssignments() {
            this.loading = true
            api.getAssignmentList(this.currentPage - 1, this.pageSize)
                .then(res => {
                    this.loading = false
                    this.assignments = res.data.data.results
                    this.total = res.data.data.total
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
                name: 'edit-problem',
                params: { problemId: row.id }
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
.assignment-list {
    margin: 20px;
}
</style>