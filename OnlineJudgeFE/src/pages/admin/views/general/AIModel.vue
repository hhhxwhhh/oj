、<template>
    <div class="ai-model">
        <Panel :title="$t('m.AI_Model_Admin')">
            <div slot="header">
                <el-row :gutter="20">
                    <el-col :span="24">
                        <el-button type="primary" icon="el-icon-plus" @click="openModal()">
                            {{ $t('m.Create') }}
                        </el-button>
                    </el-col>
                </el-row>
            </div>

            <el-table v-loading="loadingTable" element-loading-text="loading" :data="aiModels" style="width: 100%">

                <el-table-column prop="name" :label="$t('m.Name')">
                </el-table-column>

                <el-table-column prop="provider" :label="$t('m.Provider')">
                </el-table-column>

                <el-table-column prop="model" :label="$t('m.Model')">
                </el-table-column>

                <el-table-column prop="api_key" :label="$t('m.API_Key')">
                    <template slot-scope="scope">
                        <!-- Hide middle part of API key for privacy -->
                        <span v-if="scope.row.api_key && scope.row.api_key.length > 8">
                            {{ scope.row.api_key.substring(0, 4) }}****{{
                                scope.row.api_key.substring(scope.row.api_key.length - 4) }}
                        </span>
                        <span v-else>****</span>
                    </template>
                </el-table-column>

                <el-table-column prop="is_active" :label="$t('m.Active')">
                    <template slot-scope="scope">
                        <el-tag :type="scope.row.is_active ? 'success' : 'danger'">
                            {{ scope.row.is_active ? $t('m.Yes') : $t('m.No') }}
                        </el-tag>
                    </template>
                </el-table-column>

                <el-table-column prop="create_time" :label="$t('m.Create_Time')">
                    <template slot-scope="scope">
                        {{ scope.row.create_time | localtime }}
                    </template>
                </el-table-column>

                <el-table-column prop="update_time" :label="$t('m.Update_Time')">
                    <template slot-scope="scope">
                        {{ scope.row.update_time | localtime }}
                    </template>
                </el-table-column>

                <el-table-column :label="$t('m.Operation')" width="200">
                    <template slot-scope="scope">
                        <el-button type="primary" size="mini" icon="el-icon-edit" @click="openModal(scope.row)">
                            {{ $t('m.Edit') }}
                        </el-button>
                        <el-button type="danger" size="mini" icon="el-icon-delete" @click="deleteModel(scope.row.id)">
                            {{ $t('m.Delete') }}
                        </el-button>
                    </template>
                </el-table-column>
            </el-table>
        </Panel>

        <el-dialog :title="modalTitle" :visible.sync="modalVisible" width="600px" :close-on-click-modal="false">

            <el-form ref="form" :model="form" :rules="ruleValidate" label-position="top">

                <el-form-item :label="$t('m.Name')" prop="name">
                    <el-input v-model="form.name" :placeholder="$t('m.Name')" id="ai-model-name" />
                    <div class="form-item-description">A unique name to identify this AI model</div>
                </el-form-item>

                <el-form-item :label="$t('m.Provider')" prop="provider">
                    <el-select v-model="form.provider" :placeholder="$t('m.Provider')" style="width: 100%"
                        id="ai-model-provider">
                        <el-option value="openai" label="OpenAI"></el-option>
                        <el-option value="azure" label="Azure OpenAI"></el-option>
                    </el-select>
                    <div class="form-item-description">The AI service provider</div>
                </el-form-item>

                <el-form-item :label="$t('m.API_Key')" prop="api_key">
                    <el-input v-model="form.api_key" :placeholder="$t('m.API_Key')" type="password"
                        id="ai-model-api-key" />
                    <div class="form-item-description">The authentication key for accessing the AI service</div>
                </el-form-item>

                <el-form-item :label="$t('m.Model')" prop="model">
                    <el-input v-model="form.model" :placeholder="$t('m.Model')" id="ai-model-model" />
                    <div class="form-item-description">The specific model name (e.g., gpt-3.5-turbo)</div>
                </el-form-item>

                <el-form-item :label="$t('m.Config')" prop="config">
                    <el-input v-model="form.config" placeholder="Configuration in JSON format" type="textarea" :rows="4"
                        id="ai-model-config" />
                    <div class="form-item-description">Additional configuration in JSON format (optional)</div>
                </el-form-item>

                <el-form-item :label="$t('m.Active')" prop="is_active">
                    <el-switch v-model="form.is_active" id="ai-model-active"></el-switch>
                    <div class="form-item-description">Whether this model is active and can be used</div>
                </el-form-item>
            </el-form>

            <span slot="footer" class="dialog-footer">
                <el-button @click="cancelModal">Cancel</el-button>
                <el-button type="primary" @click="saveModel" :loading="loadingModal">
                    Confirm
                </el-button>
            </span>
        </el-dialog>
    </div>
</template>

<script>
import api from '../../api'

export default {
    name: 'ai-model',
    data() {
        return {
            aiModels: [],
            loadingTable: false,
            loadingModal: false,
            modalVisible: false,
            modalMode: 'create',
            form: {
                id: null,
                name: '',
                provider: 'openai',
                api_key: '',
                model: '',
                config: '{}',
                is_active: true
            },
            ruleValidate: {
                name: [
                    { required: true, message: 'Name is required', trigger: 'blur' }
                ],
                provider: [
                    { required: true, message: 'Provider is required', trigger: 'change' }
                ],
                api_key: [
                    { required: true, message: 'API Key is required', trigger: 'blur' }
                ],
                model: [
                    { required: true, message: 'Model is required', trigger: 'blur' }
                ]
            }
        }
    },
    mounted() {
        this.getAIModels()
    },
    methods: {
        getAIModels() {
            this.loadingTable = true
            api.getAIModels().then(res => {
                this.aiModels = res.data.data
                this.loadingTable = false
            }).catch(() => {
                this.loadingTable = false
            })
        },

        openModal(model = null) {
            if (model) {
                this.modalMode = 'edit'
                this.form = Object.assign({}, model)
                // Handle config field
                this.form.config = JSON.stringify(model.config, null, 2)
            } else {
                this.modalMode = 'create'
                this.form = {
                    id: null,
                    name: '',
                    provider: 'openai',
                    api_key: '',
                    model: '',
                    config: '{}',
                    is_active: true
                }
            }
            this.modalVisible = true
        },

        cancelModal() {
            this.modalVisible = false
        },

        saveModel() {
            this.$refs.form.validate((valid) => {
                if (!valid) {
                    return
                }

                // Validate and process config field
                let config = {}
                try {
                    config = JSON.parse(this.form.config)
                } catch (e) {
                    this.$error('Config is not valid JSON format')
                    return
                }

                const data = {
                    name: this.form.name,
                    provider: this.form.provider,
                    api_key: this.form.api_key,
                    model: this.form.model,
                    config: config,
                    is_active: this.form.is_active
                }

                if (this.modalMode === 'create') {
                    api.createAIModel(data).then(res => {
                        this.$success('Created successfully')
                        this.modalVisible = false
                        this.getAIModels()
                    }).catch(() => {
                        // Error handling is done in api module
                    })
                } else {
                    data.id = this.form.id
                    api.updateAIModel(data).then(res => {
                        this.$success('Updated successfully')
                        this.modalVisible = false
                        this.getAIModels()
                    }).catch(() => {
                        // Error handling is done in api module
                    })
                }
            })
        },

        deleteModel(id) {
            this.$confirm('Are you sure you want to delete this AI model?', 'Delete AI Model', {
                confirmButtonText: 'Confirm',
                cancelButtonText: 'Cancel',
                type: 'warning'
            }).then(() => {
                api.deleteAIModel(id).then(res => {
                    this.$success('Deleted successfully')
                    this.getAIModels()
                })
            }).catch(() => {
                // Cancelled
            })
        }
    },
    computed: {
        modalTitle() {
            return this.modalMode === 'create' ? 'Create AI Model' : 'Edit AI Model'
        }
    }
}
</script>

<style scoped>
.ai-model {
    margin: 10px;
}

.form-item-description {
    font-size: 12px;
    color: #888;
    margin-top: 5px;
}
</style>