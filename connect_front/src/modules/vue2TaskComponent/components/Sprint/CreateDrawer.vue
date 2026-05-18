<template>
    <DrawerTemplate
        v-model="visible"
        @close="visible = false"
        class="task_edit"
        :width="drawerWidth"
        @afterVisibleChange="afterVisibleChange">
        <template #title>
            <div class="drawer_title">{{ edit ? $t('task.edit_sprint') : $t('task.create_sprint') }}</div>
        </template>
        <template #rightHeader>
            <HelpButton partCode="sprints" />
        </template>
        <div ref="sprintFormWrapper" class="sp_body"> 
            <a-spin :spinning="sprintLoading" class="w-full">
                <a-form-model
                    ref="sprintForm"
                    :model="form"
                    :rules="rules">
                    <a-form-model-item
                        ref="name"
                        :label="$t('task.sprint_name')"
                        prop="name">
                        <a-input
                            v-model="form.name"
                            size="large"
                            :placeholder="$t('task.sprint_name_placeholder')" />
                    </a-form-model-item>
                    <a-form-model-item
                        ref="projects"
                        :label="$t('task.project')"
                        prop="projects">
                        <ProjectSelect
                            v-model="form.projects"
                            multiple
                            inputType="defaultInput"
                            :placeholder="$t('task.select_project')" />
                    </a-form-model-item>
                    <a-form-model-item
                        ref="duration"
                        :label="$t('task.duration')"
                        prop="duration">
                        <a-select 
                            v-model="form.duration" 
                            :getPopupContainer="getPopupContainer"
                            size="large">
                            <a-select-option :value="7">
                                {{ $t('task.sprint_week') }}
                            </a-select-option>
                            <a-select-option :value="14">
                                {{ $t('task.sprint_two_weeks') }}
                            </a-select-option>
                            <a-select-option :value="28">
                                {{ $t('task.sprint_month') }}
                            </a-select-option>
                        </a-select>
                    </a-form-model-item>
                    <a-form-model-item
                        ref="target"
                        :label="$t('task.sprint_goal')"
                        prop="target">
                        <a-input
                            v-model="form.target"
                            size="large"
                            :placeholder="$t('task.sprint_goal_placeholder')" />
                    </a-form-model-item>
                    <a-form-model-item
                        ref="expected_result"
                        :label="$t('task.expected_result')"
                        prop="expected_result">
                        <a-select 
                            v-model="form.expected_result" 
                            mode="tags" 
                            class="w-full"
                            size="large" 
                            :getPopupContainer="getPopupContainer"
                            :placeholder="$t('task.expected_result_placeholder')" 
                            :notFoundContent="$t('task.enter_multiple_values')">
                        </a-select>
                    </a-form-model-item>
                </a-form-model>
            </a-spin>
        </div>
        <template #footer>
            <a-button 
                type="primary" 
                size="large" 
                :loading="loading"
                block
                @click="formSubmit()">
                <template v-if="edit">
                    {{ $t('task.save') }}
                </template>
                <template v-else>
                    {{ $t('task.add_sprint') }}
                </template>
            </a-button>
        </template>
    </DrawerTemplate> 
</template>

<script>
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'
export default {
    components: {
        ProjectSelect: () => import('@/modules/DrawerSelect/ProjectSelect.vue'),
        HelpButton: () => import('@apps/Support/components/HelpButton.vue'),
        DrawerTemplate: () => import("@/components/DrawerTemplate.vue")
    },
    data(){
        return {
            edit: false,
            visible: false,
            sprintLoading: false,
            inject: false,
            back: false,
            form: {
                name: "",
                target: "",
                duration: null,
                expected_result: [],
                projects: []
            },
            rules: {
                name: [
                    { required: true, message: this.$t('task.field_require'), trigger: 'blur' },
                    { max: 255, message: this.$t('task.field_min_require'), trigger: 'blur' }
                ],
                duration: [
                    { required: true, message: this.$t('task.field_require'), trigger: 'blur' }
                ],
                projects: [
                    { required: true, message: this.$t('task.field_require'), trigger: 'blur' }
                ],
                target: [
                    { max: 255, message: this.$t('task.max_255_chars'), trigger: 'blur' }
                ]
            },
            loading: false
        }
    },
    computed: {
        isInject() {
            return this.inject ? `_inject` : ''
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        drawerWidth() {
            if(this.windowWidth > 1200)
                return 821
            else if(this.windowWidth <= 1200 && this.windowWidth > 821) {
                return '95%'
            } else {
                return '100%'
            }
        }
    },
    methods: {
        getPopupContainer() {
            return this.$refs.sprintFormWrapper
        },
        handleError(error) {
            console.log(error)
            if (error && typeof error === 'object') {
                const messages = []
                    
                for (const key in error) {
                    if (Array.isArray(error[key])) {
                        messages.push(...error[key])
                    }
                }
                    
                if (messages.length) {
                    this.$message.error(messages.join(' '))
                    return
                }
            }
            this.$message.error(this.$t('task.error'))
        },
        formSubmit() {
            this.$refs.sprintForm.validate(async valid => {
                if (valid) {
                    const queryData = {...this.form}
                    if(queryData.projects?.length)
                        queryData.projects = queryData.projects.map(item => item.id)
                    if(this.edit) {
                        try {
                            this.loading = true
                            const { data } = await this.$http.put(`/tasks/sprint/${queryData.id}/update/`, queryData)
                            if(data) {
                                this.$message.success(this.$t('task.sprint_updated'))
                                eventBus.$emit(`update_sprints_list${this.isInject}`)
                                this.visible = false
                            }
                        } catch(error) {
                            errorHandler({error})
                        } finally {
                            this.loading = false
                        }
                    } else {
                        try {
                            this.loading = true
                            const { data } = await this.$http.post('/tasks/sprint/create/', queryData)
                            if(data) {
                                this.$message.success(this.$t('task.sprint_created'))
                                eventBus.$emit(`update_sprints_list${this.isInject}`)
                                this.visible = false
                            }
                        } catch(error) {
                            errorHandler({error})
                        } finally {
                            this.loading = false
                        }
                    }
                } else {
                    return false;
                }
            })
        },
        afterVisibleChange(vis) {
            if(!vis) {
                this.edit = false
                this.inject = false
                if(this.back) {
                    const query = Object.assign({}, this.$route.query)
                    if(query.sprint && Number(query.sprint) !== this.form.id || !query.sprint) {
                        query.sprint = this.form.id
                        this.$router.push({query})
                    }
                    this.back = false
                }
                this.form = {
                    name: "",
                    target: "",
                    duration: null,
                    expected_result: [],
                    projects: []
                }
            }
        },
        async getSprint(sprint) {
            try {
                this.sprintLoading = true
                const { data } = await this.$http.get(`/tasks/sprint/${sprint.id}/`)
                if(data) {
                    this.form = {...data}
                }
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                this.sprintLoading = false
            }
        }
    },
    mounted() {
        eventBus.$on('add_sprint', injectParams => {
            if(injectParams && Object.keys(injectParams)?.length) {
                this.form = {
                    ...this.form,
                    ...injectParams
                }
                if(injectParams.inject)
                    this.inject = injectParams.inject
            }
            this.visible = true
        })
        eventBus.$on('edit_sprint', sprint => {
            this.edit = true
            this.visible = true
            if(sprint.inject)
                this.inject = sprint.inject
            if(sprint.back)
                this.back = sprint.back
            this.getSprint(sprint)
        })
    },
    beforeDestroy() {
        eventBus.$off('add_sprint')
        eventBus.$off('edit_sprint')
    }
}
</script>
