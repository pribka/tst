<template>
    <a-spin :spinning="loading" class="add-initiative-wrapper">
        <div class="task-select">
            <a-form-model :model="form" ref="initiative_form">
                <a-form-model-item
                    prop="task"
                    ref="task"
                    class="mb-0"
                    :rules="{
                        required: true,
                        message: '',
                        trigger: ['change', 'blur'],
                    }">
                    <div class="flex items-center">
                        <i class="fi fi-rr-rectangle-list mr-3"></i>
                        <TaskSelectDrawer
                            v-model="form.task"
                            :placeholder="$t('okr.selectTask')" />
                        <a-popover 
                            v-model="fastTaskVisible"
                            :title="$t('okr.createNewTask')" 
                            :getPopupContainer="trigger => trigger.parentElement"
                            trigger="click"
                            @visibleChange="fastTaskVisibleChange($event)">
                            <a-button 
                                flaticon 
                                class="n_t_btn"
                                icon="fi-rr-plus" />
                            <template slot="content">
                                <a-form-model
                                    ref="fast_task_form"
                                    class="fast_task_form"
                                    :model="fastTaskForm">
                                    <a-form-model-item 
                                        ref="name" 
                                        :label="$t('okr.taskName')" 
                                        class="mb-2"
                                        :rules="{
                                            required: true,
                                            message: $t('field_required'),
                                            trigger: 'blur'
                                        }"
                                        prop="name">
                                        <a-input 
                                            v-model="fastTaskForm.name" 
                                            ref="fastTaskFormInput"
                                            :placeholder="$t('okr.taskName')"
                                            size="large"
                                            @pressEnter="onFastTaskSubmit" />
                                    </a-form-model-item>
                                    <div class="flex items-center">
                                        <a-button 
                                            type="primary" 
                                            :loading="fastTaskLoading"
                                            block 
                                            @click="onFastTaskSubmit">
                                            {{ $t('okr.createTask') }}
                                        </a-button>
                                        <a-button 
                                            type="ui_ghost" 
                                            block 
                                            class="ml-1"
                                            ghost
                                            @click="fastTaskVisible = false">
                                            {{ $t('okr.cancel') }}
                                        </a-button>
                                    </div>
                                </a-form-model>
                            </template>
                        </a-popover>
                    </div>
                </a-form-model-item>
            </a-form-model>
        </div>
        <div class="buttons"></div>
    </a-spin>
</template>
<script>
import TaskSelectDrawer from '@apps/WorkPlan/TaskSelectDrawer.vue'
import { taskFields } from '@apps/WorkPlan/utils.js'

export default {
    name: 'AddTask',
    components: {
        TaskSelectDrawer
    },
    data() {
        return {
            loading: false,
            fastTaskVisible: false,
            fastTaskLoading: false,
            fastTaskForm: {
                name: ""
            },
            form: {
                task: undefined
            }
        }
    },
    computed: {
        currentContractorID() {
            return this.$store.state.user.user.current_contractor.id || null
        },
        user() {
            return this.$store.state.user.user
        },
    },
    methods: {
        resetForm() {
            this.$refs.initiative_form.resetFields()
            if (this.$refs.fast_task_form)
                this.$refs.fast_task_form.resetFields()
        },
        fastTaskVisibleChange(vis) {
            if(!vis) {
                this.fastTaskForm = {
                    name: ""
                }
            }
        },
        onFastTaskSubmit() {
            this.$nextTick(() => {
                this.$refs.fast_task_form.validate(async valid => {
                    if (valid) {
                        try {
                            this.fastTaskLoading = true
                            const res = await this.$store.dispatch("task/addTask", {
                                ...this.fastTaskForm,
                                organization: {
                                    id: this.currentContractorID
                                },
                                operator: this.user.id,
                                owner: this.user.id,
                                ...taskFields
                            })
                            if(res) {
                                this.form.task = res
                                this.fastTaskForm = {
                                    name: ""
                                }
                                this.fastTaskVisible = false
                            }
                        } catch(error) {
                            console.log(error)
                            if (error?.length) this.$message.error(error.join(", "))
                            else this.$message.error(this.$t("task.error"))
                        } finally {
                            this.fastTaskLoading = false
                        }
                    } else {
                        return false
                    }
                })
            })
        }
    }
}
</script>
<style lang="scss" scoped>
.fast_task_form{
    min-width: 400px;
}
.n_t_btn{
    height: 40px;
    width: 40px;
    font-size: 14px;
    border-top-left-radius: 0;
    border-bottom-left-radius: 0;
}
.add-initiative-wrapper {
    width: 100%;
    .title {
        display: flex;
        justify-content: space-between;
        align-items: center;
        .label {
            font-size: 16px;
            color: #2D2D2D;
            font-weight: 600;
        }
        .close-icon {
            cursor: pointer;
            font-size: 14px;
        }
    }
    .task-select {
        margin-top: 12px;
    }
    .fast_task_form{
        min-width: 400px;
    }
}
</style>