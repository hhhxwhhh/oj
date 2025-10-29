<template>
    <div class="assignment-detail">
        <el-card class="box-card">
            <div slot="header" class="clearfix">
                <span>{{ assignment.title }}</span>
                <el-button style="float: right; margin-left: 10px;" type="primary" @click="handleAssign">
                    {{ $t('m.Assign_To_Students') }}
                </el-button>
                <el-button style="float: right;" @click="goBack">
                    {{ $t('m.Back') }}
                </el-button>
            </div>

            <el-card class="statistics-card">
                <div slot="header">
                    <span>统计信息</span>
                    <el-button style="float: right; padding: 3px 0" type="text" @click="viewStatistics">查看详情</el-button>
                </div>
                <el-row :gutter="20">
                    <el-col :span="6">
                        <div class="stat-item">
                            <p class="stat-value">{{ statistics.total_students || 0 }}</p>
                            <p class="stat-label">总学生数</p>
                        </div>
                    </el-col>
                    <el-col :span="6">
                        <div class="stat-item">
                            <p class="stat-value">{{ statistics.submitted_students || 0 }}</p>
                            <p class="stat-label">已提交</p>
                        </div>
                    </el-col>
                    <el-col :span="6">
                        <div class="stat-item">
                            <p class="stat-value">{{ statistics.average_score || 0 }}</p>
                            <p class="stat-label">平均分</p>
                        </div>
                    </el-col>
                    <el-col :span="6">
                        <div class="stat-item">
                            <p class="stat-value">{{ statistics.completion_percentage || 0 }}%</p>
                            <p class="stat-label">完成率</p>
                        </div>
                    </el-col>
                </el-row>
            </el-card>
            <el-card class="analysis-card">
                <div slot="header">
                    <span>分析仪表板</span>
                    <el-button style="float: right; padding: 3px 0" type="text" @click="viewDashboard">查看详情</el-button>
                </div>
                <p>查看该作业的详细分析报告，包括学生表现趋势、题目难度分析等。</p>
            </el-card>
            <el-row :gutter="20">
                <el-col :span="16">
                    <el-card class="info-card">
                        <div slot="header">
                            <span>{{ $t('m.Information') }}</span>
                        </div>
                        <el-form label-width="120px">
                            <el-form-item :label="$t('m.Title')">
                                <span>{{ assignment.title }}</span>
                            </el-form-item>
                            <el-form-item :label="$t('m.Description')">
                                <span>{{ assignment.description }}</span>
                            </el-form-item>
                            <el-form-item :label="$t('m.Creator')">
                                <span>{{ assignment.creator_username }}</span>
                            </el-form-item>
                            <el-form-item :label="$t('m.Rule_Type')">
                                <span>{{ assignment.rule_type }}</span>
                            </el-form-item>
                            <el-form-item :label="$t('m.Is_Personalized')">
                                <el-tag :type="assignment.is_personalized ? 'success' : 'info'">
                                    {{ assignment.is_personalized ? $t('m.Yes') : $t('m.No') }}
                                </el-tag>
                            </el-form-item>
                            <el-form-item :label="$t('m.Start_Time')">
                                <span>{{ assignment.start_time }}</span>
                            </el-form-item>
                            <el-form-item :label="$t('m.End_Time')">
                                <span>{{ assignment.end_time }}</span>
                            </el-form-item>
                        </el-form>
                    </el-card>

                    <el-card class="problems-card" style="margin-top: 20px;">
                        <div slot="header">
                            <span>{{ $t('m.Problems') }}</span>
                            <el-button style="float: right;" type="primary" icon="el-icon-plus"
                                @click="showAddProblemDialog = true">
                                {{ $t('m.Add_Problem') }}
                            </el-button>
                        </div>

                        <el-table :data="problems" style="width: 100%">
                            <el-table-column prop="problem._id" label="ID" width="80" />
                            <el-table-column prop="problem.title" :label="$t('m.Title')" />
                            <el-table-column prop="score" :label="$t('m.Score')" width="100" />
                            <el-table-column :label="$t('m.Operation')" width="100">
                                <template slot-scope="scope">
                                    <el-button size="mini" type="danger" @click="removeProblem(scope.row)">
                                        {{ $t('m.Delete') }}
                                    </el-button>
                                </template>
                            </el-table-column>
                        </el-table>
                    </el-card>
                </el-col>

                <el-col :span="8">
                    <el-card class="assigned-students-card">
                        <div slot="header">
                            <span>{{ $t('m.Assigned_Students') }}</span>
                            <el-button style="float: right;" type="success" @click="refreshAssignedStudents">
                                {{ $t('m.Refresh') }}
                            </el-button>
                        </div>

                        <el-table :data="assignedStudents" style="width: 100%">
                            <el-table-column prop="student_username" :label="$t('m.Username')" />
                            <el-table-column prop="student_realname" :label="$t('m.Real_Name')" />
                            <el-table-column prop="status" :label="$t('m.Status')" />
                        </el-table>
                    </el-card>
                </el-col>
            </el-row>
        </el-card>

        <!-- 添加题目对话框 -->
        <el-dialog :title="$t('m.Add_Problem')" :visible.sync="showAddProblemDialog" width="50%">
            <el-form :model="newProblem" label-width="100px">
                <el-form-item :label="$t('m.Problem_ID')">
                    <el-input v-model="newProblem.problem_id" />
                </el-form-item>
                <el-form-item :label="$t('m.Score')">
                    <el-input-number v-model="newProblem.score" :min="0" :max="100" />
                </el-form-item>
            </el-form>

            <span slot="footer" class="dialog-footer">
                <el-button @click="showAddProblemDialog = false">{{ $t('m.Cancel') }}</el-button>
                <el-button type="primary" @click="addProblem">{{ $t('m.Submit') }}</el-button>
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
        addProblem() {
            api.addProblemToAssignment(this.assignmentId, this.newProblem).then(res => {
                this.showAddProblemDialog = false
                this.newProblem = {
                    problem_id: '',
                    score: 0
                }
                this.getAssignmentProblems()
                this.$message({
                    type: 'success',
                    message: this.$t('m.Add_Successfully')
                })
            })
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