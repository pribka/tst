<template>
    <DrawerTemplate
        v-model="visible"
        :width="drawerWidth"
        destroyOnClose
        @afterVisibleChange="afterVisibleChange"
        @close="visible = false">
        <template #title>
            <div class="drawer_title">
                {{ edit ? $t('approvals.edit_request') : $t('approvals.add_new_request') }}
            </div>
        </template>
        <template #rightHeader>
            <HelpButton partCode="request-approvals" class="ml-2" />
        </template>
        <a-form-model ref="form" :model="form" :rules="rules">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-2 md:gap-3 mb-2 md:mb-3">
                <a-form-model-item :label="$t('approvals.request_type')" prop="request_type" class="mb-0 w-full">
                    <DSelect
                        v-model="form.request_type"
                        size="large"
                        apiUrl="/app_info/filtered_select_list/"
                        :oneSelect="edit ? false : true"
                        :firstSelected="edit ? false : true"
                        :placeholder="$t('sports.selectFromList')"
                        valueKey="code"
                        :disabled="checkDraft"
                        listObject="filteredSelectList"
                        :params="{ model: 'processes.WorkflowRequestTypeModel' }"
                        :default-active-first-option="false"
                        :filter-option="false"
                        :not-found-content="null"
                        @change="changeRequestType"
                        @oneChange="changeRequestType"/>
                </a-form-model-item>

                <a-form-model-item :label="$t('Organization')" prop="organization" class="mb-0 w-full">
                    <DSelect
                        v-model="form.organization"
                        size="large"
                        apiUrl="/contractor_permissions/organizations/"
                        class="w-full"
                        :oneSelect="edit ? false : true"
                        :listObject="false"
                        labelKey="name"
                        :disabled="checkDraft"
                        :params="{ permission_type: 'request_approvals_manager,request_approvals_admin' }"
                        :placeholder="$t('sports.selectFromList')"
                        :default-active-first-option="false"
                        :filter-option="false"
                        :not-found-content="null"
                        @change="changeOrganization"
                        @oneChange="changeOrganization"/>
                </a-form-model-item>
            </div>

            <a-spin :spinning="configLoading" class="w-full">
                <template v-if="formInfo">
                    <div v-if="formInfo.project || formInfo.amount_requested" class="grid grid-cols-1 md:grid-cols-2 gap-2 md:gap-3 mb-2 md:mb-3">
                        <a-form-model-item 
                            v-if="formInfo.project" 
                            :label="formInfo.project.label || $t('approvals.project')" 
                            :rules="formInfo.project.required ? {
                                required: true,
                                message: $t('field_required'),
                            } : []"
                            prop="project" 
                            class="mb-0 w-full">
                            <ProjectSelect
                                inputType="defaultInput"
                                :placeholder="formInfo.project.placeholder || ''"
                                v-model="form.project" />
                        </a-form-model-item>

                        <a-form-model-item
                            v-if="formInfo.amount_requested" 
                            :label="formInfo.amount_requested.label || $t('approvals.amount')"
                            prop="amount_requested"
                            :rules="formInfo.amount_requested.required ? {
                                required: true,
                                message: $t('field_required'),
                            } : []"
                            class="mb-0 w-full">
                            <a-input
                                size="large"
                                class="w-full"
                                :placeholder="formInfo.amount_requested.placeholder || $t('approvals.print_amount')"
                                v-model="form.amount_requested"
                                @input="onAmountInput"
                                @blur="onAmountBlur"/>
                        </a-form-model-item>
                    </div>

                    <a-form-model-item 
                        v-if="formInfo.description" 
                        :label="formInfo.description.label || $t('approvals.description')" 
                        :rules="formInfo.description.required ? {
                            required: true,
                            message: $t('field_required'),
                        } : []"
                        prop="description" 
                        class="mb-3">
                        <div class="textarea_wrapper">
                            <a-textarea
                                v-model="form.description"
                                class="textarea_input"
                                ref="descriptionTextArea"
                                :maxLength="descriptionMaxCount"
                                :placeholder="formInfo.description.placeholder || $t('approvals.print_description')"
                                @input="adjustHeight" />
                            <div class="description_length">
                                {{form.description.length}}/{{ descriptionMaxCount }}
                            </div>
                        </div>
                    </a-form-model-item>

                    <a-form-model-item 
                        v-if="formInfo.dead_line" 
                        :label="formInfo.dead_line.label || $t('approvals.dead_line')" 
                        :rules="formInfo.dead_line.required ? {
                            required: true,
                            message: $t('field_required'),
                        } : []"
                        prop="dead_line" 
                        class="mb-3 w-full">
                        <a-date-picker
                            size="large"
                            class="w-full"
                            :getCalendarContainer="getPopupContainer"
                            :inputReadOnly="false"
                            format="DD.MM.YYYY"
                            v-model="form.dead_line"/>
                    </a-form-model-item>

                    <div v-if="formInfo.event_date_start || formInfo.event_date_end" class="grid grid-cols-1 md:grid-cols-2 gap-2 md:gap-3 mb-5">
                        <a-form-model-item 
                            v-if="formInfo.event_date_start"
                            :label="formInfo.event_date_start.label || $t('approvals.date_start')" 
                            :rules="formInfo.event_date_start.required ? {
                                required: true,
                                message: $t('field_required'),
                            } : []"
                            prop="event_date_start" 
                            class="mb-0 w-full">
                            <a-date-picker
                                size="large"
                                class="w-full"
                                :getCalendarContainer="getPopupContainer"
                                :inputReadOnly="false"
                                format="DD.MM.YYYY"
                                v-model="form.event_date_start"/>
                        </a-form-model-item>

                        <a-form-model-item 
                            v-if="formInfo.event_date_end"
                            :label="formInfo.event_date_end.label || $t('approvals.date_end')" 
                            :rules="formInfo.event_date_end.required ? {
                                required: true,
                                message: $t('field_required'),
                            } : []"
                            prop="event_date_end" 
                            class="mb-0 w-full">
                            <a-date-picker
                                size="large"
                                class="w-full"
                                :getCalendarContainer="getPopupContainer"
                                :inputReadOnly="false"
                                format="DD.MM.YYYY"
                                v-model="form.event_date_end"/>
                        </a-form-model-item>
                    </div>

                    <a-form-model-item 
                        v-if="isMobile && formInfo && formInfo.money_under_report"
                        prop="event_date_end" 
                        class="mb-2 w-full">
                        <div class="flex items-center">
                            <a-switch v-model="form.money_under_report" />
                            <span class="pl-2 cursor-pointer" @click="form.money_under_report = !form.money_under_report">
                                {{ formInfo.money_under_report.label }}
                            </span>
                        </div>
                    </a-form-model-item>

                    <transition v-if="formInfo.route" name="slide-fade">
                        <a-spin v-if="form.organization" class="w-full" size="small" :spinning="routeLoading">
                            <div class="form_route rounded-lg bg-neutral-1 px-4 py-3 mb-3">
                                <h3 class="blue_color flex items-center">
                                    <i class="fi fi-rr-route mr-2" />
                                    {{ formInfo.route.label || $t('approvals.approvals_route') }}
                                </h3>

                                <div v-for="block in routeList" :key="block.id" class="selected_block rounded-lg">
                                    <div class="selected_block__title mb-2">
                                        {{ block.workflow_position.name }}
                                    </div>

                                    <a-form-model-item
                                        :prop="routeProp(block)"
                                        :rules="{
                                            type: 'array',
                                            required: true,
                                            min: 1,
                                            message: $t('approvals.user_required'),
                                            trigger: 'change'
                                        }"
                                        class="mb-0">
                                        <div class="user_list flex items-center flex-wrap gap-2">
                                            <div
                                                v-for="user in block.users"
                                                :key="user.id"
                                                class="flex items-center user_select select-none"
                                                :title="user.full_name"
                                                :class="[userCardClass(block, user), {
                                                    'cursor-pointer': !checkDraft,
                                                    'cursor-not-allowed user_select--disabled': checkDraft
                                                }]"
                                                @click="!checkDraft && toggleRouteUser(block, user)">
                                                <a-avatar
                                                    :key="user.id"
                                                    avResize
                                                    :size="18"
                                                    :src="user.avatar && user.avatar.path ? user.avatar.path : ''"
                                                    icon="user" />
                                                <span class="ml-2">{{ user.full_name }}</span>
                                                <span v-if="isAutoSelected(block, user)" class="ml-2 route_auto_flag">
                                                    <a-tag 
                                                        size="small" 
                                                        v-tippy
                                                        :content="$t('approvals.user_auto_selected')"
                                                        color="green">
                                                        {{ $t('approvals.auto') }}
                                                    </a-tag>
                                                </span>
                                            </div>
                                        </div>
                                    </a-form-model-item>
                                </div>
                            </div>
                        </a-spin>
                    </transition>

                    <a-form-model-item 
                        v-if="formInfo.attachments"
                        :label="formInfo.attachments.label || $t('approvals.attachments')" 
                        prop="attachments" 
                        class="mb-0">
                        <a-button
                            type="link"
                            size="small"
                            class="p-0"
                            @click="openFileModal">
                            + {{ formInfo.attachments.button_text || $t('approvals.select_file') }}
                        </a-button>

                        <div v-show="form.attachments.length">
                            <p>{{ formInfo.attachments.file_list || $t('approvals.attachments_selected') }}</p>
                            <FileAttach
                                ref="fileAttach"
                                :zIndex="1100"
                                class="task_files_list"
                                :attachmentFiles="form.attachments"
                                :maxMBSize="50"
                                createFounder
                                listType="picture"
                                :showDeviceUpload="true"/>
                        </div>
                    </a-form-model-item>
                </template>
            </a-spin>
        </a-form-model>

        <template #footer>
            <a-button v-if="editOrMobile" type="primary" size="large" style="height: 40px;" :block="isMobile" :loading="loading" :disabled="configLoading" @click="createHandler()">
                {{ $t('save') }}
            </a-button>
            <a-dropdown v-else :getPopupContainer="getPopupContainer">
                <a-button type="primary" size="large" style="height: 40px;" :block="isMobile" :loading="loading" :disabled="configLoading" @click="createHandler()">
                    {{ $t('save') }}
                </a-button>
                <a-menu slot="overlay">
                    <a-menu-item key="save_and_open" class="flex items-center" @click="createHandler(true)">
                        <i class="fi fi-rr-redo mr-2" />
                        {{ $t('approvals.save_and_open') }}
                    </a-menu-item>
                </a-menu>
            </a-dropdown>
            <div v-if="!isMobile && formInfo && formInfo.money_under_report" class="flex items-center ml-4">
                <a-switch v-model="form.money_under_report" />
                <span class="pl-2 cursor-pointer" @click="form.money_under_report = !form.money_under_report">
                    {{ formInfo.money_under_report.label }}
                </span>
            </div>
        </template>
    </DrawerTemplate>
</template>

<script>
import eventBus from "@/utils/eventBus"
import { errorHandler } from '@/utils/index.js'
import { formModel } from '../utils.js'
let timer;
export default {
    components: {
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue'),
        DSelect: () => import("@apps/DrawerSelect/Select.vue"),
        ProjectSelect: () => import("@apps/DrawerSelect/ProjectSelect.vue"),
        FileAttach: () => import("@apps/vue2Files/components/FileAttach"),
        HelpButton: () => import('@apps/Support/components/HelpButton.vue')
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        drawerWidth() {
            const baseWidth = 800
            const offset = 40
            return this.windowWidth > baseWidth + offset
                ? baseWidth
                : this.windowWidth
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        editOrMobile() {
            if(this.isMobile)
                return true
            return this.edit
        },
        checkDraft() {
            if(this.loading)
                return false
            if(!this.edit)
                return false
            return !this.isDraft
        }
    },
    data() {
        return {
            model: 'processes.WorkflowRequestModel',
            pageName: 'page_list_processes.WorkflowRequestModel',
            isDraft: false,
            descriptionMaxCount: 4000,
            routeLoading: true,
            formInfo: null,
            visible : false,
            isInit : null,
            fileKey: Date.now(),
            loading : null,
            edit : null,
            amount_requested: "",
            form: { ...formModel },
            routeSelectedByPosition: {},
            routeList: [],
            configLoading : null,
            autoSelectedMap: {},
            rules: {
                request_type: [
                    {
                        required: true,
                        message: this.$t("field_required"),
                        trigger: "blur"
                    }
                ],
                organization: [
                    {
                        required: true,
                        message: this.$t("field_required"),
                        trigger: "blur"
                    }
                ]
            }
        }
    },
    methods: {
        onAmountInput(e) {
            let v = String(e.target.value || '')

            v = v.replace(',', '.')
            v = v.replace(/[^\d.]/g, '')

            const parts = v.split('.')
            const intPart = parts[0]
            const decPart = parts[1] ? parts[1].slice(0, 2) : ''

            v = decPart !== undefined
                ? `${intPart}${parts.length > 1 ? '.' + decPart : ''}`
                : intPart

            this.form.amount_requested = this.formatThousands(v)
        },

        onAmountBlur() {
            let v = String(this.form.amount_requested || '')
                .replace(/\s/g, '')

            if (!v) {
                this.form.amount_requested = ''
                return
            }

            let [intPart, decPart = ''] = v.split('.')
            decPart = decPart.padEnd(2, '0').slice(0, 2)

            this.form.amount_requested = this.formatThousands(`${intPart}.${decPart}`)
        },

        formatThousands(value) {
            if (!value) return ''

            const parts = value.split('.')
            const intPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
            const decPart = parts[1] !== undefined ? `.${parts[1]}` : ''

            return `${intPart}${decPart}`
        },
        adjustHeight(event) {
            const textarea = event.target;
            textarea.style.height = 'auto'
            const maxHeight = window.innerHeight - 100
            textarea.style.height = `${Math.min(textarea.scrollHeight, maxHeight)}px`
        },
        async changeRequestType() {
            try {
                this.configLoading = true
                const { data } = await this.$http.get('/processes/workflow_requests/form_info/', {
                    params: {
                        request_type: this.form.request_type
                    }
                })
                if(data) {
                    this.formInfo = data
                    if(!this.isMobile && !this.isInit && !this.edit) {
                        this.$nextTick(() => {
                            if(this.$refs.descriptionTextArea)
                                this.$refs.descriptionTextArea.focus()
                        })
                    }
                    this.isInit = true

                    this.clearRouteDynamicFields()
                    this.getRequestRoute()
                }
            } catch(error) {
                errorHandler({error, show : null})
            } finally {
                this.configLoading = false
            }
        },
        routeProp(block) {
            return `route_${block.id}`
        },
        ensureRouteField(blockId) {
            const key = `route_${blockId}`
            if (!Array.isArray(this.form[key])) {
                this.$set(this.form, key, [])
            }
            return key
        },
        setRouteSelected(blockId, userIds) {
            const key = this.ensureRouteField(blockId)
            this.$set(this.form, key, Array.isArray(userIds) ? userIds : [])
            this.syncRoutePayload()
        },
        getRouteSelected(blockId) {
            const key = this.ensureRouteField(blockId)
            return this.form[key] || []
        },
        isSelected(block, user) {
            const selected = this.getRouteSelected(block.id)
            return selected.includes(user.id)
        },
        isAutoSelected(block, user) {
            const auto = this.autoSelectedMap?.[block.id]
            return auto === user.id
        },
        userCardClass(block, user) {
            return {
                is_selected: this.isSelected(block, user),
                is_auto_selected: this.isAutoSelected(block, user)
            }
        },
        normalizeAmount(value) {
            if (value === undefined || value === null || value === '') return ''

            const str = String(value).replace(/\s/g, '').replace(',', '.')
            if (!str) return ''

            const parts = str.split('.')
            const intPart = parts[0].replace(/\D/g, '') || '0'
            const decPart = (parts[1] || '').replace(/\D/g, '').slice(0, 2)

            const fixedDec = decPart.padEnd(2, '0')
            return this.formatThousands(`${intPart}.${fixedDec}`)
        },
        toggleRouteUser(block, user) {
            if (this.checkDraft) return
            if (!block?.id || !user?.id) return

            const selected = [...this.getRouteSelected(block.id)]
            const idx = selected.indexOf(user.id)

            if (idx !== -1) {
                selected.splice(idx, 1)
                if (this.autoSelectedMap?.[block.id] === user.id) {
                    this.$delete(this.autoSelectedMap, block.id)
                }
            } else {
                selected.push(user.id)
            }

            this.setRouteSelected(block.id, selected)

            this.$nextTick(() => {
                if (this.$refs.form) {
                    this.$refs.form.validateField(this.routeProp(block))
                }
            })
        },
        buildRouteFromBackend(routeList) {
            this.routeList = Array.isArray(routeList) ? routeList : []
            this.autoSelectedMap = {}

            this.routeList.forEach(block => {
                this.ensureRouteField(block.id)

                const users = Array.isArray(block.users) ? block.users : []
                const position = block?.workflow_position?.code || ''

                const preselected = this.routeSelectedByPosition?.[position]
                if (Array.isArray(preselected) && preselected.length) {
                    const allowedIds = users.map(u => u.id)
                    const selectedIds = preselected.filter(id => allowedIds.includes(id))
                    this.setRouteSelected(block.id, selectedIds)
                    return
                }

                if (!this.edit && users.length === 1) {
                    const onlyUserId = users[0].id
                    this.$set(this.autoSelectedMap, block.id, onlyUserId)
                    this.setRouteSelected(block.id, [onlyUserId])
                } else {
                    this.setRouteSelected(block.id, this.getRouteSelected(block.id))
                }
            })

            this.syncRoutePayload()
        },
        syncRoutePayload() {
            const payload = (this.routeList || []).map(block => {
                const users = this.getRouteSelected(block.id)
                const position = block?.workflow_position?.code || ''

                return {
                    position,
                    users
                }
            })

            this.form.route = payload
        },
        clearRouteDynamicFields() {
            const keys = Object.keys(this.form || {})
            keys.forEach(k => {
                if (k.startsWith('route_')) {
                    this.$delete(this.form, k)
                }
            })
            this.routeList = []
            this.autoSelectedMap = {}
            this.form.route = []
        },
        changeOrganization() {
            this.form.route = []
            this.clearRouteDynamicFields()
            this.getRequestRoute()
        },
        getRequestRoute() {
            clearTimeout(timer)

            if (this.form.organization && this.form.request_type) {
                timer = setTimeout(async () => {
                    try {
                        this.routeLoading = true
                        const { data } = await this.$http.get('/processes/workflow_requests/route_template/', {
                            params: {
                                request_type: this.form.request_type,
                                contractor: this.form.organization
                            }
                        })
                        if (data) {
                            this.buildRouteFromBackend(data)
                        }
                    } catch (error) {
                        errorHandler({ error, show : null })
                    } finally {
                        this.routeLoading = false
                    }
                }, 500)
            } else {
                this.routeLoading = false
            }
        },
        openFileModal() {
            this.$nextTick(() => {
                this.$refs.fileAttach.openFileModal()
            })
        },
        createHandler(open = false) {
            this.loading = true
            this.syncRoutePayload()

            this.$refs.form.validate(async (v) => {
                if (v) {
                    try {
                        this.syncRoutePayload()
                        const queryData = JSON.parse(JSON.stringify(this.form))

                        if(queryData.attachments?.length)
                            queryData.attachments = queryData.attachments.map(atch => atch.id)
                        if(queryData.project?.id)
                            queryData.project = queryData.project.id
                        if (queryData.amount_requested) {
                            queryData.amount_requested = Number(
                                queryData.amount_requested
                                    .replace(/\s/g, '')
                                    .replace(',', '.')
                            )
                        }

                        if(this.edit) {
                            if(!this.isDraft) {
                                delete queryData.organization
                                delete queryData.request_type
                                delete queryData.route
                                delete queryData.routes
                            }

                            const { data } = await this.$http.put(`/processes/workflow_requests/${queryData.id}/`, queryData)
                            if(data) {
                                this.$message.success(this.$t('approvals.request_edited'))
                                //eventBus.$emit(`update_filter_${this.model}_${this.pageName}`);
                                //eventBus.$emit(`update_request_approvals_${queryData.id}`)
                                this.visible = false
                            }
                        } else {
                            const { data } = await this.$http.post('/processes/workflow_requests/', queryData)
                            if(data) {
                                this.$message.success(this.$t('approvals.request_created'))
                                eventBus.$emit(`update_filter_${this.model}_${this.pageName}`);
                                this.visible = false
                                if(open) {
                                    const query = JSON.parse(JSON.stringify(this.$route.query))
                                    query.approvals = data.id
                                    this.$router.push({query})
                                }
                            }
                        }
                    } catch (error) {
                        errorHandler({ error })
                    } finally {
                        this.loading = false
                    }
                } else {
                    this.loading = false
                    this.$message.warning(this.$t("project.fill_all_fields"))
                }
            })
        },
        getPopupContainer(trigger) {
            return trigger.parentNode
        },
        afterVisibleChange(vis) {
            if (vis) {
                
            } else {
                this.closeDrawer()
            }
        },
        closeDrawer() {
            clearTimeout(timer)
            this.routeLoading = true
            this.isDraft = false
            this.edit = false
            this.isInit = false
            this.routeSelectedByPosition = {}
            this.form = JSON.parse(JSON.stringify(formModel))
            this.form.attachments = []
            this.form.amount_requested = ""
            this.clearRouteDynamicFields()
        },
        async getDetail(record) {
            try {
                const { data } = await this.$http.get(`/processes/workflow_requests/${record.id}/`)
                if(data) {
                    const formData = data

                    if(formData.status?.code === 'draft')
                        this.isDraft = true
                    if(formData.dead_line)
                        formData.dead_line = this.$moment(formData.dead_line)

                    if(formData.event_date_start)
                        formData.event_date_start = this.$moment(formData.event_date_start)

                    if(formData.event_date_end)
                        formData.event_date_end = this.$moment(formData.event_date_end)

                    if(formData.request_type)
                        formData.request_type = formData.request_type.code

                    if(formData.organization)
                        formData.organization = formData.organization.id

                    const selectedByPosition = {}
                    const routes = Array.isArray(formData.routes) ? formData.routes : []
                    routes.forEach(r => {
                        const position = r?.workflow_position?.code
                        if (!position) return
                        const through = Array.isArray(r.request_route_user_through) ? r.request_route_user_through : []
                        const ids = through.map(t => t?.user?.id).filter(Boolean)
                        selectedByPosition[position] = ids
                    })
                    this.routeSelectedByPosition = selectedByPosition

                    delete formData.date_start
                    delete formData.date_end

                    if(formData.amount_requested)
                        formData.amount_requested = this.normalizeAmount(formData.amount_requested)

                    this.form = { ...formData }

                    await this.changeRequestType()
                    this.clearRouteDynamicFields()
                    this.getRequestRoute()
                }
            } catch(error) {
                errorHandler({error})
            }
        }
    },
    mounted() {
        eventBus.$on('add_request_approvals', () => {
            this.visible = true
        })
        eventBus.$on('edit_request_approvals', record => {
            this.edit = true
            this.visible = true
            this.getDetail(record)
        })
    },
    beforeDestroy() {
        eventBus.$off('add_request_approvals')
        eventBus.$off('edit_request_approvals')
    }
}
</script>

<style lang="scss" scoped>
.slide-fade-enter-active {
    transition: all 0.3s ease;
}
.slide-fade-leave-active {
    transition: all 0.3s cubic-bezier(1, 0.5, 0.8, 1);
}
.slide-fade-enter,
.slide-fade-leave-to {
    transform: translateY(-10px);
    opacity: 0;
}
.textarea_wrapper{
    position: relative;
    .description_length{
        position: absolute;
        bottom: 10px;
        right: 10px;
        z-index: 5;
        color: #888;
        font-size: 13px;
        line-height: 13px;
    }
    .textarea_input{
        margin-bottom: 0px!important;
        padding-bottom: 25px;
    }
}
.user_select{
    border: 1px solid var(--borderColor);
    padding: 5px 10px;
    border-radius: 20px;
    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    min-height: 33px;
    &.user_select--disabled{
        opacity: 0.6;
        background: #f5f5f5;
    }
    &.is_selected{
        background: #e8ecfa;
        border-color: var(--borderColor);
        color: var(--blue);
    }
    &::v-deep{
        .ant-tag{
            line-height: 20px;
            padding: 0 8px;
            border-radius: 30px;
            font-size: 12px;
            &.ant-tag-green{
                color: rgb(22 163 74 / 1);
                background: rgb(240 253 244 / 1);
            }
        }
    }
}
.selected_block{
    background: #fff;
    padding: 10px;
    &:not(:last-child){
        margin-bottom: 10px;
    }
    &::v-deep{
        .ant-form-explain{
            padding-top: 5px;
        }
        .ant-form-item-control{
            line-height: 20px;
        }
    }
}
.form_route{
    h3{
        font-size: 17px;
        line-height: 22px;
        margin-bottom: 15px;
    }
}
</style>
