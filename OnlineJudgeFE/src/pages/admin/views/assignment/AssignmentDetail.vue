<template>
    <div class="assignment-detail">
        <!-- 作业信息卡片 -->
        <el-card class="info-card">
            <div slot="header">
                <span>{{ $t('m.Assignment_Detail') }}</span>
            </div>
            <el-row>
                <el-col :span="8">
                    <p><strong>{{ $t('m.Title') }}:</strong> {{ assignment.title }}</p>
                </el-col>
                <el-col :span="8">
                    <p><strong>{{ $t('m.Start_Time') }}:</strong> {{ assignment.start_time }}</p>
                </el-col>
                <el-col :span="8">
                    <p><strong>{{ $t('m.End_Time') }}:</strong> {{ assignment.end_time }}</p>
                </el-col>
            </el-row>
            <el-row>
                <el-col :span="24">
                    <p><strong>{{ $t('m.Description') }}:</strong> {{ assignment.description }}</p>
                </el-col>
            </el-row>
        </el-card>

        <!-- 题目卡片 -->
        <el-card class="problems-card" style="margin-top: 20px;">
            <div slot="header">
                <span>{{ $t('m.Problems') }}</span>
                <el-button style="float: right; padding: 3px 0" type="primary" size="small"
                    @click="showAddProblemDialog = true">
                    {{ $t('m.Add_Problem') }}
                </el-button>
            </div>
            <el-table :data="problems" style="width: 100%">
                <el-table-column prop="problem._id" label="ID" width="80" />
                <el-table-column prop="problem.title" :label="$t('m.Title')" />
                <el-table-column prop="score" :label="$t('m.Score')" width="100" />
                <el-table-column fixed="right" :label="$t('m.Option')" width="100">
                    <template slot-scope="scope">
                        <el-button size="mini" type="danger" @click="removeProblem(scope.row)">
                            {{ $t('m.Delete') }}
                        </el-button>
                    </template>
                </el-table-column>
            </el-table>
        </el-card>

        <!-- 添加题目对话框 -->
        <el-dialog :title="$t('m.Add_Problem')" :visible.sync="showAddProblemDialog" width="70%">
            <el-row :gutter="20">
                <el-col :span="12">
                    <el-card>
                        <div slot="header">
                            <span>{{ $t('m.Search_Problems') }}</span>
                        </div>
                        <el-input v-model="searchKeyword" :placeholder="$t('m.Keyword_Search')"
                            prefix-icon="el-icon-search" @input="searchProblems">
                        </el-input>
                        <el-table :data="searchResults" v-loading="searchLoading" style="width: 100%; margin-top: 10px;"
                            height="300" @row-click="selectProblem">
                            <el-table-column prop="_id" label="ID" width="100"></el-table-column>
                            <el-table-column prop="title" :label="$t('m.Title')"></el-table-column>
                        </el-table>
                        <el-pagination layout="prev, pager, next" :current-page="searchPage" :page-size="searchLimit"
                            :total="searchTotal" @current-change="handlePageChange"
                            style="margin-top: 10px; text-align: center;">
                        </el-pagination>
                    </el-card>
                </el-col>
                <el-col :span="12">
                    <el-card>
                        <div slot="header">
                            <span>{{ $t('m.Selected_Problem') }}</span>
                        </div>
                        <div v-if="selectedProblem">
                            <p><strong>ID:</strong> {{ selectedProblem._id }}</p>
                            <p><strong>{{ $t('m.Title') }}:</strong> {{ selectedProblem.title }}</p>
                            <el-form :model="newProblem" label-width="100px" style="margin-top: 20px;">
                                <el-form-item :label="$t('m.Score')">
                                    <el-input-number v-model="newProblem.score" :min="0" :max="100" />
                                </el-form-item>
                            </el-form>
                        </div>
                        <div v-else>
                            <p>{{ $t('m.Please_select_a_problem') }}</p>
                        </div>
                    </el-card>
                </el-col>
            </el-row>

            <span slot="footer" class="dialog-footer">
                <el-button @click="showAddProblemDialog = false">{{ $t('m.Cancel') }}</el-button>
                <el-button type="primary" @click="addProblem" :disabled="!selectedProblem">
                    {{ $t('m.Submit') }}
                </el-button>
            </span>
        </el-dialog>

        <!-- 分配作业对话框 -->
        <el-dialog :title="$t('m.Assign_To_Students')" :visible.sync="showAssignDialog" width="50%">
            <el-form :model="assignForm" label-width="120px">
                <el-form-item :label="$t('m.Assign_Type')">
                    <el-radio-group v-model="assignForm.assignType">
                        <el-radio label="specific">{{ $t('m.Specific_Students') }}</el-radio>
                        <el-radio label="all">{{ $t('m.All_Students') }}</el-radio>
                    </el-radio-group>
                </el-form-item>

                <el-form-item v-if="assignForm.assignType === 'specific'" :label="$t('m.Select_Students')">
                    <el-select v-model="assignForm.student_ids" multiple filterable
                        :placeholder="$t('m.Select_Students')" style="width: 100%">
                        <el-option v-for="student in students" :key="student.id"
                            :label="student.username + ' (' + student.real_name + ')'" :value="student.id" />
                    </el-select>
                </el-form-item>
            </el-form>

            <span slot="footer" class="dialog-footer">
                <el-button @click="showAssignDialog = false">{{ $t('m.Cancel') }}</el-button>
                <el-button type="primary" @click="assignToStudents">{{ $t('m.Assign') }}</el-button>
            </span>
        </el-dialog>
    </div>
</template>

<script>
import api from '../../api.js'

export default {
    name: 'AssignmentDetail',
    data() {
        return {
            assignmentId: '',
            assignment: {},
            problems: [],
            assignedStudents: [],
            students: [],
            showAddProblemDialog: false,
            showAssignDialog: false,
            newProblem: {
                problem_id: '',
                score: 0
            },
            assignForm: {
                assignType: 'specific',
                student_ids: []
            },
            statistics: {
                total_students: 0,
                submitted_students: 0,
                average_score: 0,
                completion_percentage: 0
            },
            // 新增的搜索相关数据
            searchKeyword: '',
            searchResults: [],
            searchLoading: false,
            searchPage: 1,
            searchLimit: 10,
            searchTotal: 0,
            selectedProblem: null
        }
    },
    created() {
        this.assignmentId = this.$route.params.assignmentId
        this.getAssignmentDetail()
        this.getAssignmentProblems()
        this.getAssignedStudents()
        this.getAssignmentStatistics()
        this.getAllStudents()
    },
    methods: {
        getAssignmentDetail() {
            api.getAssignment(this.assignmentId).then(res => {
                this.assignment = res.data.data
            })
        },
        getAssignmentProblems() {
            api.getAssignmentProblems(this.assignmentId).then(res => {
                this.problems = res.data.data
            })
        },
        getAssignmentStatistics() {
            api.getAssignmentDetailedStatistics(this.assignmentId).then(res => {
                this.statistics = res.data.data
            })
        },
        viewStatistics() {
            this.$router.push({
                name: 'assignment-statistics',
                params: { assignmentId: this.assignmentId }
            })
        },
        getAssignedStudents() {
            api.getAssignedStudents(this.assignmentId).then(res => {
                this.assignedStudents = res.data.data
            })
        },
        getAllStudents() {
            api.getUserList(1, 1000, 'Regular User').then(res => {
                this.students = res.data.data.results
            })
        },
        refreshAssignedStudents() {
            this.getAssignedStudents()
        },
        // 修改搜索题目方法
        searchProblems() {
            this.searchPage = 1;
            this.fetchProblems();
        },
        // 获取题目列表
        fetchProblems(page = 1) {
            this.searchLoading = true;
            const params = {
                keyword: this.searchKeyword,
                offset: (page - 1) * this.searchLimit,
                limit: this.searchLimit,
                is_public: true  // 只获取公开题目
            };

            api.getProblemList(params).then(res => {
                this.searchLoading = false;
                this.searchTotal = res.data.data.total;
                this.searchResults = res.data.data.results;
            }).catch(() => {
                this.searchLoading = false;
            });
        },
        // 处理分页变化
        handlePageChange(page) {
            this.searchPage = page;
            this.fetchProblems(page);
        },
        // 选择题目
        selectProblem(row) {
            this.selectedProblem = row;
            this.newProblem.problem_id = row._id;
        },
        // 添加题目
        addProblem() {
            if (!this.selectedProblem) {
                this.$message({
                    type: 'warning',
                    message: this.$t('m.Please_select_a_problem')
                });
                return;
            }

            api.addProblemToAssignment(this.assignmentId, this.newProblem).then(res => {
                this.showAddProblemDialog = false;
                this.newProblem = {
                    problem_id: '',
                    score: 0
                };
                this.selectedProblem = null;
                this.searchKeyword = '';
                this.searchResults = [];
                this.getAssignmentProblems();
                this.$message({
                    type: 'success',
                    message: this.$t('m.Add_Successfully')
                });
            }).catch(err => {
                let errorMessage = this.$t('m.Add_Failed');
                if (err.response && err.response.data && err.response.data.data) {
                    errorMessage = err.response.data.data;
                }
                this.$message({
                    type: 'error',
                    message: errorMessage
                });
            });
        },
        removeProblem(row) {
            this.$confirm(this.$t('m.Remove_Problem_Tips'), this.$t('m.Warning'), {
                confirmButtonText: this.$t('m.OK'),
                cancelButtonText: this.$t('m.Cancel'),
                type: 'warning'
            }).then(() => {
                api.removeProblemFromAssignment(this.assignmentId, row.problem.id).then(res => {
                    this.getAssignmentProblems()
                    this.$message({
                        type: 'success',
                        message: this.$t('m.Delete_Successfully')
                    })
                })
            })
        },
        handleAssign() {
            this.showAssignDialog = true
        },
        viewDashboard() {
            this.$router.push({
                name: 'assignment-dashboard',
                params: { assignmentId: this.assignmentId }
            })
        },


        assignToStudents() {
            const data = {
                all_students: this.assignForm.assignType === 'all',
                student_ids: this.assignForm.student_ids
            }

            api.assignAssignmentToStudents(this.assignmentId, data).then(res => {
                this.showAssignDialog = false
                this.getAssignedStudents()
                this.$message({
                    type: 'success',
                    message: res.data.data.message
                })
            })
        },
        goBack() {
            this.$router.push({ name: 'assignment-list' })
        }
    }
}
</script>

<style scoped>
.assignment-detail {
    margin: 20px;
}

.info-card,
.problems-card,
.assigned-students-card {
    margin-bottom: 20px;
}

.statistics-card {
    margin-bottom: 20px;
}

.stat-item {
    text-align: center;
}

.stat-value {
    font-size: 20px;
    font-weight: bold;
    margin: 0;
}

.stat-label {
    margin: 5px 0 0 0;
    color: #999;
}

.analysis-card {
    margin-bottom: 20px;
}
</style>