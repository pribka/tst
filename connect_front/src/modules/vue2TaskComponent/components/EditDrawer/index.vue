<template>
    <DrawerTemplate
        ref="drawerTemplate"
        v-model="visible"
        :hardZIndex="hardZIndex"
        @afterVisibleChange="afterVisibleChange"
        @close="onClose"
        :width="drawerWidth">
        <template #rightHeader>
            <transition name="slide-fade">
                <a-tag
                    v-if="isDraft"
                    closable
                    @close="clearDraftForm"
                    class="draft_task"
                    color="purple">
                    {{ $t("task.draft") }}
                </a-tag>
            </transition>
            <HelpButton partCode="tasks" />
        </template>
        <template #title>
            <div class="flex w-full justify-between items-center">
                <span class="title">{{ editDrawerTitle }}</span>
            </div>
        </template>
        <div class="d_body w-full" ref="tFormBody">
            <a-spin class="w-full" :spinning="formLoading">
                <template v-if="formInfo">
                    <a-form-model
                        ref="taskForm"
                        class="task_form_wrap"
                        :model="form"
                        :rules="rules">
                        <a-form-model-item
                            v-if="formInfo.name"
                            :rules="formInfo.name.rules"
                            :label="$t('task.form_name')"
                            prop="name">
                            <a-input
                                v-model="form.name"
                                size="large"
                                :placeholder="$t('task.form_name')"/>
                        </a-form-model-item>
                        <a-form-model-item
                            v-if="!edit && formInfo.task_type"
                            :label="formInfo.task_type.title"
                            :rules="formInfo.task_type.rules"
                            prop="task_type">
                            <a-select
                                v-model="form.task_type"
                                size="large"
                                :getPopupContainer="getPopupContainer"
                                :placeholder="$t('Type')"
                                @change="changeTaskType"
                                defaultValue="task">
                                <a-select-option
                                    v-for="item in taskTypeOptions"
                                    :key="item.value"
                                    :value="item.value">
                                    {{ item.label }}
                                </a-select-option>
                            </a-select>
                        </a-form-model-item>
                        <a-form-model-item
                            v-if="formInfo.description"
                            :label="$t('task.form_description')"
                            :rules="formInfo.description.rules"
                            class="description_row relative"
                            style="z-index: 5;"
                            prop="description">
                            <component
                                :is="ckEditor"
                                :taskId="form.id"
                                :key="edit || visible"
                                v-model="form.description"/>
                        </a-form-model-item>
                        <a-form-model-item
                            v-if="formInfo.result && !isStage && !isMilestone"
                            :rules="formInfo.result.rules"
                            :label="formInfo.result.title"
                            prop="result">
                            <a-input
                                v-model="form.result"
                                size="large"
                                :placeholder="formInfo.result.title"/>
                        </a-form-model-item>
                        <div class="grid grid-cols-1 md:grid-cols-2 md:gap-4">
                            <a-form-model-item
                                v-if="formInfo.date_start_plan && !isMilestone"
                                :rules="rules.date_start_plan"
                                :label="formInfo.date_start_plan.title"
                                prop="date_start_plan">
                                <DatePicker
                                    v-model="form.date_start_plan"
                                    size="large"
                                    allowClear
                                    :disabledAfter="disabledStartDateAfter"
                                    :disabledBefore="disabledStartDateBefore"
                                    :getCalendarContainer="getPopupContainer"
                                    :disabled="isMilestone"
                                    :show-time="{ format: 'HH:mm' }"
                                    @change="dateStartChange">
                                    <template #suffixIcon>
                                        <i class="fi fi-rr-play" />
                                    </template>
                                </DatePicker>
                            </a-form-model-item>
                            <a-form-model-item
                                v-if="formInfo.dead_line"
                                :rules="rules.dead_line"
                                :label="formInfo.dead_line.title"
                                prop="dead_line">
                                <DatePicker
                                    v-model="form.dead_line"
                                    allowClear
                                    size="large"
                                    :getCalendarContainer="getPopupContainer"
                                    :disabledAfter="disabledDeadlineAfter"
                                    :disabledBefore="disabledDeadlineBefore"
                                    :startTime="false"
                                    @change="deadlineChange"
                                    :show-time="{ format: 'HH:mm' }">
                                    <template #suffixIcon>
                                        <i class="fi fi-rr-calendar-check" />
                                    </template>
                                </DatePicker>
                            </a-form-model-item>
                        </div>
                        <div class="flex tabs">
                            <a-button
                                v-for="tab in tabs"
                                :key="tab.value"
                                size="large"
                                useTruncate
                                class="mr-4 last:mr-0 button-light"
                                :class="
                                    invalidFields.includes('organization') &&
                                        tab.value === 'select_project' &&
                                        'button_error'
                                "
                                block
                                :type="activeTab === tab.value ? 'primary' : ''"
                                @click="selectTab(tab.value)">
                                {{ tab.label }}
                            </a-button>
                        </div>

                        <div ref="mobCollapse" class="mobile-tabs">
                            <a-collapse
                                v-for="(tab, index) in tabs"
                                :key="tab.value"
                                v-model="activeKey"
                                class="mobile-tab"
                                :bordered="false">
                                <a-collapse-panel :key="tab.value" :header="tab.label">
                                    <hr class="mobile-tabs__divider my-2" />
                                    <component
                                        :is="tabComponent(tab.value)"
                                        v-model="form"
                                        :ref="`collapse_comp_${index}`"
                                        :formInfo="formInfo"
                                        :defaultUserSelectId="defaultUserSelectId"
                                        :opnUserSetting="opnUserSetting"
                                        :edit="edit"
                                        :checkOldSelect="checkOldSelect"
                                        :changeMetadata="changeMetadata"
                                        :selectProject="selectProject"
                                        :getContractSelectApiUrl="getContractSelectApiUrl"
                                        :getContractSelectParams="getContractSelectParams"
                                        :contractSelectKey="contractSelectKey"
                                        :groupChange="groupChange"
                                        :openSubtaskSelection="openSubtaskSelection"
                                        :selectParentTask="selectParentTask"
                                        :changeParentDisabled="changeParentDisabled"
                                        :parentZIndex="drawerZIndex"
                                        :visible="visible"
                                        :isMilestone="isMilestone"
                                        :isStage="isStage"/>
                                </a-collapse-panel>
                            </a-collapse>
                        </div>
                        <div ref="descTab">
                            <div
                                v-show="activeTab === tab.value"
                                class="desctop-tab"
                                v-for="(tab, index) in tabs"
                                :key="tab.value">
                                <div class="mt-5">
                                    <div class="tab-panel">
                                        <component
                                            :is="tabComponent(tab.value)"
                                            v-model="form"
                                            :ref="`tab_comp_${index}`"
                                            :formInfo="formInfo"
                                            :defaultUserSelectId="defaultUserSelectId"
                                            :opnUserSetting="opnUserSetting"
                                            :edit="edit"
                                            :checkOldSelect="checkOldSelect"
                                            :changeMetadata="changeMetadata"
                                            :selectProject="selectProject"
                                            :getContractSelectApiUrl="getContractSelectApiUrl"
                                            :getContractSelectParams="getContractSelectParams"
                                            :contractSelectKey="contractSelectKey"
                                            :groupChange="groupChange"
                                            :openSubtaskSelection="openSubtaskSelection"
                                            :selectParentTask="selectParentTask"
                                            :parentZIndex="drawerZIndex"
                                            :changeParentDisabled="changeParentDisabled"
                                            :visible="visible"
                                            :isMilestone="isMilestone"
                                            :isStage="isStage"/>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <a-form-model-item
                            v-if="formInfo.customer_card"
                            :rules="formInfo.customer_card.rules || null"
                            :label="formInfo.customer_card.title"
                            :label-col="formInfo.customer_card['label-col'] || { span: 5 }"
                            :wrapper-col="formInfo.customer_card['wrapper-col'] || { span: 12 }"
                            labelAlign="left"
                            ref="customer_card"
                            prop="customer_card">
                            <DSelect
                                :value="customerCardId"
                                :apiUrl="formInfo.customer_card.dataPath || '/app_info/filtered_select_list/?model=help_desk.CustomerCardModel'"
                                class="w-full"
                                infinity
                                size="large"
                                :resultsKey="formInfo.customer_card.listObject || 'filteredSelectList'"
                                :showSearch="true"
                                :initList="true"
                                :initOptionList="customerCardOptionList"
                                :useOptionFlex="false"
                                :useSearchApi="true"
                                :allowClear="true"
                                searchKey="search"
                                labelKey="string_view"
                                :listObject="false"
                                :default-active-first-option="false"
                                :filter-option="false"
                                :not-found-content="null"
                                :placeholder="formInfo.customer_card.title || null"
                                @change="customerCardHandler"
                                @changeFull="customerCardFullHandler"/>
                        </a-form-model-item>
                        <a-form-model-item
                            v-if="formInfo.potential_contractor_name"
                            :rules="formInfo.potential_contractor_name.rules"
                            :label="formInfo.potential_contractor_name.title"
                            :label-col="
                                formInfo.potential_contractor_name['label-col'] || { span: 5 }
                            "
                            :wrapper-col="
                                formInfo.potential_contractor_name['wrapper-col'] || {
                                    span: 12,
                                }
                            "
                            labelAlign="left"
                            ref="p_contractor_name"
                            prop="p_contractor_name">
                            <a-input
                                v-model="form.p_contractor_name"
                                :disabled="form.contractor !== null || Boolean(customerCardId)"
                                size="large"
                                allowClear
                                :placeholder="formInfo.potential_contractor_name.title || null"/>
                        </a-form-model-item>
                        <a-form-model-item
                            v-if="formInfo.potential_contractor_company"
                            :rules="formInfo.potential_contractor_company.rules || null"
                            :label="formInfo.potential_contractor_company.title"
                            :label-col="
                                formInfo.potential_contractor_company['label-col'] || {
                                    span: 5,
                                }
                            "
                            :wrapper-col="
                                formInfo.potential_contractor_company['wrapper-col'] || {
                                    span: 12,
                                }
                            "
                            labelAlign="left"
                            ref="p_contractor_company"
                            prop="p_contractor_company">
                            <a-input
                                v-model="form.p_contractor_company"
                                :disabled="form.contractor !== null || Boolean(customerCardId)"
                                size="large"
                                allowClear
                                :placeholder="
                                    formInfo.potential_contractor_company.title || null
                                "/>
                        </a-form-model-item>
                        <a-form-model-item
                            v-if="formInfo.phone"
                            :label="formInfo.phone.title"
                            :label-col="formInfo.phone['label-col'] || { span: 5 }"
                            :wrapper-col="formInfo.phone['wrapper-col'] || { span: 12 }"
                            labelAlign="left"
                            ref="phone"
                            prop="phone">
                            <a-input
                                v-model="form.phone"
                                :disabled="form.contractor !== null"
                                size="large"
                                allowClear
                                :placeholder="formInfo.phone.title || null"/>
                        </a-form-model-item>
                        <a-form-model-item
                            v-if="formInfo.email"
                            :rules="formInfo.email.rules || null"
                            :label="formInfo.email.title"
                            :label-col="formInfo.email['label-col'] || { span: 5 }"
                            :wrapper-col="formInfo.email['wrapper-col'] || { span: 12 }"
                            labelAlign="left"
                            ref="email"
                            prop="email">
                            <a-input
                                v-model="form.email"
                                :disabled="form.contractor !== null"
                                size="large"
                                allowClear
                                :placeholder="formInfo.email.title || null"/>
                        </a-form-model-item>
                        <a-form-model-item
                            v-if="formInfo.lead_source"
                            :rules="formInfo.lead_source.rules || null"
                            :label="formInfo.lead_source.title"
                            :label-col="formInfo.lead_source['label-col'] || { span: 5 }"
                            :wrapper-col="formInfo.lead_source['wrapper-col'] || { span: 12 }"
                            labelAlign="left"
                            ref="lead_source"
                            prop="lead_source">
                            <a-select
                                v-model="form.lead_source"
                                allowClear
                                size="large"
                                :getPopupContainer="getPopupContainer"
                                :loading="leadSourcesLoader"
                                @change="onChange"
                                :placeholder="$t('task.source_appeal')">
                                <a-select-option
                                    v-for="lead_source in leadSources"
                                    :key="lead_source.id"
                                    :value="lead_source.id">
                                    {{ lead_source.name }}
                                </a-select-option>
                            </a-select>
                        </a-form-model-item>
                        <a-form-model-item
                            v-if="isFromOrder()"
                            :rules="formInfo.start_point.rules || null"
                            :label="formInfo.start_point.title"
                            prop="start_point"
                            :label-col="formInfo.start_point['label-col'] || { span: 5 }"
                            :wrapper-col="formInfo.start_point['wrapper-col'] || { span: 12 }"
                            labelAlign="left">
                            <a-select v-model="form.start_point">
                                <a-select-option
                                    v-for="startPoint in startPointList"
                                    :key="startPoint.id"
                                    :value="startPoint.id">
                                    {{ startPoint.string_view }}
                                </a-select-option>
                            </a-select>
                        </a-form-model-item>
                        <a-form-model-item
                            v-if="formInfo.contractor"
                            :rules="formInfo.contractor.rules"
                            :label="formInfo.contractor.title"
                            :label-col="formInfo.contractor['label-col'] || { span: 5 }"
                            :wrapper-col="formInfo.contractor['wrapper-col'] || { span: 12 }"
                            labelAlign="left"
                            ref="contractor"
                            prop="contractor">
                            <ContractorDrawer
                                v-model="form.contractor"
                                inputSize="large"
                                :selectContractor="contractorHandler"
                                :title="
                                    formInfo.contractor.drawerTitle ||
                                        $t('task.contractordrawer.drawerTitle')
                                "/>
                        </a-form-model-item>
                        <a-collapse
                            v-model="expandActive"
                            :bordered="false"
                            class="collapse mt-2">
                            <a-collapse-panel key="1" :header="$t('task.additionally')">
                                <a-form-model-item
                                    v-if="taskType && taskType === 'task'"
                                    :label="$t('task.reason_inject')">
                                    <TicketSelect 
                                        v-model="form.reasonObject" 
                                        inputType="defaultInput" />
                                </a-form-model-item>

                                <a-form-model-item
                                    v-if="formInfo.funds"
                                    :label="formInfo.funds.title"
                                    prop="funds">
                                    <a-input-number
                                        v-model="form.funds"
                                        :max="Math.pow(10, 13) - 1"
                                        :min="0"
                                        :placeholder="formInfo.funds.title"
                                        class="w-full"
                                        size="large"/>
                                </a-form-model-item>
                                <a-form-model-item
                                    v-if="formInfo.execution_time_plan"
                                    :label="formInfo.execution_time_plan.title"
                                    prop="execution_time_plan">
                                    <a-input-number
                                        v-model="form.execution_time_plan"
                                        :max="Math.pow(10, 4) - 1"
                                        :min="0"
                                        :step="0.5"
                                        :placeholder="formInfo.execution_time_plan.title"
                                        class="w-full"
                                        size="large"/>
                                </a-form-model-item>

                                <a-form-model-item v-if="!edit" prop="makeEvent">
                                    <a-checkbox v-model="form.is_need_to_make_event">
                                        {{ $t("task.make_event") }}
                                    </a-checkbox>
                                </a-form-model-item>
                                <a-form-model-item
                                    v-if="form.reason_model"
                                    :label="$t('task.task_based')"
                                    :label-col="{ span: 6 }"
                                    :wrapper-col="{ span: 13 }"
                                    labelAlign="left">
                                    <div
                                        class="user_draw_input ant-input flex items-center relative">
                                        <a-tag color="blue" class="tag_block">
                                            <template v-if="form.reason_model === 'chat_message'">
                                                {{ $t("task.chat_message") }}
                                            </template>
                                            <template v-if="form.reason_model === 'comments'">
                                                {{ $t("task.comment") }}
                                            </template>
                                            <template v-if="form.reason_model === 'files'">
                                                {{ $t("task.file2") }}
                                            </template>
                                            <template v-if="form.reason_model === 'order'">
                                                {{ $t("task.order") }} №{{ form.reason_name }}
                                            </template>
                                        </a-tag>
                                        <a-button @click="reasonClear()" type="link" class="px-0">
                                            {{ $t("task.remove") }}
                                        </a-button>
                                    </div>
                                </a-form-model-item>

                                <a-button
                                    v-if="formInfo.set_points && formInfo.set_points.available"
                                    @click="openAddressDrawer"
                                    :loading="addressButtonLoading">
                                    {{
                                        formInfo.set_points.button_text ||
                                            $t("task.specify_address")
                                    }}
                                </a-button>
                                <div v-if="taskPointsList.length !== 0" class="mt-5">
                                    <a-descriptions :title="mapConfig.listTitle" />

                                    <div class="divide-y">
                                        <a-list
                                            item-layout="horizontal"
                                            v-for="(point, n) in taskPointsList"
                                            :key="n">
                                            <a-list-item>
                                                <a-list-item-meta>
                                                    <div slot="title" class="flex flex-row">
                                                        <div class="mr-5">{{ n + 1 }}</div>
                                                        <div>{{ point.name }}</div>
                                                    </div>
                                                </a-list-item-meta>
                                            </a-list-item>
                                        </a-list>
                                    </div>
                                </div>
                            </a-collapse-panel>
                        </a-collapse>
                    </a-form-model>
                </template>
            </a-spin>
        </div>
        <template v-if="formInfo" #footer>
            <div class="d_footer w-full">
                <a-button
                    v-if="edit"
                    type="primary"
                    :block="isMobile"
                    size="large"
                    class="mr-2 w-full md:w-auto lg:w-auto"
                    :loading="loading"
                    @click="update()">
                    {{ saveBtnText }}
                </a-button>
                <template v-else>
                    <div v-if="isMobile" class="flex items-center w-full">
                        <a-button
                            type="primary"
                            :loading="loading"
                            block
                            size="large"
                            @click="submit()">
                            {{ saveBtnText }}
                        </a-button>
                        <a-button
                            type="primary"
                            :disabled="loading"
                            size="large"
                            class="ml-1 dots_btn"
                            flaticon
                            icon="fi-rr-menu-dots-vertical"
                            @click="visibleActivity = true"/>
                        <ActivityDrawer v-model="visibleActivity">
                            <ActivityItem
                                v-if="formInfo.formActions.create_and_open"
                                key="0"
                                @click="submitAndOpen()">
                                <i class="fi fi-rr-link-horizontal"></i>
                                {{ $t("task.create_and_open") }}
                            </ActivityItem>
                            <ActivityItem
                                v-if="formInfo.formActions.create_and_create"
                                key="1"
                                @click="submitAndCreate()">
                                <i class="fi fi-rr-apps-add"></i>
                                {{ $t("task.create_and_create") }}
                            </ActivityItem>
                            <ActivityItem
                                v-if="formInfo.formActions.create_and_copy"
                                key="2"
                                @click="submitAndCopy()">
                                <i class="fi fi-rr-duplicate"></i>
                                {{ $t("task.create_and_copy") }}
                            </ActivityItem>
                            <ActivityItem
                                key="3"
                                @click="submitAndPinFocus()">
                                <i class="fi fi-rr-flag-alt"></i>
                                {{ $t("task.create_and_pin_focus") }}
                            </ActivityItem>
                        </ActivityDrawer>
                    </div>
                    <a-button-group v-else class="mr-2">
                        <a-button type="primary" size="large" :loading="loading" @click="submit()">
                            {{ saveBtnText }}
                        </a-button>
                        <a-dropdown
                            v-if="formInfo.formActions"
                            :trigger="['click']"
                            :disabled="loading">
                            <a-button type="primary" size="large" icon="more" class="flex items-center justify-center" />
                            <a-menu slot="overlay">
                                <a-menu-item
                                    v-if="formInfo.formActions.create_and_open"
                                    key="0"
                                    @click="submitAndOpen()">
                                    {{ $t("task.create_and_open") }}
                                </a-menu-item>
                                <a-menu-item
                                    v-if="formInfo.formActions.create_and_create"
                                    key="1"
                                    @click="submitAndCreate()">
                                    {{ $t("task.create_and_create") }}
                                </a-menu-item>
                                <a-menu-item
                                    v-if="formInfo.formActions.create_and_copy"
                                    key="2"
                                    @click="submitAndCopy()">
                                    {{ $t("task.create_and_copy") }}
                                </a-menu-item>
                                <a-menu-item
                                    key="3"
                                    @click="submitAndPinFocus()">
                                    {{ $t("task.create_and_pin_focus") }}
                                </a-menu-item>
                            </a-menu>
                        </a-dropdown>
                    </a-button-group>
                </template>
                <a-button v-if="!isMobile" type="ui" size="large" ghost @click="onClose()">
                    {{ $t("task.close") }}
                </a-button>
            </div>
        </template>
        <ReplaceVisorsModal
            ref="replaceVisorsModalRef"
            v-model="form" />

        <TaskSelectDrawer
            v-model="form.parent"
            :taskDrawer="taskDrawer"
            :selectParentTask="selectParentTask"
            :filters="taskSelectFilters"
            :closeHandler="closeTaskSelected"/>
        <DrawerTemplate
            v-model="addressDrawerVisible"
            :title="addressDrawerTitle"
            destroyOnClose
            @afterVisibleChange="addressAfterVisibleChange"
            @close="onCloseAddressDrawer"
            class="set_task_points"
            :width="windowWidth > 1500 ? 1500 : windowWidth">
            <component
                v-if="addressDrawerVisible && SetPointsAsync"
                ref="setPointRef"
                :is="SetPointsAsync"
                :mapConfig="mapConfig"
                :taskTitle="form.name"
                :ownerSelect="true" />
            <template #footer>
                <div class="w-full flex justify-end">
                    <a-button
                        type="ui"
                        ghost
                        block
                        class="my-2 w-24"
                        @click="onCloseAddressDrawer">
                        {{ $t("task.close") }}
                    </a-button>
                </div>
            </template>
        </DrawerTemplate>
    </DrawerTemplate>
</template>

<script>
import { mapState } from "vuex"
import { priorityList } from "@/utils/localeData"
import eventBus from "@/utils/eventBus"
import { ActivityItem, ActivityDrawer } from "@/components/ActivitySelect"
import { isEqual } from "lodash"
import { formModel } from '../../utils/index.js'
import { errorHandler } from '@/utils/index.js'
import taskEdit from '../../mixins/taskEdit.js'
import AddUser from "./FormParts/AddUser.vue"
import SelectProject from "./FormParts/SelectProject.vue"
import SetPriority from "./FormParts/SetPriority.vue"
import AttachFiles from "./FormParts/AttachFiles.vue"
let formWatch;
const checkDate = (data, type) => {
    if (data[type]) {
        return data[type];
    } else if (data.project?.[type]) {
        return data.project[type];
    }

    return null;
};
const checkDateDeadLine = (data, type) => {
    if (data.project?.[type]) {
        return data.project[type];
    } else if (data[type]) {
        return data[type];
    }
    return null;
};

export default {
    name: "TaskEditDrawer",
    mixins: [ taskEdit ],
    components: {
        HelpButton: () => import('@apps/Support/components/HelpButton.vue'),
        DrawerTemplate: () => import("@/components/DrawerTemplate.vue"),
        UserDrawer: () => import("@apps/DrawerSelect/index.vue"),
        TicketSelect: () => import("@apps/DrawerSelect/TicketSelect.vue"),
        Priority: () => import("../Priority.vue"),
        // eslint-disable-next-line vue/no-unused-components
        Upload: () => import("@apps/Upload"),
        // eslint-disable-next-line vue/no-unused-components
        FileAttach: () => import("@apps/vue2Files/components/FileAttach"),
        DatePicker: () => import("./DatePick"),
        //ProjectDrawer: () => import("../ProjectDrawer.vue"),
        //WorkGroupDrawer: () => import("../WorkGroupDrawer.vue"),
        TaskSelectDrawer: () => import("./TaskSelectDrawer.vue"),
        ContractorDrawer: () => import("../ContractorDrawer"),
        AttachFiles,
        AddUser,
        SetPriority,
        SelectProject,
        ActivityItem,
        ActivityDrawer,
        FileDrawer: () => import("../FileDrawer.vue"),
        DSelect: () => import("@apps/DrawerSelect/Select.vue"),
        ReplaceVisorsModal: () => import("../ReplaceVisorsModal.vue")
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
        parentTask() {
            return this.form?.parent || null
        },
        drawerZIndex() {
            return this.$refs?.drawerTemplate?.getZIndex();
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

        deadline() {
            return this.form.dead_line 
        },
        startDate() {
            return this.form.date_start_plan 
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
        /*startDateRules() {
            const isRequired = ["stage"].includes(this.form.task_type)
            const rules = [{
                required: isRequired,
                message: this.$t("task.field_require"),
                trigger: ['blur', 'change'],
            },]
            rules.push({
                validator: (rule, value, callback) => {
                    if (!value) { return callback() }
                    const momentStartDate = this.$moment(value)
                    const momentDeadline = this.$moment(this.form.dead_line)
                    if (this.isDateOutOfLimit(momentStartDate)) {
                        this.$message.error(this.$t('task.date_start_out_of_range'))
                        return callback(new Error(this.$t('task.invalid_start_date')));
                    }
                    if (momentStartDate.isAfter(momentDeadline)) {
                        this.$message.error(this.$t('task.start_date_after_deadline'))
                        return callback(new Error(this.$t('task.invalid_start_date')));
                    }
                    return callback()
                },
                trigger: ['blur', 'change'],
            })
            return rules
        },*/
        /*deadlineRules() {
            const isRequired = ["stage", "milestone"].includes(this.form.task_type)
            const rules = [{
                required: isRequired,
                message: this.$t("task.field_require"),
                trigger: ['blur', 'change'],
            }]

            rules.push({
                validator: (rule, value, callback) => {
                    if (!value) { return callback() }
                    const momentDeadline = this.$moment(value)
                    const momentStartDate = this.$moment(this.form.date_start_plan)
                    if (this.isDateOutOfLimit(momentDeadline)) {
                        this.$message.error(this.$t('task.deadline_out_of_range'))
                        return callback(new Error(this.$t('task.invalid_deadline')));
                    }
                    if (momentDeadline.isBefore(momentStartDate)) {
                        this.$message.error(this.$t('task.deadline_before_start_date'))
                        return callback(new Error(this.$t('task.invalid_deadline')));
                    }
                    return callback()
                },
                trigger: ['blur', 'change'],
            })
            return rules
        },*/
        addressDrawerTitle() {
            return this.formInfo?.set_points?.drawer_title
                ? this.formInfo.set_points.drawer_title
                : this.$t("task.specify_address_2");
        },
        openButtonRef() {
            if (this.$refs.openFileTask?.length) return this.$refs.openFileTask;
            return false;
        },
        drawerWidth() {
            if (this.windowWidth > 900) return 900;
            else if (this.windowWidth < 800 && this.windowWidth > 500)
                return this.windowWidth - 30;
            else return this.windowWidth;
        },
        visible: {
            get() {
                return this.$store.state.task.editDrawer;
            },
            set(value) {
                this.$store.commit("task/SET_EDIT_DRAWER", value);
            },
        },
        ckEditor() {
            if (this.visible) return () => import("@apps/CKEditor");
            else return null;
        },
        filtersUserDrawer() {
            if (this.form?.contractor) {
                return { contractor_profile__contractor: this.form.contractor?.id };
            }
            return null;
        },
        customerCardId() {
            if (!this.form?.customer_card) return null;
            return typeof this.form.customer_card === "object"
                ? this.form.customer_card.id || null
                : this.form.customer_card;
        },
        customerCardOptionList() {
            const customerCard = this.form?.customer_card;
            if (!customerCard || typeof customerCard !== "object") return [];
            return [
                {
                    ...customerCard,
                    string_view:
                        customerCard.string_view ||
                        customerCard.name ||
                        customerCard.full_name ||
                        "",
                },
            ];
        },
        taskSelectFilters() {
            let filters = {};
            if (this.form.workgroup) {
                filters.or_workgroup = this.form.workgroup.id;
            }
            if (this.form.project) {
                filters.or_project = this.form.project.id;
            }
            return filters;
        },
        isMobile() {
            return this.$store.state.isMobile;
        },
        taskType() {
            return this.$store.state.task.taskType;
        },
        showInputPhone() {
            return this.isHelpdesk;
        },
        isHelpdesk() {
            return this.taskType === "helpdesk";
        },
        taskUpdatedText() {
            if (!this.formInfo) return this.$t('task.task_updated')

            const map = {
                milestone: 'task.milestone_updated',
                stage: 'task.stage_updated',
                default: 'task.task_updated'
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
        saveBtnText() {
            if (!this.formInfo) return ''

            if (this.isHelpdesk) return this.$t('task.save')

            const prefix = this.edit ? 'save' : 'add'
            const map = {
                milestone: `task.${prefix}_milestone`,
                stage: `task.${prefix}_stage`,
                default: `task.${prefix}_task`
            }
            return this.$t(map[this.form.task_type] || map.default)
        },
        editDrawerTitle() {
            if (!this.formInfo) return ''

            if (this.isHelpdesk) {
                return this.$t(this.edit ? 'task.edit_appeal' : 'task.add_appeal')
            }

            const prefix = this.edit ? 'edit' : 'add'
            const map = {
                milestone: `task.${prefix}_milestone`,
                stage: `task.${prefix}_stage`,
                default: `task.${prefix}_task`
            }
            return this.$t(map[this.form.task_type] || map.default)
        },
        rules() {
            const rules = {};
            if (this.showInputPhone) {
                rules.tmp_phone = [
                    {
                        required: true,
                        message: this.$t("task.field_require"),
                        trigger: "blur",
                    },
                    {
                        max: 255,
                        message: this.$t("task.field_min_require"),
                        trigger: "blur",
                    },
                ];
                rules.workgroup = [
                    {
                        required: true,
                        message: this.$t("task.field_require"),
                        trigger: "blur",
                    },
                ];
            }

            rules.dead_line = this.formInfo?.dead_line?.rules || null
            rules.date_start_plan = this.formInfo?.date_start_plan?.rules || null
           
            return rules;
        },
        isMilestone() {
            return this.form?.task_type === "milestone"
        },
        isStage() {
            return this.form?.task_type === "stage"
        },
        tabs() {
            const addSetPriority = (this.isMilestone || this.isStage) ? 
                [] :
                [{
                    value: "set_priority",
                    label: this.$t("Set priority"),
                }]
            return [
                {
                    value: "add_user",
                    label: this.$t("Add user"),
                },
                {
                    value: "select_project",
                    label: this.$t("task.select_project_and_group"),
                },
                ...addSetPriority,
                {
                    value: "attach_files",
                    label: this.$t("Attach files"),
                }
            ]
        }
    },
    data() {
        return {
            invalidFields: [],
            SetPointsAsync: null,
            datesDonMatch: false,
            activeKey: [],
            userTypeTab: [
                {
                    value: "operator",
                    label: this.$t("Operator"),
                },
                // {
                //     value: "cooperator",
                //     label: this.$t("Cooperator"),
                // },
                {
                    value: "owner",
                    label: this.$t("Owner"),
                },
                {
                    value: "visors",
                    label: this.$t("Visors"),
                },
            ],
            activeTab: "add_user",
            activeUserTab: "operator",
            disableDraft: false,
            changeParentDisabled: false,
            formInfo: null,
            saveId: null,
            formLoading: false,
            taskDrawer: false,
            expandActive: 0,
            edit: false,
            back: false,
            isDraft: false,
            copy: false,
            formInject: null,
            priorityList,
            visibleActivity: false,
            loading: false,
            moreCreate: false,
            formCopy: false,
            pinFocus: false,
            subtask: false,
            fileList: [],
            open: false,
            form: Object.assign({}, formModel),
            startPointList: [],
            addressDrawerVisible: false,
            addressButtonLoading: false,
            defaultUserSelectId: "empty_task",
            contractSelectKey: Date.now(),
            taskTypeOptions: [
                { value: "stage", label: this.$t("Stage") },
                { value: "task", label: this.$t("Task") },
                { value: "milestone", label: this.$t("Milestone") },
            ],
        };
    },
    watch: {
        visible(val) {
            if (this.$route.query?.viewGroup || this.$route.query?.viewProject)
                this.$store.commit("task/SET_TASK_DRAWER_ZINDEX", 1010);

            if (val) {
                if (
          this.formDefault?.["task_type"] &&
          this.formInfoData?.[this.formDefault["task_type"]]
                ) {
                    if (this.form.task_type !== this.formDefault["task_type"]) {
                        this.form.task_type = this.formDefault["task_type"];
                    }
                    this.formInfo = this.formInfoData[this.formDefault["task_type"]];
                }
            }
            if (!val) eventBus.$emit("task_drawer_close");
        },
    },
    created() {
        setTimeout(() => {
            this.checkOpen();
        }, 600);
    },
    methods: {
        dateConfirm() {
            this.$confirm({
                title: this.$t('task.dates_don_match'),
                cancelText: this.$t('no'),
                okText: this.$t('yes'),
                onOk: async () => {
                    if(this.edit)
                        await this.submitEditTask()
                    else
                        await this.submitAddTask()
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
        async loadSetPoints() {
            if (this.SetPointsAsync) return
            const m = await import(/* webpackChunkName: "set-points", webpackPrefetch: false, webpackPreload: false */ './SetPoints')
            this.SetPointsAsync = m.default || m
            await this.$nextTick()
        },
        addressAfterVisibleChange(vis) {
            if(vis) {
                if (vis && !this.SetPointsAsync) this.loadSetPoints()
            }
        },
        opnUserSetting() {
            this.visible = false
            this.clearDraftForm()
            const query = JSON.parse(JSON.stringify(this.$route.query))
            query.my_profile = 'open'
            this.$router.push({query})
        },

        /*isDateOutOfLimit(date) {
            const momentStartDateLimit = this.$moment(this.startDateLimit)
            const momentDeadlineLimit = this.$moment(this.deadlineLimit)
            if (momentStartDateLimit.isValid() && momentDeadlineLimit.isValid()) {
                return !date.isBetween(momentStartDateLimit, momentDeadlineLimit, 'minute', '[]')
            }
            if (momentStartDateLimit.isValid()) {
                return date.isBefore(momentStartDateLimit)
            }
            if (momentDeadlineLimit.isValid()) {
                return date.isAfter(momentDeadlineLimit)
            }
            return false
        },*/
        changeTaskType() {
            this.validateFieldByName('dead_line')
            this.validateFieldByName('date_start_plan')
        },
        isValidDate(value) {
            return value && !isNaN(new Date(value).getTime())
        },
        selectTab(value) {
            if (value === this.activeTab) {
                this.activeTab = "";
                return;
            }
            this.activeTab = value;
        },
        changeMetadata({ key, value }) {
            this.$set(this.form.metadata, key, value);
        },
        openFileDrawer() {
            this.$refs.fileDrawer.openDrawer();
        },
        contractorHandler(contractor) {
            this.form.p_contractor_name = "";
            this.form.p_contractor_company = "";
            this.form.phone = contractor ? contractor.phone : "";
            this.form.email = contractor ? contractor.email : "";
        },
        customerCardHandler(customerCardId) {
            this.form.customer_card = customerCardId || null;
            if (customerCardId) {
                this.form.contractor = null;
                this.form.p_contractor_name = "";
                this.form.p_contractor_company = "";
            }
        },
        customerCardFullHandler(customerCard) {
            if (!customerCard) return;
            this.form.customer_card = customerCard;
        },
        onChange(val) {
            if (!val) {
                this.form.lead_source = null;
            }
        },
        getPopupContainer() {
            return this.$refs.tFormBody;
        },
        onClose() {
            this.disableDraft = false;
            this.changeParentDisabled = false;

            this.visible = false;
            this.$store.commit("task/SET_TASK_POINT_LIST", []);
            if(this.$refs?.taskForm)
                this.$refs.taskForm.resetFields();
        },
        async openAddressDrawer() {
            await this.$store.dispatch("task/getMapConfig").then(() => {
                this.$nextTick(() => {
                    this.addressDrawerVisible = true;
                });
            });
        },
        onCloseAddressDrawer() {
            this.$nextTick(() => {
                this.addressDrawerVisible = false;
            });
            if(this.$refs?.setPointRef)
                this.$refs.setPointRef.clearAll();
        },
        checkOldSelect(field) {
            if (typeof field.oldSelected === "boolean") {
                return field.oldSelected;
            } else return true;
        },
        setButtonLoading(value) {
            this.loading = value;
        },
        nameGenerator() {
            if (this.formInfo?.nameGenerate && !this.edit) {
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
                    this.formInfo = this.$store.getters["task/getFormInfoByType"](
                        this.form.task_type
                    );
                } catch (error) {
                    errorHandler({error})
                } finally {
                    this.formLoading = false;
                }
            }

            this.nameGenerator();
        },
        groupChange() {
            if (!this.form?.workgroup?.id) { return }
            this.requestReplaceVisors({ reason: 'group', id: this.form.workgroup.id })
        },
        resolveProjectId(project = null) {
            const targetProject = project || this.form?.project
            if (!targetProject) return null
            return typeof targetProject === 'object' ? targetProject.id || null : targetProject
        },
        getContractSelectApiUrl() {
            return '/customer_contracts/analytics_keys/by_project/'
        },
        getContractSelectParams() {
            const projectId = this.resolveProjectId()
            if (!projectId) return {}
            return { project: projectId }
        },
        selectProject(project) {
            /*this.form.parent = null;
            if (project?.control_dates) { 
                const hasChanges = this.setTaskDatesByLimits(this.form.project.date_start_plan, this.form.project.dead_line)
                if (hasChanges.startDate && hasChanges.deadline) {
                    this.$message.info(this.$t("task.task_dates_changed_project"));
                } else if (hasChanges.startDate) {
                    this.$message.info(this.$t("task.start_date_changed_project"));
                } else if (hasChanges.deadline) {
                    this.$message.info(this.$t("task.deadline_changed_project"));
                }
            }

            this.validateFieldByName('dead_line')
            this.validateFieldByName('date_start_plan')*/
            this.form.contract = null
            this.contractSelectKey = Date.now()

            const projectId = this.resolveProjectId(project)
            if (!projectId) { return }
            this.requestReplaceVisors({ reason: 'project', id: projectId })
            this.updateDatesMismatch()
        },
        setTaskDatesByLimits(before, after) {
            const hasChanges = { startDate: false, deadline: false }
            const momentBeforeLimit = this.$moment(before)
            const momentAfterLimit = this.$moment(after)
            const momentStartDate = this.$moment(this.startDate)
            const momentDeadline = this.$moment(this.deadline)
            if ((momentBeforeLimit.isValid() || momentAfterLimit.isValid())) {
                if (
                    momentStartDate.isValid() && 
                    momentStartDate.isAfter(momentAfterLimit) ||
                    momentStartDate.isBefore(momentBeforeLimit)) {
                    this.form.date_start_plan = before
                    hasChanges.startDate = true
                }
                if (
                    momentDeadline.isValid() && 
                    momentDeadline.isAfter(momentAfterLimit) ||
                    momentDeadline.isBefore(momentBeforeLimit)) {
                    this.form.dead_line = after
                    hasChanges.deadline = true
                }
            }

            return hasChanges
        },
        validateFieldByName(name) {
            this.$nextTick(() => {
                this.$refs.taskForm.validateField(name);
            })
        },
        selectParentTask(parentTask) {
            if (this.changeParentDisabled) { return }

            if (parentTask) { 
                const hasChanges = this.setTaskDatesByLimits(this.form.parent.date_start_plan, this.form.parent.dead_line)
                if (hasChanges.startDate && hasChanges.deadline) {
                    this.$message.info(this.$t("task.task_dates_changed_parent"));
                } else if (hasChanges.startDate) {
                    this.$message.info(this.$t("task.start_date_changed_parent"));
                } else if (hasChanges.deadline) {
                    this.$message.info(this.$t("task.deadline_changed_parent"));
                }
            } else {
                this.form.parent = null
            }

            this.validateFieldByName('dead_line')
            this.validateFieldByName('date_start_plan')

        },
        dateStartChange(date) {
            if (
                this.form.dead_line &&
                this.$moment(this.form.dead_line).isSameOrBefore(date)
            ) {
                this.form.date_start_plan = this.$moment(date).subtract({ hours: 1 });
            }
            this.updateDatesMismatch();
        },
        deadlineChange(date) {
            if (
                this.form.dead_line &&
                this.form.date_start_plan &&
                this.$moment(this.form.date_start_plan).isSameOrAfter(date)
            ) {
                this.form.date_start_plan = this.$moment(this.form.dead_line).subtract(1, 'hours');
            }
            this.updateDatesMismatch();
        },
        async afterVisibleChange(vis) {
            if (vis) {
                this.formInit();

                if (!this.edit) {
                    if(this.saveId)
                        this.saveId = null
                    await this.generateForm(true);
                }

                this.draftWatch();
            } else {
                this.$store.commit("task/SET_HARD_INDEX", null);
                eventBus.$emit(
          `drawer_select_drop_temp_state_${
            this.form.id || this.defaultUserSelectId
          }`
                );
                this.$store.state.task.pageName = null;
                this.formInfo = null;
                formWatch();
                this.datesDonMatch = false
                this.expandActive = 0;
                this.clearForm();
                if (this.back) {
                    this.back = false;
                    if(this.$route.query?.task === this.saveId) {
                        this.saveId = null
                        this.$store.commit("task/CHANGE_TASK_SHOW", true);
                    }
                }
            }
        },
        checkOpen() {
            if (this.$route.query?.createTask) {
                this.visible = true;
                let query = Object.assign({}, this.$route.query);
                delete query.createTask;
                this.$router.push({ query });
            }
        },
        reasonClear() {
            this.form.reason_model = null;
            this.form.reason = null;
        },
        close() {
            this.visible = false;
        },
        closeTaskSelected() {
            this.taskDrawer = false;
        },
        submitAndCopy() {
            this.formCopy = true;
            this.open = false;
            this.subtask = false;
            this.moreCreate = false;
            this.pinFocus = false;
            this.submit();
        },
        submitAndOpen() {
            this.open = true;
            this.formCopy = false;
            this.moreCreate = false;
            this.pinFocus = false;
            this.submit();
        },
        submitAndCreate() {
            this.moreCreate = true;
            this.open = false;
            this.subtask = false;
            this.formCopy = false;
            this.pinFocus = false;
            this.submit();
        },
        submitAndPinFocus() {
            this.moreCreate = false;
            this.open = false;
            this.subtask = false;
            this.formCopy = false;
            this.pinFocus = true;
            this.submit();
        },
        tabComponent(tabName) {
            if (!tabName) {
                return;
            }
            const components = {
                add_user: AddUser,
                select_project: SelectProject,
                set_priority: SetPriority,
                attach_files: AttachFiles,
            };
            return components[tabName];
        },
        draftWatch() {
            formWatch = this.$watch("form", {
                deep: true,
                handler() {
                    if (this.visible && !this.edit && !this.copy && !this.subtask) {
                        this.isDraft = true;
                        localStorage.setItem(
                            "task_create_form_draft",
                            JSON.stringify(this.form)
                        );
                    }
                },
            });
        },
        async generateForm(vis) {
            this.form.owner = {
                ...this.user,
                id: this.user.id,
                full_name: this.user.last_name + " " + this.user.first_name,
            };

            // TODO
            if (
        this.formDefault?.task_type &&
        this.form.task_type !== this.formDefault["task_type"]
            )
                this.form.task_type = this.formDefault.task_type;

            if (this.isFromOrder()) {
                this.form.task_type = "logistic";
                const { data } = await this.$http(
                    "app_info/select_list/?model=catalogs.DeliveryPointModel"
                );
                this.startPointList = data.selectList;
            }

            if (this.parentTask?.workgroup)
                this.form.workgroup = this.parentTask.workgroup;
            if (this.parentTask?.project)
                this.form.project = this.parentTask.project;
            if (this.parentTask?.dead_line)
                this.form.p_dead_line = this.parentTask.dead_line;

            const draftForm = JSON.parse(
                localStorage.getItem("task_create_form_draft")
            );
            if (draftForm && !this.edit && !this.copy && !this.disableDraft) {
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

            if (this.formInject)
                this.form = Object.assign(this.form, this.formInject);
            if (this.formDefault)
                this.form = Object.assign(
                    this.form,
                    JSON.parse(JSON.stringify(this.formDefault))
                );

            this.updateDatesMismatch()
            if (vis) await this.getFormInfo();
        },
        async clearDraftForm() {
            formWatch();
            this.isDraft = false;
            localStorage.removeItem("task_create_form_draft");
            this.form = Object.assign({}, formModel);
            this.form.visors = [];
            this.form.attachments = [];

            this.fileList = [];
            if(this.$refs?.taskForm)
                this.$refs.taskForm.resetFields();
            await this.generateForm();
            this.draftWatch();
        },
        checkPvhValid() {
            if (this.$refs["pvh_widget"]?.$refs?.["pvh_form"]) {
                return this.$refs["pvh_widget"].$refs["pvh_form"].partsCheck();
            } else return true;
        },
        openSubtaskSelection() {
            if (this.changeParentDisabled) {
                return;
            }
            this.taskDrawer = true;
        },
        async submitAddTask() {
            try {
                this.loading = true;
                const payload = this.pinFocus ? { ...this.form, pinned: true } : this.form;
                const res = await this.$store.dispatch("task/addTask", payload);
                if (res) {
                    if(this.form.reason_model && this.form.reason_model === 'comments' && this.form.reason_parent)
                        eventBus.$emit(`comment_task_added_${this.form.reason_parent}`, {
                            item: this.form.reason
                        })
                    if(this.form.reasonObject?.id) {
                        await this.$http.put(`/tasks/task/${res.id}/update_reason/`, {
                            reason:this.form.reasonObject.id
                        })
                    }
                    if (this.$store.hasModule('workplan')) {
                        this.$store.dispatch('workplan/reloadList', {
                            list: 'taskList'
                        })
                    }
                    if (res.project) {
                        this.$store.commit("projects/ADD_TABLE_ROW", {
                            record: res,
                            tableKey: "project_tasks",
                        });
                    }
                    if(this.form.isWorkPlan) {
                        eventBus.$emit('work_day_add_task', {
                            ...res,
                            planeIndex: this.form.planeIndex
                        })
                        delete this.form.isWorkPlan
                        if(this.formInject?.isWorkPlan)
                            delete this.formInject.isWorkPlan
                    }

                    const pvhForm = this.$refs["pvh_widget"]?.$refs?.["pvh_form"];
                    if (pvhForm) {
                        await pvhForm.createForm({
                            act: "save",
                            posted: false,
                            postedStatus: true,
                            injectId: res.id,
                        });
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
                    // Временный фикс
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

                    /*eventBus.$emit(`TASK_CREATED_${this.form.task_type}`, {
                                ...res,
                                formData: this.form,
                            });*/
                    eventBus.$emit(`update_filter_${this.pageName}`)
                    /*eventBus.$emit(`table_row_${this.pageName}`, {
                                action: "create",
                                row: res,
                            });*/

                    //eventBus.$emit('update_task_handler')
                    eventBus.$emit(`drawer_select_save_state_${this.form.id}`);

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
        submit() {
            if (this.loading) { return }
            this.$refs.taskForm.validate(async (valid, invalidFields) => {
                this.invalidFields = Object.keys(invalidFields);
                const pvhValid = this.checkPvhValid();
                if (valid && pvhValid) {
                    if(this.form.project) {
                        if (this.datesDonMatch)
                            this.dateConfirm()
                        else
                            await this.submitAddTask()
                    } else {
                        this.$confirm({
                            title: this.$t('task.project_no_selected'),
                            content: this.$t('task.project_no_selected_message'),
                            okText: this.$t('task.create_no_project'),
                            cancelText: this.$t('task.use_project'),
                            onOk: async () => {
                                await this.submitAddTask()
                            },
                            onCancel: () => {
                                this.$nextTick(() => {
                                    this.activeTab = 'select_project'
                                    this.activeKey = 'select_project'

                                    const scrollToRef = (ref) => {
                                        if (!ref) return false
                                        const el = ref.$el || ref
                                        let parent = el.parentNode
                                        while (parent && parent !== document.body) {
                                            const style = window.getComputedStyle(parent)
                                            const overflowY = style.overflowY
                                            if ((overflowY === 'auto' || overflowY === 'scroll') && parent.scrollHeight > parent.clientHeight) break
                                            parent = parent.parentNode
                                        }
                                        if (!parent || parent === document.body) return false
                                        const rectEl = el.getBoundingClientRect()
                                        const rectParent = parent.getBoundingClientRect()
                                        const offset = rectEl.top - rectParent.top + parent.scrollTop
                                        parent.scrollTop = Math.max(0, Math.floor(offset - 20))
                                        return true
                                    }

                                    setTimeout(() => {
                                        if(!this.isMobile && this.$refs.descTab)
                                            scrollToRef(this.$refs.descTab)
                                        if(this.isMobile && this.$refs.mobCollapse)
                                            scrollToRef(this.$refs.mobCollapse)
                                        
                                        if(this.$refs['tab_comp_1']?.[0])
                                            this.$refs['tab_comp_1'][0].projectSelect()
                                        if(this.$refs['collapse_comp_1']?.[0])
                                            this.$refs['collapse_comp_1'][0].projectSelect()
                                    }, 300)
                                })
                            }
                        })
                    }
                } else {
                    if (!pvhValid) this.expandActive = "2";
                    this.$message.warning(this.$t("task.field_require_all"));
                    return false;
                }
            });
        },
        async submitEditTask() {
            try {
                this.loading = true;
                const res = await this.$store.dispatch(
                    "task/updateTask",
                    this.form
                );
                if (res) {
                    if(this.form.reasonObject?.id) {
                        await this.$http.put(`/tasks/task/${res.id}/update_reason/`, {
                            reason: this.form.reasonObject.id
                        })
                    } else {
                        if(this.form.reason) {
                            await this.$http.put(`/tasks/task/${res.id}/update_reason/`, {
                                reason: null
                            })
                        }
                    }
                    if (this.$store.hasModule('workplan')) {
                        this.$store.dispatch('workplan/updateItem', {
                            item: res,
                            list: 'taskList'
                        })
                    }
                    if (res.project) {
                        this.$store.commit("projects/UPDATE_TABLE_ROW", {
                            record: res,
                            tableKey: "project_tasks",
                        });
                    }

                    const pvhForm = this.$refs["pvh_widget"]?.$refs?.["pvh_form"];
                    if (pvhForm) {
                        await pvhForm.updateForm({
                            act: "save",
                            posted: false,
                            postedStatus: true,
                            injectId: res.id,
                        });
                    }

                    this.$message.success(this.taskUpdatedText);
                    eventBus.$emit(`UPDATE_TEXT_VIEWER`);
                    //eventBus.$emit('update_task_handler')

                    eventBus.$emit(`update_filter_${this.pageName}`)
                    /*eventBus.$emit(`table_row_${this.pageName}`, {
                                    action: "update",
                                    row: res,
                                });*/
                    this.visible = false;
                    this.clearForm();
                }
            } catch (error) {
                errorHandler({error})
            } finally {
                this.loading = false;
            }
        },
        update() {
            if (!this.loading) {
                this.$refs.taskForm.validate(async (valid) => {
                    const pvhValid = this.checkPvhValid();
                    if (valid && pvhValid) {
                        if (this.datesDonMatch) {
                            this.dateConfirm()
                        } else {
                            await this.submitEditTask()
                        }
                    } else {
                        if (!pvhValid) this.expandActive = "2";
                        this.$message.warning(this.$t("task.field_require_all"));
                        return false;
                    }
                });
            }
        },
        clearForm() {
            this.isDraft = false;
            this.formInject = null;

            if (this.task && !this.back) {
                if(this.form?.id === this.$route.query?.task)
                    this.$store.commit("task/SET_TASK", null)
            }

            if (this.formDefault) this.$store.commit("task/SET_FORM_DEFAULT", null);

            if (!this.formCopy) {
                this.form = JSON.parse(JSON.stringify(formModel))
                this.form.visors = [];
                this.form.cooperators = [];
                this.form.prerequisites = [];
                this.form.attachments = [];
                this.fileList = [];
                this.contractSelectKey = Date.now()
                if(this.$refs?.taskForm)
                    this.$refs.taskForm.resetFields();
                this.generateForm();
            }

            this.formCopy = false;
            this.edit = false;
            this.copy = false;
            this.open = false;
            this.moreCreate = false;
            this.pinFocus = false;
        },
        updateForm({ key, data }) {
            this.back = false;
            this.formInject = {
                [key]: data,
            };
        },
        async setEdit({ back, task_type }) {
            this.edit = true;
            this.back = back;
            this.isDraft = false;
            this.saveId = JSON.parse(JSON.stringify(this.task.id));
            let editForm = JSON.parse(JSON.stringify(this.task));
            if (editForm.cooperators?.length) {
                editForm.cooperators = editForm.cooperators.map((item) => item.user);
            }

            if (task_type && this.form.task_type !== task_type) {
                editForm.task_type = task_type;
            }

            if (editForm.attachments.length) {
                editForm.attachments.forEach((file) => {
                    this.fileList.push({
                        uid: file.id,
                        name: file.path,
                        status: "done",
                        url: file.path,
                    });
                });
            }

            if (editForm.parent?.dead_line || editForm.project?.dead_line) {
                const dead_line = checkDateDeadLine(editForm, "dead_line");
                editForm.r_dead_line_from = dead_line;
                editForm.p_dead_line_from = dead_line;
            }

            if (editForm.parent?.date_start_plan || editForm.project?.date_start_plan)
                editForm.s_dead_line_from = checkDate(editForm, "date_start_plan");

            if (editForm.parent || editForm.attachments?.length)
                this.expandActive = 1;
            if(editForm.reason?.id && editForm.reason.type === 'help_desk.HelpDeskTicketModel')
                editForm.reasonObject = editForm.reason
            this.form = editForm;
            this.visible = true;
            this.getFormInfo();
        },
        formInit() {
            if (!this.form?.task_type) {
                this.form.task_type = this.taskType;
            }
        },
        isFromOrder() {
            return this.form.reason_model === "order";
        },
        async getParentById(id) {
            const params = {
                task_type: "task,stage,milestone",
                filters: { id: id },
            };

            return await this.$http.get("tasks/task/list", { params });
        },
    },
    mounted() {
        eventBus.$on("ADD_WATCH", async ({ type = null, data, key = null }) => {
            this.isDraft = false;
            if (key) {
                this.updateForm({ key, data });
                if (key === "parent" || key === "workgroup" || key === "project")
                    this.expandActive = 1;
            }
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
                    };

                    if(data.reason?.id && data.reason.type === 'help_desk.HelpDeskTicketModel')
                        subtask.reasonObject = data.reason

                    this.formInject = Object.assign({}, subtask);
                    this.expandActive = 1;
                } else if (type === "copy") {
                    this.copy = true;
                    let copy = { ...data };

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
                    if(data.reason?.id && data.reason.type === 'help_desk.HelpDeskTicketModel')
                        copy.reasonObject = data.reason
                    this.form = JSON.parse(JSON.stringify(copy))
                    this.expandActive = 1;
                } else if (type === "add_task") {
                    let form = Object.assign({}, data);
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

                    if (data.parent && !data.parent.id) {
                        try {
                            const response = await this.getParentById(data.parent);
                            form.parent = response.data.results[0];
                        } catch (error) {
                            errorHandler({error})
                            form.parent = null;
                        }
                    }
                    // if

                    this.form = Object.assign(this.form, form);
                    this.disableDraft = true;
                    /*if(form.reason_model === 'order') {
                        this.form.task_type = 'logistic'
                    }*/

                    this.expandActive = 1;
                }
            }
            this.visible = true;
        });
        eventBus.$on("EDIT_TASK", ({ back, task_type }) => {
            this.setEdit({ back, task_type });
        });
    },
    beforeDestroy() {
        eventBus.$off("EDIT_TASK");
        eventBus.$off("ADD_WATCH");
    },
};
</script>

<style lang="scss">
.draft_task {
  border: 0px;

  .anticon {
    vertical-align: 0;
  }
}

.task_edit {
  &:not(.mobile_task_edit) {
    .d_body {
      padding: 30px;
    }
  }

  .auction_btn {
    height: 46px;
  }

  .ant-drawer-wrapper-body,
  .ant-drawer-content {
    overflow: hidden;
  }

  .ant-drawer-body {
    height: calc(100% - 40px);
    padding: 0px;
  }

  .ant-drawer-header {
    padding-left: 30px;
    padding-right: 30px;
  }

  .d_body {
    height: calc(100% - 50px);
    overflow-y: auto;
    overflow-x: hidden;

    .task_form_wrap {
      .ck-editor__editable {
        max-height: 300px;
      }
    }
  }

  .d_footer {
    display: flex;
    align-items: center;
    height: 50px;
    border-top: 1px solid #e8e8e8;
    padding-left: 30px;
    padding-right: 30px;

    .save_btn {
      margin-right: 5px;
    }
  }

  .operator {
    .ant-form-item-children {
      display: flex;
    }
  }
}

.mobile_task_edit {
  .ant-drawer-header {
    padding-left: 15px;
    padding-right: 15px;
  }

  .d_body {
    height: calc(100% - 48px);

    .task_form_wrap {
      padding: 15px;
    }
  }

  .d_footer {
    padding-left: 15px;
    padding-right: 15px;
    height: 48px;

    .dots_btn {
      width: 55px;
    }
  }
}

.make_event {
  display: flex;
  align-items: center;
}

.tab-panel {
  padding: 15px;
  padding-top: 20px;
  padding-bottom: 25px;
  background-color: #fafafa;
  border-radius: 8px;
}
</style>

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
.description_row{
    &::v-deep{
        .ck-editor__top{
            position: sticky !important;
            top: -20px !important;
            background: white !important;
            z-index: 999999;
        }
    }
}
::v-deep {
  .collapse {
    border-radius: 0;
    background: transparent;

    .ant-collapse-content-box {
      padding: 2px;
      padding-bottom: 30px;
    }

    .ant-collapse-item {
      border: 0;
    }
    .ant-form-item{
        margin-bottom: 15px;
    }
    .ant-collapse-header{
        background: #f7f9fc;
        border-radius: 8px;
    }
  }

  .mobile-tab {
    border-radius: 8px;
    .ant-collapse-content-box {
      padding-top: 0;
    }

    .ant-collapse-item {
      border: 0;
    }
  }

  .ant-form-item {
    margin-bottom: 10px;

    @media (min-width: 900px) {
      margin-bottom: 24px;
    }
  }
}

.tabs {
  display: none;

  @media (min-width: 900px) {
    display: flex;
  }
}

.mobile-tabs {
  display: grid;
  gap: 10px;

  @media (min-width: 900px) {
    display: none;
  }
}

.desctop-tab {
  display: none;

  @media (min-width: 900px) {
    display: block;
  }
}

.mobile-tab {
  min-width: 0;
  background-color: #f7f9fc;
}

.mobile-tabs__divider {
  border-top: 1px solid #f1eeee;
}

.button-light:not(.ant-btn-primary) {
  background: #f0f9fe;
  border: 1px solid #f0f9fe;
}

.button-gray {
  background: #1c65c01a;
}

.button-light.button_error,
.button-gray.button_error {
  border: 1px solid #f5222d;
  background-color: transparent;
  color: #f5222d;
}
</style>
