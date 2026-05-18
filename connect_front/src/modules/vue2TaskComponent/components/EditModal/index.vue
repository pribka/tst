<template>
    <a-modal
        :width="650"
        @afterVisibleChange="afterVisibleChange"
        destroyOnClose
        :visible="visible"
        @cancel="visible = false">
        <template #title>
            <div v-if="formInfo" class="w-full flex items-center justify-between">
                <div>{{ modalTitle }}</div>
                <div class="flex items-center ml-2 gap-1">
                    <transition name="slide-fade">
                        <a-tag
                            v-if="isDraft && !disableDraft"
                            closable
                            @close="clearDraftForm"
                            class="draft_task mr-0"
                            color="purple">
                            {{ $t("task.draft") }}
                        </a-tag>
                    </transition>
                    <HelpButton partCode="tasks" />
                </div>
            </div>
            <a-skeleton v-else active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 40%;" /> 
        </template>
        <template v-if="formInfo">
            <a-form-model
                ref="taskForm"
                :model="form"
                :label-col="{ span: 6, style: { textAlign: 'left' } }"
                :wrapper-col="{ span: 18 }"
                class="mini_form"
                :rules="rules">
                <a-form-model-item 
                    v-if="formInfo.name" 
                    ref="name" 
                    prop="name" 
                    :wrapper-col="{ span: 24 }"
                    class="mb-1 name_field" 
                    :rules="formInfo.name.rules">
                    <a-input 
                        v-model="form.name"
                        ref="nameInput"
                        inputType="ghost"
                        :placeholder="formInfo.name && formInfo.name.rules ? `${$t('task.form_name')} *` : $t('task.form_name')" 
                        size="large"
                        @pressEnter="onSubmit()" />
                </a-form-model-item>
                <a-form-model-item
                    v-if="formInfo.description"
                    :wrapper-col="{ span: 24 }"
                    :rules="formInfo.description.rules"
                    prop="description">
                    <div class="w-full description_editor bg-neutral-1 z-10 relative px-4 py-3 rounded-xl">
                        <component
                            v-if="editorGate"
                            :is="ckEditor"
                            :taskId="form.id || null"
                            :placeholder="$t('task.form_description')"
                            :key="visible"
                            v-model="form.description"/>
                    </div>
                </a-form-model-item>
                <a-form-model-item 
                    v-if="formInfo.task_type" 
                    ref="task_type" 
                    :label="$t('task.task_type')"
                    class="flex items-center h-9"
                    prop="task_type" 
                    :rules="formInfo.task_type.rules">
                    <div class="flex items-center" :title="$t('Type')">
                        <a-select
                            v-model="form.task_type"
                            inputType="ghost"
                            :getPopupContainer="getCalendarContainer"
                            :placeholder="$t('Type')"
                            defaultValue="task"
                            @change="changeTaskType">
                            <a-select-option
                                v-for="item in taskTypeOptions"
                                :key="item.value"
                                :value="item.value">
                                {{ item.label }}
                            </a-select-option>
                        </a-select>
                    </div>
                </a-form-model-item>
                <a-form-model-item ref="project" :label="formInfo.project.title" prop="project" :rules="formInfo.project.rules || null" class="flex items-center h-9">
                    <ProjectSelect 
                        v-if="formInfo.project" 
                        ref="projectSelect"
                        inputType="input"
                        :placeholder="$t('task.select_project')"
                        v-model="form.project"
                        @change="projectChange" />
                </a-form-model-item>
                <a-form-model-item
                    v-if="formInfo.contract || resolvedProjectId"
                    ref="contract"
                    :label="contractPlaceholder"
                    prop="contract"
                    class="modal_contract_select flex items-center h-9"
                    :rules="(formInfo.contract && formInfo.contract.rules) || null">
                    <ContractSelect
                        :key="`task_contract_select_${contractSelectKey}_${resolvedProjectId || 'empty'}`"
                        :apiUrl="getContractSelectApiUrl()"
                        :params="getContractSelectParams()"
                        :value="form.contract"
                        :disabled="!resolvedProjectId"
                        listObject="filteredSelectList"
                        inputType="ghost"
                        size="default"
                        :title="contractPlaceholder"
                        valueKey="id"
                        labelKey="string_view"
                        searchKey="search"
                        iconClass="fi-rr-file-contract"
                        :showIcon="false"
                        :showSearch="true"
                        :showRecent="false"
                        :showClear="true"
                        :showArrow="true"
                        :initList="Boolean(resolvedProjectId)"
                        :useSearchApi="false"
                        :placeholder="contractPlaceholder"
                        @change="onContractChange" />
                </a-form-model-item>
                <a-form-model-item
                    v-if="form.contract || customerCardOptions.length"
                    ref="customer_card"
                    :label="$t('task.client')"
                    prop="customer_card"
                    class="flex items-center h-9">
                    <DSelect
                        :key="`task_customer_card_select_${customerCardSelectKey}`"
                        v-model="form.customer_card"
                        class="w-full"
                        inputType="ghost"
                        size="large"
                        :initList="false"
                        :showSearch="false"
                        :useSearchApi="false"
                        :allowClear="true"
                        :disabled="!form.contract"
                        :initOptionList="customerCardOptions"
                        valueKey="id"
                        labelKey="name"
                        :placeholder="$t('task.client')"
                        @change="onCustomerCardChange" />
                </a-form-model-item>
                <a-form-model-item
                    v-if="formInfo.result && form.task_type !== 'milestone' && form.task_type !== 'stage'"
                    :label="formInfo.result.title"
                    :rules="formInfo.result.rules"
                    class="flex items-center h-9"
                    prop="result">
                    <a-input
                        v-model="form.result"
                        size="small"
                        inputType="ghost"
                        :placeholder="formInfo.result.title" /> 
                </a-form-model-item>
                <a-form-model-item 
                    v-if="formInfo.operator" 
                    ref="operator" 
                    :label="$t('task.operator')" 
                    class="flex items-center h-9"
                    prop="operator" 
                    :rules="formInfo.operator.rules">
                    <UserDrawer
                        v-model="form.operator"
                        :id="defaultUserSelectId"
                        class="w-full"
                        :disabled="form.is_auction"
                        inputType="ghost"
                        :inputPlaceholder="formInfo.operator.title"
                        :filters="
                            formInfo.operator.filters
                                ? formInfo.operator.filters
                                : null
                        "
                        :oldSelected="checkOldSelect(formInfo.operator)"
                        :title="
                            formInfo.operator.drawerTitle ||
                                $t('task.select_performer')
                        "/>
                </a-form-model-item>
                <a-form-model-item
                    v-if="formInfo.date_start_plan && form.task_type !== 'milestone'"
                    :rules="rules.date_start_plan"
                    :label="formInfo.date_start_plan.title"
                    class="flex items-center h-9 date_select"
                    prop="date_start_plan">
                    <DatePicker
                        v-model="form.date_start_plan"
                        allowClear
                        inputType="ghost"
                        showToday
                        iconPosition="left"
                        :disabledAfter="disabledStartDateAfter"
                        :disabledBefore="disabledStartDateBefore"
                        :getCalendarContainer="getCalendarContainer"
                        :show-time="{ format: 'HH:mm' }"
                        @change="changeStartDate()" />
                </a-form-model-item>
                <a-form-model-item ref="dead_line" :label="formInfo.dead_line.title" class="flex items-center h-9 date_select" prop="dead_line" :rules="formInfo.dead_line.rules || null">
                    <div class="flex items-center justify-between">
                        <DatePicker
                            v-model="form.dead_line"
                            allowClear
                            ref="deadLinePicker"
                            renderExtraFooter
                            inputType="ghost"
                            iconPosition="left"
                            :showToday="false"
                            :getCalendarContainer="getCalendarContainer"
                            :disabledAfter="disabledDeadlineAfter"
                            :disabledBefore="disabledDeadlineBefore"
                            :startTime="false"
                            :show-time="{ format: 'HH:mm' }"
                            @change="changeDeadline()" />
                        <div v-if="form.task_type === 'task'" class="priority_picker flex items-center gap-2">
                            <div 
                                v-for="(item, index) in priority" 
                                :key="index" 
                                v-tippy
                                :content="item.name"
                                :class="item.value === form.priority && 'active'"
                                class="priority_picker__item cursor-pointer w-8 h-8 flex items-center justify-center text-base" 
                                :style="`color: ${item.color};border-radius: 8px;`"
                                @click="form.priority = item.value">
                                <i class="fi" :class="item.icon" />
                            </div>
                        </div> 
                    </div>
                </a-form-model-item>
                <div class="modal_divider"></div>
                <div class="flex items-center gap-2 flex-wrap form_footer_btn">
                    <a-button
                        v-if="formInfo.files"
                        type="flat"
                        flaticon
                        icon="fi-rr-clip"
                        @click="openFileModal">
                        {{ $t("task.file") }}
                    </a-button>
                    <div class="btn_divider" />
                    <UserDrawer
                        v-if="form.task_type === 'task'"
                        :id="defaultUserSelectId"
                        v-model="form.cooperators"
                        :metadata="{ key: 'cooperators', value: form.metadata }"
                        :changeMetadata="changeMetadata"
                        multiple
                        buttonNew
                        :buttonText="$t('task.cooperators')"
                        buttonIcon="fi-rr-user-add"
                        :title="$t('task.select_cooperators')"/>
                    <UserDrawer
                        v-if="form.task_type === 'task'"
                        :id="defaultUserSelectId"
                        v-model="form.visors"
                        :metadata="{ key: 'visors', value: form.metadata }"
                        :changeMetadata="changeMetadata"
                        multiple
                        buttonNew
                        :buttonText="$t('task.observers')"
                        buttonIcon="fi-rr-user-add"
                        :title="
                            formInfo.visors.drawerTitle ||
                                $t('task.select_observers')
                        "/>
                    <a-button 
                        v-if="form.parent" 
                        :title="$t('task.main_task')"
                        type="flat" 
                        class="flex items-center"
                        @click="form.parent = null">
                        <div class="truncate" style="max-width: 200px;">{{ form.parent.name }}</div>
                        <i class="fi fi-rr-cross-small ml-2" />
                    </a-button>
                    <a-button 
                        v-if="!moreFieldsShow"
                        type="flat" 
                        :title="$t('task.show_more')"
                        icon="fi-rr-plus-small" 
                        flaticon
                        @click="moreFieldsShow = true" />
                    <template v-if="moreFieldsShow">
                        <UserDrawer
                            v-if="formInfo.owner"
                            :id="defaultUserSelectId"
                            v-model="form.owner"
                            buttonNew
                            :buttonText="$t('task.owner')"
                            buttonIcon="fi-rr-user-add"
                            :title="
                                formInfo.owner.drawerTitle ||
                                    $t('task.select_author')
                            "/>
                        <component 
                            v-if="formInfo.organization"
                            :is="orgSelectComponent"
                            :opnUserSetting="opnUserSetting"
                            v-model="form.organization" />
                        <component 
                            v-if="formInfo.workgroup"
                            :is="groupSelectComponent"
                            v-model="form.workgroup"
                            @change="groupChange" /> 
                        <a-checkbox v-model="form.is_need_to_make_event">
                            {{ $t("task.make_event") }}
                        </a-checkbox>
                    </template>
                </div>
                <div v-if="formInfo.files" v-show="form.attachments.length" class="mt-3">
                    <div class="mb-2" style="color: #888888;">{{ $t("Attached files") }}</div>
                    <FileAttach
                        ref="fileAttach"
                        :zIndex="1100"
                        :attachmentFiles="form.attachments"
                        :maxMBSize="50"
                        createFounder
                        listType="picture"
                        :showDeviceUpload="true"/>
                </div>
            </a-form-model>
        </template>
        <template v-else>
            <div class="mb-4">
                <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 70%;" /> 
            </div>
            <div class="mb-6">
                <div class="w-full description_editor bg-neutral-1 z-10 relative px-4 py-3 rounded-xl" style="min-height: 108px;">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 80%;" class="mb-3" /> 
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 100%;" /> 
                </div>
            </div>
            <div class="flex items-center w-full gap-4 mb-6">
                <div style="width: 30%;">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 100%;" /> 
                </div>
                <div style="width: 70%;">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 60%;" /> 
                </div>
            </div>
            <div class="flex items-center w-full gap-4 mb-6">
                <div style="width: 32%;">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 100%;" /> 
                </div>
                <div style="width: 75%;">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 60%;" /> 
                </div>
            </div>
            <div class="flex items-center w-full gap-4 mb-6">
                <div style="width: 30%;">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 70%;" /> 
                </div>
                <div style="width: 70%;">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 70%;" /> 
                </div>
            </div>
            <div class="flex items-center w-full gap-4 mb-6">
                <div style="width: 30%;">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 70%;" /> 
                </div>
                <div style="width: 40%;">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 60%;" /> 
                </div>
            </div>
            <div class="flex items-center w-full gap-4 mb-6">
                <div style="width: 30%;">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 70%;" /> 
                </div>
                <div style="width: 40%;">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 80%;" /> 
                </div>
            </div>
            <div class="flex items-center w-full gap-4 mb-6">
                <div style="width: 30%;">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 100%;" /> 
                </div>
                <div style="width: 70%;">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 100%;" /> 
                </div>
            </div>
            <div class="modal_divider" />
            <div class="flex items-center gap-2 flex-wrap form_footer_btn mb-2">
                <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 100px;" /> 
                <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 100px;" /> 
                <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 100px;" /> 
                <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 100px;" /> 
            </div>
        </template>
        <template #footer>
            <div v-if="formInfo" ref="modal_footer" class="flex items-center justify-between w-full">
                <div class="flex gap-1 items-center">
                    <a-dropdown :getPopupContainer="() => $refs.modal_footer">
                        <a-button type="primary" :disabled="!formInfo" size="large" class="flex items-center" :loading="loading" @click="onSubmit()">
                            <template v-if="formInfo">
                                {{ saveBtnText }}
                                <i class="fi fi-rr-angle-small-down ml-2" />
                            </template>
                            <a-spin v-else size="small" />
                        </a-button>
                        <a-menu slot="overlay">
                            <a-menu-item class="flex items-center" @click="submitAndCreate()">
                                <i class="fi fi-rr-add mr-2" />
                                {{ $t("task.create_and_create") }}
                            </a-menu-item>
                            <a-menu-item class="flex items-center" @click="submitAndOpen()">
                                <i class="fi fi-rr-redo mr-2" />
                                {{ $t("task.create_and_open") }}
                            </a-menu-item>
                            <a-menu-item class="flex items-center" @click="submitAndPinFocus()">
                                <i class="fi fi-rr-flag-alt mr-2" />
                                {{ $t("task.create_and_pin_focus") }}
                            </a-menu-item>
                        </a-menu>
                    </a-dropdown>
                    <a-button type="ui_ghost" ghost size="large" :disabled="!formInfo" @click="visible = false">
                        {{ $t("task.close") }}
                    </a-button>
                </div>
                <a-button type="ui_ghost" ghost size="large" :disabled="!formInfo" @click="openFullForm()">
                    {{ $t('open_full_form') }}
                </a-button>
            </div>
            <div v-else class="flex items-center justify-between w-full">
                <div class="flex gap-1 items-center">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 150px;" /> 
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 100px;" /> 
                </div>
                <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 200px;" /> 
            </div>
        </template>
        <ReplaceVisorsModal
            ref="replaceVisorsModalRef"
            v-model="form" />
    </a-modal>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { formModel, priorityList, checkDate, checkDateDeadLine } from '../../utils/index.js'
import { mapState } from 'vuex'
import { isEqual } from "lodash"
import taskEdit from '../../mixins/taskEdit.js'
import { errorHandler } from '@/utils/index.js'
let formWatch;
export default {
    mixins: [ taskEdit ],
    components: {
        UserDrawer: () => import("@apps/DrawerSelect/index.vue"),
        FileAttach: () => import("@apps/vue2Files/components/FileAttach"),
        ProjectSelect: () => import("@apps/DrawerSelect/ProjectSelect.vue"),
        ContractSelect: () => import("@apps/DrawerSelect/ContractSelect.vue"),
        DSelect: () => import("@apps/DrawerSelect/Select.vue"),
        //OrgSelect: () => import("@apps/DrawerSelect/OrgSelect.vue"),
        //GroupSelect: () => import("@apps/DrawerSelect/GroupSelect.vue"),
        DatePicker: () => import("../EditDrawer/DatePick"),
        ReplaceVisorsModal: () => import('../ReplaceVisorsModal.vue'),
        HelpButton: () => import('@apps/Support/components/HelpButton.vue')
    },
    computed: {
        ...mapState({
            pageName: (state) => state.task.pageName,
            windowWidth: (state) => state.windowWidth,
            user: (state) => state.user.user,
            formDefault: (state) => state.task.formDefault,
            taskList: (state) => state.task.taskList,
            task: (state) => state.task.task,
            mainKey: (state) => state.task.mainKey,
            formInfoData: (state) => state.task.formInfo,
            taskDrawerZIndex: (state) => state.task.taskDrawerZIndex,
            taskPointsList: (state) => state.task.taskPointsList,
            mapConfig: (state) => state.task.mapConfig,
            leadSources: (state) => state.task.leadSources,
            leadSourcesLoader: (state) => state.task.leadSourcesLoader,
            hardZIndex: (state) => state.task.hardZIndex,
        }),
        showTimeOptions() {
            const options = {}
            const defaultTime = '18:00:00'
            options.defaultValue = this.$moment(defaultTime, 'HH:mm:ss')
            return options
        },
        orgSelectComponent() {
            if(this.moreFieldsShow)
                return () => import("@apps/DrawerSelect/OrgSelect.vue")
            return null
        },
        groupSelectComponent() {
            if(this.moreFieldsShow)
                return () => import("@apps/DrawerSelect/GroupSelect.vue")
            return null
        },
        ckEditor() {
            if (this.visible) return () => import("@apps/CKEditor");
            else return null;
        },
        deadline() {
            return this.form.dead_line 
        },
        taskType() {
            return this.$store.state.task.taskType;
        },
        disabledStartDateAfter() {
            return this.deadline || this.deadlineLimit
        },
        disabledStartDateBefore() {
            return this.startDateLimit
        },
        disabledDeadlineAfter() {
            return this.deadlineLimit
        },
        disabledDeadlineBefore() {
            return this.startDate || this.startDateLimit
        },
        startDate() {
            return this.form.date_start_plan 
        },
        startDateLimit() {
            if (this.parentTask?.date_start_plan)
                return this.parentTask.date_start_plan
            /*if (this.form?.project?.date_start_plan && this.form?.project?.control_dates) {
                return this.form.project.date_start_plan
            }*/
            return null
        },
        deadlineLimit() {
            if (this.parentTask?.dead_line)
                return this.parentTask.dead_line
            /*if (this.form?.project?.dead_line && this.form?.project?.control_dates) {
                return this.form.project.dead_line
            }*/
            return null
        },
        resolvedProjectId() {
            if (!this.form?.project) return null
            return typeof this.form.project === 'object'
                ? this.form.project.id || null
                : this.form.project
        },
        contractPlaceholder() {
            return (this.formInfo && this.formInfo.contract && this.formInfo.contract.title) || 'Контракт'
        },
        saveBtnText() {
            if (!this.formInfo) return ''

            const prefix = 'add'
            const map = {
                milestone: `task.${prefix}_milestone`,
                stage: `task.${prefix}_stage`,
                default: `task.${prefix}_task`
            }
            return this.$t(map[this.form.task_type] || map.default)
        },
        createdMessage() {
            if (!this.formInfo) return this.$t('task.task_created')

            const map = {
                milestone: 'task.milestone_created',
                stage: 'task.stage_created',
                default: 'task.task_created'
            }
            return this.$t(map[this.form.task_type] || map.default)
        },
        openTaskText() {
            if (!this.formInfo) return this.$t('task.open_task')

            const map = {
                milestone: 'task.open_milestone',
                stage: 'task.open_stage',
                default: 'task.open_task'
            }
            return this.$t(map[this.form.task_type] || map.default)
        },
        parentTask() {
            return this.form?.parent || null
        },
        rules() {
            if(this.form.task_type !== 'task') {
                if(this.form.task_type === 'stage') {
                    return {
                        dead_line: [
                            { required: true, message: this.$t('field_required'), trigger: 'blur' },
                        ],
                        date_start_plan: [
                            { required: true, message: this.$t('field_required'), trigger: 'blur' },
                        ]
                    }
                } else {
                    return {
                        dead_line: [
                            { required: true, message: this.$t('field_required'), trigger: 'blur' },
                        ]
                    }
                }
            }
            return {}
        },
        modalTitle() {
            if (!this.formInfo) return ''

            if(this.copy)
                return this.$t('task.copy_task_label')
            if(this.form.parent?.id)
                return this.$t('task.add_subtask')

            if (this.isHelpdesk)
                return this.$t('task.add_appeal')

            const prefix = 'add'
            const map = {
                milestone: `task.${prefix}_milestone`,
                stage: `task.${prefix}_stage`,
                default: `task.${prefix}_task`
            }
            return this.$t(map[this.form.task_type] || map.default)
        }
    },
    data() {
        return {
            priority: priorityList,
            openFullCheck: false,
            disableDraft: false,
            visible: false,
            fileList: [],
            loading: false,
            datesDonMatch: false,
            form: {...formModel},
            open: false,
            subtask: false,
            editorGate: false,
            changeParentDisabled: false,
            formInject: null,
            isDraft: false,
            defaultUserSelectId: 'empty_task',
            contractSelectKey: Date.now(),
            customerCardSelectKey: Date.now(),
            customerCardOptions: [],
            formLoading: false,
            formInfo: null,
            moreCreate: false,
            formCopy: false,
            pinFocus: false,
            moreFieldsShow: false,
            taskTypeOptions: [
                { value: 'stage', label: this.$t('Stage') },
                { value: 'task', label: this.$t('Task') },
                { value: 'milestone', label: this.$t('Milestone') },
            ],
            initPhase: false
        }
    },
    methods: {
        dateConfirm() {
            this.$confirm({
                title: this.$t('task.dates_don_match'),
                cancelText: this.$t('no'),
                okText: this.$t('yes'),
                onOk: async () => {
                    await this.submitTask();
                }
            })
        },
        updateDatesMismatch() {
            const mk = v => {
                if (!v) return null
                let m

                if (this.$moment.isMoment && this.$moment.isMoment(v))
                    m = v.clone()
                else if (v instanceof Date)
                    m = this.$moment(v)
                else if (typeof v === 'string') {
                    const raw = v.trim()
                    const formats = [
                        this.$moment.ISO_8601,
                        'DD.MM.YYYY HH:mm:ss',
                        'DD.MM.YYYY HH:mm',
                        'DD.MM.YYYY',
                        'YYYY-MM-DD HH:mm:ss',
                        'YYYY-MM-DD HH:mm',
                        'YYYY-MM-DD'
                    ]

                    for (const fmt of formats) {
                        m = fmt === this.$moment.ISO_8601
                            ? this.$moment.parseZone(raw, fmt, true)
                            : this.$moment(raw, fmt, true)
                        if (m.isValid()) break
                    }
                } else
                    m = this.$moment(v)

                if (!m.isValid()) return null
                return m.startOf('day')
            }

            const taskStart = this.form?.date_start_plan
            const taskEnd = this.form?.dead_line
            const projectStart = this.form?.project?.date_start_plan
            const projectEnd = this.form?.project?.dead_line

            if (!taskStart && !taskEnd) {
                this.datesDonMatch = false
                return
            }

            if (!projectStart && !projectEnd) {
                this.datesDonMatch = false
                return
            }

            const tStart = mk(taskStart)
            const tEnd = mk(taskEnd)
            const pStart = mk(projectStart)
            const pEnd = mk(projectEnd)

            let mismatch = false

            const tStartMs = tStart ? tStart.valueOf() : null
            const tEndMs = tEnd ? tEnd.valueOf() : null
            const pStartMs = pStart ? pStart.valueOf() : null
            const pEndMs = pEnd ? pEnd.valueOf() : null

            if (pStartMs !== null && pEndMs !== null) {
                if (tStartMs !== null && tStartMs < pStartMs) mismatch = true
                if (tEndMs !== null && tEndMs > pEndMs) mismatch = true
            } else if (pStartMs !== null && pEndMs === null) {
                if (tStartMs !== null && tStartMs < pStartMs) mismatch = true
            } else if (pStartMs === null && pEndMs !== null) {
                if (tEndMs !== null && tEndMs > pEndMs) mismatch = true
            }

            this.datesDonMatch = Boolean(mismatch)
        },
        changeDeadline() {
            this.updateDatesMismatch();
        },
        changeStartDate() {
            this.updateDatesMismatch();
        },
        opnUserSetting() {
            this.visible = false
            this.clearDraftForm()
            const query = JSON.parse(JSON.stringify(this.$route.query))
            query.my_profile = 'open'
            this.$router.push({query})
        },
        startOpenChange(val) {
            if(!val && this.form.date_start_plan && this.$refs.deadLinePicker) {
                this.$refs.deadLinePicker.openPicker()
            }
        },
        changeTaskType() {
            if(this.form.task_type !== 'task') {
                this.form.priority = 2
                this.form.cooperators = []
                this.form.visors = []
            }
            this.$nextTick(() => {
                const forms = [this.$refs.taskForm].filter(Boolean)
                forms.forEach(f => {
                    if (typeof f.clearValidate === 'function') {
                        f.clearValidate()
                    } else if (typeof f.resetFields === 'function') {
                        f.resetFields()
                    }
                })
            })
        },  
        getContractSelectApiUrl() {
            return '/customer_contracts/analytics_keys/by_project/'
        },
        getContractSelectParams() {
            if (!this.resolvedProjectId) return {}
            return { project: this.resolvedProjectId }
        },
        async syncCustomerCardOptions(contract, preserveCurrent = false) {
            const contractId = contract && (typeof contract === 'object' ? contract.id : contract)
            this.customerCardOptions = []
            this.customerCardSelectKey = Date.now()

            if (!contractId) {
                this.form.customer_card = null
                return
            }

            try {
                const { data } = await this.$http.get(`/customer_contracts/${contractId}/service_cards/`, {
                    params: { page: 1, page_size: 100 }
                })
                const results = Array.isArray(data?.results) ? data.results : []
                this.customerCardOptions = results

                const currentId = this.form.customer_card && typeof this.form.customer_card === 'object'
                    ? this.form.customer_card.id
                    : this.form.customer_card

                if (results.length === 1) {
                    this.form.customer_card = results[0].id
                } else if (!preserveCurrent || !results.some(item => item.id === currentId)) {
                    this.form.customer_card = null
                }
            } catch (error) {
                this.form.customer_card = null
                errorHandler({ error, show: false })
            } finally {
                this.customerCardSelectKey = Date.now()
            }
        },
        async onContractChange(contract) {
            this.form.contract = contract || null
            await this.syncCustomerCardOptions(this.form.contract)
        },
        onCustomerCardChange(customerCardId) {
            this.form.customer_card = customerCardId || null
        },
        projectChange() {
            this.form.contract = null
            this.form.customer_card = null
            this.customerCardOptions = []
            this.customerCardSelectKey = Date.now()
            this.contractSelectKey = Date.now()

            if (!this.resolvedProjectId) return

            this.requestReplaceVisors({ reason: 'project', id: this.resolvedProjectId })
            this.updateDatesMismatch()
        },
        groupChange() {
            if (!this.form?.workgroup?.id) { return }
            this.requestReplaceVisors({ reason: 'group', id: this.form.workgroup.id })
        },
        draftWatch() {
            if (formWatch) formWatch()
            formWatch = this.$watch('form', {
                deep: true,
                handler() {
                    if (this.visible && !this.copy && !this.subtask && !this.initPhase && !this.disableDraft) {
                        this.isDraft = true
                        localStorage.setItem('task_create_form_draft', JSON.stringify(this.form))
                    }
                }
            })
        },
        changeMetadata({ key, value }) {
            this.$set(this.form.metadata, key, value);
        },
        async clearDraftForm() {
            formWatch();
            this.isDraft = false;
            localStorage.removeItem("task_create_form_draft");
            this.form = {...formModel}

            if(!this.form.organization) {
                if(this.user?.current_contractor) {
                    this.form.organization = this.user.current_contractor
                } else {
                    this.getMyOrganization()
                }
            }

            this.form.visors = [];
            this.form.cooperators = [];
            this.form.prerequisites = [];
            this.form.attachments = [];
            this.fileList = [];
            this.customerCardOptions = []
            this.customerCardSelectKey = Date.now()
            this.contractSelectKey = Date.now()
            this.moreFieldsShow = false
            await this.generateForm();
            this.draftWatch();
        },
        async getMyOrganization() {
            try {
                const { data } = await this.$http.get('/users/my_organizations/', {
                    params: {
                        page: 1,
                        page_size: 1,
                        page_name: 'select_organization_drawer',
                        display: 'tree'
                    }
                })
                if(data?.results?.[0]) {
                    this.form.organization = data.results[0]
                }
            } catch(error) {
                errorHandler({error, show: false})
            }
        },
        formInit() {
            if (!this.form?.task_type) {
                this.form.task_type = this.taskType;
            }
        },
        openFileModal() {
            this.$nextTick(() => {
                this.$refs.fileAttach.openFileModal();
            });
        },
        clearForm() {
            this.isDraft = false;
            this.formInject = null;

            if (this.formDefault) this.$store.commit("task/SET_FORM_DEFAULT", null);

            if (!this.formCopy) {
                this.form = {...formModel}
                this.form.visors = [];
                this.form.cooperators = [];
                this.form.prerequisites = [];
                this.form.attachments = [];
                this.fileList = [];
                this.form.organization = null
                this.form.customer_card = null
                this.customerCardOptions = []
                this.customerCardSelectKey = Date.now()
                this.contractSelectKey = Date.now()
            }

            this.subtask = false
            this.formCopy = false;
            this.copy = false;
            this.open = false;
            this.moreCreate = false;
            this.pinFocus = false;
        },
        openFullForm() {
            this.openFullCheck = true
            eventBus.$emit('ADD_WATCH', {type: 'copy', data: this.form}) 
            this.visible = false
        },
        getCalendarContainer(trigger) {
            return trigger.parentNode
        },
        checkOldSelect(field) {
            if (typeof field.oldSelected === "boolean") {
                return field.oldSelected;
            } else return true;
        },
        async generateForm() {
            try {
                this.form.owner = {
                    ...this.user,
                    id: this.user.id,
                    full_name: this.user.last_name + " " + this.user.first_name,
                };

                // TODO
                if (this.formDefault?.task_type && this.form.task_type !== this.formDefault["task_type"])
                    this.form.task_type = this.formDefault.task_type;

                if (this.parentTask?.workgroup)
                    this.form.workgroup = this.parentTask.workgroup;
                if (this.parentTask?.project)
                    this.form.project = this.parentTask.project;
                if (this.parentTask?.dead_line)
                    this.form.p_dead_line = this.parentTask.dead_line;

                const draftForm = JSON.parse(
                    localStorage.getItem("task_create_form_draft")
                );
                if (draftForm && !this.copy && !this.disableDraft) {
                    if (!isEqual(draftForm, this.form)) {
                        this.form = draftForm;
                        this.isDraft = true;
                        this.updateDatesMismatch()
                    }
                } else this.isDraft = false;

                if (this.formDefault?.project?.dead_line) {
                    const dead_line = checkDateDeadLine(this.formDefault, "dead_line");
                    this.formDefault.r_dead_line_from = dead_line;
                    this.formDefault.p_dead_line_from = dead_line;
                }

                if (this.formDefault?.project?.date_start_plan) {
                    this.formDefault.s_dead_line_from = checkDate(
                        this.formDefault,
                        "date_start_plan"
                    );
                }

                if (this.formInject) {
                    this.form = {...this.form, ...this.formInject}
                } if (this.formDefault) {
                    this.form = Object.assign(
                        this.form,
                        JSON.parse(JSON.stringify(this.formDefault))
                    )
                }

                if(this.form.task_type !== 'task' || this.form.workgroup)
                    this.moreFieldsShow = true

                const raw = localStorage.getItem('task_create_form_draft')
                if (raw && !this.copy && !this.disableDraft) {
                    const draftForm = JSON.parse(raw)
                    if (!isEqual(draftForm, this.form)) this.form = draftForm
                    this.isDraft = true
                } else
                    this.isDraft = false

                if (this.form.customer_card && typeof this.form.customer_card === 'object') {
                    this.form.customer_card = this.form.customer_card.id || null
                }

                this.updateDatesMismatch();
                await this.getFormInfo();
                if (this.form.contract) {
                    await this.syncCustomerCardOptions(this.form.contract, true)
                }
            } catch(error) {
                errorHandler({error, show: false})
            }
        },
        async afterVisibleChange(vis) {
            if (vis) {
                this.initPhase = true
                this.editorGate = false
                this.formInit()
                await this.generateForm()
                await this.$nextTick()
                await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))
                this.editorGate = true
                this.draftWatch()
                this.$nextTick(() => {
                    this.initPhase = false
                })
            } else {
                this.disableDraft = false
                this.moreFieldsShow = false
                this.formCopy = false
                this.moreCreate = false
                this.pinFocus = false
                this.formInfo = null
                this.datesDonMatch = false
                this.changeParentDisabled = false
                if (formWatch) formWatch()
                this.clearForm()
                if(!this.openFullCheck)
                    eventBus.$emit('close_add_task_modal')
                this.openFullCheck = false
            }
        },
        async submitTask() {
            try {
                this.loading = true;
                const payload = this.pinFocus ? { ...this.form, pinned: true } : this.form;
                const res = await this.$store.dispatch("task/addTask", payload);
                if (res) {
                    if(this.form.reason_model && this.form.reason_model === 'comments' && this.form.reason_parent) {
                        eventBus.$emit(`comment_task_added_${this.form.reason_parent}`, {
                            item: this.form.reason
                        })
                    }
                        
                    if (this.$store.hasModule('workplan')) {
                        this.$store.dispatch('workplan/reloadList', {
                            list: 'taskList'
                        })
                    }
                    if(this.form.isWorkPlan) {
                        eventBus.$emit('work_day_add_task', {
                            ...res,
                            planeIndex: this.form.planeIndex
                        })
                        delete this.form.isWorkPlan
                        delete this.formInject.isWorkPlan
                    }

                    const openTask = () => {
                        const query = {...this.$route.query}
                        if(!query.task) {
                            query.task = res.id;
                            this.$router.push({ query });
                        } else {
                            delete query.task
                            this.$router.push({ query })
                            setTimeout(() => {
                                openTask()
                            }, 800)
                        }
                    };
                    if (this.mainKey && this.taskList?.[this.mainKey]?.length)
                        eventBus.$emit("UPDATE_LIST");

                    if (this.open) {
                        this.$message.info(this.createdMessage);
                        openTask();
                        this.open = false;
                    } else {
                        this.$message.info(
                            this.$createElement("span", {}, [
                    `${this.createdMessage}.`,
                    this.$createElement(
                        "span",
                        {
                            class: "link cursor-pointer blue_color",
                            on: {
                                click: () => {
                                    openTask();
                                },
                            },
                        },
                    ` ${this.openTaskText}`
                    ),
                            ]),
                            5
                        );
                    }

                    if (!this.moreCreate && !this.formCopy) this.visible = false;

                    if (this.form.create_handler) {
                        eventBus.$emit(
                `TASK_CREATED_${this.form.task_type}_${this.form.create_handler}`,
                {
                    ...res,
                    formData: this.form,
                }
                        );
                    }
                    eventBus.$emit(`drawer_select_save_state_${res.id}`);
                    eventBus.$emit(`update_filter_${this.pageName}`)
                    eventBus.$emit(`drawer_select_save_state_${this.form.id}`);
                    //eventBus.$emit('update_task_handler')

                    this.clearForm();
                    this.clearDraftForm();
                }
            } catch (error) {
                errorHandler({error})
            } finally {
                this.pinFocus = false;
                this.loading = false;
            }
        },
        submitAndCreate() {
            this.moreCreate = true;
            this.open = false;
            this.subtask = false;
            this.formCopy = false;
            this.pinFocus = false;
            this.onSubmit();
        },
        submitAndOpen() {
            this.open = true;
            this.formCopy = false;
            this.moreCreate = false;
            this.pinFocus = false;
            this.onSubmit();
        },
        submitAndPinFocus() {
            this.open = false;
            this.formCopy = false;
            this.moreCreate = false;
            this.subtask = false;
            this.pinFocus = true;
            this.onSubmit();
        },
        onSubmit() {
            if (this.loading) { return }
            this.$refs.taskForm.validate(async (valid, invalidFields) => {
                this.invalidFields = Object.keys(invalidFields);
                if (valid) {
                    if(this.form.project) {
                        if (this.datesDonMatch)
                            this.dateConfirm()
                        else
                            await this.submitTask()
                    } else {
                        this.$confirm({
                            title: this.$t('task.project_no_selected'),
                            content: this.$t('task.project_no_selected_message'),
                            okText: this.$t('task.create_no_project'),
                            cancelText: this.$t('task.use_project'),
                            onOk: async () => {
                                await this.submitTask()
                            },
                            onCancel: () => {
                                this.$nextTick(() => {
                                    if(this.$refs.projectSelect)
                                        this.$refs.projectSelect.openSelect()
                                })
                            }
                        })
                    }
                } else {
                    this.$message.warning(this.$t("task.field_require_all"));
                    return false;
                }
            });
        },
        nameGenerator() {
            if (this.formInfo?.nameGenerate) {
                if (this.form.task_type === "logistic") {
                    this.form.name = `${$t("task.delivery_from")} ${this.$moment().format(
                        "DD.MM.YYYY"
                    )}`;
                }
                if (this.form.task_type === "task") {
                    this.form.name = `${$t("task.task_from")} ${this.$moment().format(
                        "DD.MM.YYYY"
                    )}`;
                }
            }
        },
        async getFormInfo() {
            if (!this.formInfo) {
                try {
                    this.formLoading = true;
                    await this.$store.dispatch("task/getFormInfo", {
                        task_type: this.form.task_type,
                    });
                    if(!this.form.organization) {
                        if(this.user?.current_contractor) {
                            this.form.organization = this.user.current_contractor
                        } else {
                            await this.getMyOrganization()
                        }
                    }
                    this.formInfo = this.$store.getters["task/getFormInfoByType"](
                        this.form.task_type
                    );

                    this.$nextTick(() => {
                        if(this.$refs?.nameInput)
                            this.$refs.nameInput.focus()
                    })
                } catch (error) {
                    errorHandler({error, show: false})
                } finally {
                    this.formLoading = false;
                }
            }

            this.nameGenerator();
        },
        async getParentById(id) {
            try {
                const params = {
                    task_type: "task,stage,milestone",
                    filters: { id: id },
                };

                return await this.$http.get("tasks/task/list", { params });
            } catch(error) {
                errorHandler({error, show: false})
            }
        },
    },
    mounted() {
        eventBus.$on('add_task_modal', data => {
            this.formInject = {...data}
            this.visible = true

        })
        eventBus.$on("add_task_modal_watch", async ({ type = null, data, key = null }) => {
            this.isDraft = false;
            /*if (key) {
                this.updateForm({ key, data });
            }*/
            if (type) {
                if (type === "subtask") {
                    this.subtask = true;
                    const subtask = {
                        parent: {
                            name: data.name,
                            id: data.id,
                            dead_line: data.dead_line,
                            date_start_plan: data.date_start_plan,
                        },
                        project: data.project || null,
                        workgroup: data.workgroup || null,
                        dead_line: data.dead_line ? this.$moment(data.dead_line) : null,
                        p_dead_line_from: checkDate(data, "dead_line"),
                        s_dead_line_from: checkDate(data, "date_start_plan"),
                        r_dead_line_from: checkDate(data, "dead_line"),
                    }
                    this.formInject = {...subtask}
                    this.disableDraft = true;
                } else if (type === "copy") {
                    this.copy = true;
                    let copy = { ...data };
                    copy.reason_model = "";
                    copy.reason = null;

                    if (copy.reason?.id) copy.reason = copy.reason.id;

                    copy.owner = {
                        ...this.user,
                        id: this.user.id,
                        full_name: this.user.last_name + " " + this.user.first_name,
                    };
                    if (copy.attachments?.length) {
                        copy.attachments.forEach((file) => {
                            this.fileList.push({
                                uid: file.id,
                                name: file.path,
                                status: "done",
                                url: file.path,
                            });
                        });
                    }
                    if(copy.cooperators?.length) {
                        copy.cooperators = copy.cooperators.map(us => {
                            if(us.user) {
                                return {
                                    ...us.user,
                                    id: us.user.id,
                                    full_name: us.user.last_name + " " + us.user.first_name,
                                }
                            } else
                                return us
                            
                        })
                    }
                    this.form = JSON.parse(JSON.stringify(copy))
                    this.disableDraft = true;
                } else if (type === "add_task") {
                    const form = {...data}
                    if (data.attachments && data.attachments.length) {
                        data.attachments.forEach((file) => {
                            this.fileList.push({
                                uid: file.id,
                                name: file.path,
                                status: "done",
                                url: file.path,
                            });
                        });
                    }
                    form.p_dead_line_from = checkDate(data, "dead_line");
                    form.s_dead_line_from = checkDate(data, "date_start_plan");
                    form.r_dead_line_from = checkDate(data, "dead_line");

                    if (data.changeParentDisabled) {
                        this.changeParentDisabled = true;
                    }

                    if (data.organization?.id) {
                        form.organization = data.organization
                    }

                    if (data.parent && !data.parent.id) {
                        try {
                            const response = await this.getParentById(data.parent);
                            form.parent = response.data.results[0];
                        } catch (error) {
                            console.error(error);
                            form.parent = null;
                        }
                    }

                    this.formInject = {...form}
                    this.disableDraft = true;
                }
            }
            this.visible = true;

            if (this.form.visors.length === 0) {
                if (data?.project?.id) {
                    this.requestReplaceVisors({ reason: 'project', id: data.project.id })
                    // this.setDefaultVisors(data.project.id)
                } else if (data?.workgroup?.id) {
                    this.requestReplaceVisors({ reason: 'group', id: data.workgroup.id })
                }
            }

        });
    },
    beforeDestroy() {
        eventBus.$off('add_task_modal')
        eventBus.$off('add_task_modal_watch')
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
  transform: translateX(10px);
  opacity: 0;
}
.name_field{
    &::v-deep{
        .has-error{
            .ant-input{
                &::placeholder{
                    color: #f5222d;
                }
            }
            .ant-form-explain{
                display: none;
            }
        }
    }
}
.date_select{
    &::v-deep{
        .ant-calendar-picker-ghost.ant-calendar-picker-icon-left .ant-calendar-picker-input{
            padding-left: 25px;
        }
    }
}
.input_pd{
    &::v-deep{
        .ant-input{
            &.ant-input-ghost{
                font-size: 14px!important;
                padding-left: 35px!important;
            }
        }
    }
}
.description_editor{
    min-height: 108.65px;
    &::v-deep{
        .ck-editor__top{
            position: sticky !important;
            top: 0px !important;
            background: white !important;
            z-index: 999999;
        }
        .ck{
            &.ck-toolbar__items{
                margin-right: 0px!important;
            }
            &.ck-toolbar__separator{
                opacity: 0;
                margin-right: 0px!important;
            }
            &.ck-toolbar{
                border: 0px;
            }
            &.ck-content{
                border: 0px!important;
                box-shadow: none!important;
                padding-left: 0px!important;
                padding-right: 0px!important;
            }
        }
    }
}
.btn_select{
    font-size: 14px;
    color: var(--text);
    &::v-deep{
        .ant-select-selection{
            height: 36px;
            background: #f7f9fb;
            border-color: #f7f9fb;
            box-shadow: initial!important;
            .ant-select-selection__rendered{
                line-height: 34px;
            }
        }
    }
}
.btn_divider{
    height: 100%;
    width: 1px;
    background: #d9d9d9;
    margin: 0 4px;
    min-height: 36px;
}
.name_form{
    margin-bottom: -15px;
}
.modal_contract_select{
    min-width: 220px;
}
.priority_picker{
    &__item{
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
        &:hover{
            background: #f0f1f6;
        }
        &.active{
            background: #f0f1f6;
        }
    }
}
</style>
