<template>
    <div class="inline-flex items-center">
        <template v-if="!edit && !record.edit_only">
            <template v-if="isRootRecord || isStage">
                <a-button type="link" class="px-0" @click="enableEditMode('stage')" :disabled="!template">
                    <span class="inline-flex justify-center w-6">
                        <i class="fi fi-rr-add"></i>
                    </span>
                    Добавить этап
                </a-button>
                <span class="mx-1">/</span>
            </template>
            <a-button type="link" class="px-0" @click="enableEditMode('task')" :disabled="!template">
                <span v-if="!isRootRecord && !isStage" class="inline-flex justify-center w-6">
                    <i  class="fi fi-rr-add"></i>
                </span>
                Добавить задачу
            </a-button>
            <span class="mx-1">/</span>
            <a-button type="link" class="px-0" @click="enableEditMode('milestone')" :disabled="!template">Добавить веху</a-button>
        </template>
        <template v-else>
            <a-form-model :model="form" ref="form" :rules="rules" layout="inline" >
                <a-form-model-item>
                    <a-tooltip :title="$t('cancel')">
                        <a-button 
                            type="link"
                            flaticon 
                            icon="fi-rr-cross" 
                            @click="disableEditMode">
                        </a-button>
                    </a-tooltip>
                </a-form-model-item>
                <a-form-model-item
                    prop="name">
                    <span ref="spanNameRef"></span>
                    <a-input
                        ref="nameInputRef"
                        class="min-w-[196px] max-w-[640px]"
                        @change="nameChange"
                        :placeholder="placeholders.name"
                        v-model="form.name"></a-input>
                </a-form-model-item>
                <a-form-model-item>
                    <a-input
                        :placeholder="placeholders.description"
                        v-model="form.description"/>
                </a-form-model-item>
                <template v-if="form.taskType === 'task'">
                    <a-form-model-item
                        prop="duration">
                        <a-input-number
                            :min="0"
                            class="w-full"
                            :placeholder="placeholders.duration"
                            v-model="form.duration"/>
                    </a-form-model-item>
                </template>
                <a-form-model-item>
                    <a-tooltip :title="$t('save')">
                        <a-button 
                            type="primary"
                            ghost
                            flaticon 
                            icon="fi-rr-disk" 
                            :loading="loading"
                            @click="submit">
                        </a-button>
                    </a-tooltip>
                </a-form-model-item>
            </a-form-model>
        </template>
    </div>
</template>

<script>
export default {
    props: {
        record: {
            type: Object,
            required: true
        },
        template: {
            type: String,
            default: ''
        }
    },
    components: {},
    data() {
        return {
            edit: false,
            loading: false,
            form: {
                name: "",
                description: "",
                duration: 0,
                taskType: ''
            },
        };
    },
    computed: {
        isStage() {
            return this.record.parentTaskType === 'stage';
        },
        isRootRecord() {
            return !this.record.parent
        },
        placeholders() {
            if (this.form.taskType === 'stage') {
                return {
                    name: this.$t('Stage name'),
                    description: this.$t('Stage description'),
                    duration: this.$t('Stage duration')
                }
                
            } 
            if (this.form.taskType === 'milestone') {
                return {
                    name: this.$t('Milestone name'),
                    description: this.$t('Milestone description'),
                    duration: this.$t('Milestone duration')
                }
            }
            return {
                name: this.$t('Task name'),
                description: this.$t('Task description'),
                duration: this.$t('Task duration')
            }
        },
        rules() {
            const rules = {
                name: [
                    { required: true, message: this.$t('project.field_require'), trigger: 'blur' },
                ],
                duration: [
                    { validator: this.durationValidator, required: false, message: this.$t('project.field_require'), trigger: 'blur' },
                ]
            }
            if (this.form.taskType === 'task') {
                rules.duration[0].required = true
            }   
            return rules
        },
    },
    created() {
        if (this.record.edit_only) {
            this.form = {
                ...this.record, 
                taskType: this.record.task_type,
                duration: Number(this.record.duration.replace(' 00:00:00', '')) || 0
            }
            
        }
    },
    methods: {
        nameChange(event) {
            const value = event.target.value
            this.$refs.nameInputRef.$el.style.width = value.length + 5 + "ch";
        },
        durationValidator(rule, value, callback) {
            if (value) {
                callback();
            } else {
                callback(new Error(this.$t('project.field_require')));
            }
        },
        submit() {
            this.$refs.form.validate()
                .then(() => {
                    if (this.record.edit_only) {
                        this.editTask()
                    } else {
                        this.createTask()
                    }
                })
                .catch(error => {
                    console.error(error);
                    this.$message.error(this.$t('error'));
                })
        },
        createTask() {
            const url = '/work_groups/task_templates/'
            const payload = {
                template: this.template,
                parent: this.record.parent || null,
                name: this.form.name,
                description: this.form.description,
                duration: `${this.form.duration} 00:00:00`,
                task_type: this.form.taskType
            }
            this.loading = true
            this.$http.post(url, payload)
                .then(({ data }) => {
                    this.updateRecord(data)
                    this.clearForm()
                })
                .catch(error => {
                    this.$message.error(this.$t('error'))
                    console.error(error)
                })
                .finally(() => {
                    this.loading = false
                })
        },
        editTask() {
            const url = `work_groups/task_templates/${this.record.id}/`
            const payload = {
                name: this.form.name,
                description: this.form.description,
                duration: `${this.form.duration} 00:00:00`,
                // task_type: this.record.task_type
            }
            this.loading = true
            this.$http.put(url, payload)
                .then(({ data }) => {
                    this.clearForm()
                    this.$store.commit('projects/EDIT_TEMPLATE_TABLE_ROW', { value: data, id: data.id })
                })
                .catch((error) => {
                    this.$message.error(this.$t('error'))
                    console.error(error)
                })
                .finally(() => {
                    this.loading = false
                })
        },
        updateRecord(value) {
            const payload = { value, id: this.record.id, indent: this.record.indent+1 }
            this.$store.commit('projects/UPDATE_TEMPLATE_TABLE_ROW', payload)

        },
        enableEditMode(taskType) {
            const payload = {
                task_type: taskType,
                record: this.record
            }
            this.$store.commit('projects/ADD_TEMPLATE_TABLE_ROW', payload)
            
            // return 0
            this.edit = true
            this.form.taskType = taskType
        },
        disableEditMode() {
            if (this.record.edit_only) {
                this.$store.commit('projects/EDIT_TEMPLATE_TABLE_ROW', { value: {
                    ...this.record,
                    is_action: false,
                    edit_only: false
                }, id: this.record.id })
            } else {
                this.$store.commit('projects/REMOVE_TEMPLATE_TABLE_ROW', { id: this.record.id })
            }
        },
        clearForm() {
            this.form = {
                name: '',
                description: '',
                duration: 0,
                taskType: ''
            }
        }
    },
};
</script>