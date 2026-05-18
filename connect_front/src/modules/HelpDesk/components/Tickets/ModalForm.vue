<template>
    <a-modal
        :width="modalWidth"
        :afterClose="afterClose"
        :visible="visible"
        destroyOnClose
        :maskClosable="false"
        @afterVisibleChange="afterVisibleChange"
        :wrapClassName="modalWrapClass"
        :dialogStyle="modalDialogStyle"
        :bodyStyle="modalBodyStyle"
        @cancel="visible = false">
        <template #title>
            <div class="flex items-center justify-between">
                <span>{{ $t('helpdesk.create_appeal') }}</span>
                <HelpButton partCode="helpdesk" class="ml-2" />
            </div>
        </template>

        <a-form-model
            ref="ruleForm"
            :model="form"
            :label-col="formLabelCol"
            :wrapper-col="formWrapperCol"
            class="mini_form"
            :rules="rules">

            <a-form-model-item
                class="mt-2"
                ref="description"
                :wrapper-col="{ span: 24 }"
                prop="description">
                <div class="w-full description_editor bg-neutral-1 z-10 relative px-4 py-3 rounded-xl">
                    <component
                        v-if="editorGate"
                        :is="ckEditor"
                        ref="editorRef"
                        initFocus
                        :taskId="form.id || null"
                        :placeholder="$t('helpdesk.description')"
                        :key="visible"
                        v-model="form.description"/>
                </div>
            </a-form-model-item>

            <a-form-model-item
                ref="customer_card"
                :label="$t('helpdesk.organization')"
                class="form-row flex items-center h-9"
                :class="{ 'form-row--mobile': isMobile }"
                prop="customer_card">
                <ListViewModal
                    endpoint="help_desk/customer_cards/"
                    tableType="clients"
                    pageName="helpdesk_clients_all"
                    :title="$t('helpdesk.contractor_name')"
                    model="help_desk.CustomerCardModel"
                    @select="selectClient"
                    :add="addClientNoReturn"
                    ref="listViewModalClientsRef"/>
                <DSelect
                    v-model="form.customer_card"
                    apiUrl="/app_info/filtered_select_list/?model=help_desk.CustomerCardModel"
                    class="w-full"
                    :showAllHandler="showAllClientsHandler"
                    ref="contact_person_select"
                    infinity
                    size="default"
                    :disabled="disabled_massage"
                    resultsKey="filteredSelectList"
                    inputType="ghost"
                    showSearch
                    initList
                    :initOptionList="initListClient"
                    :useOptionFlex="false"
                    useSearchApi
                    :selectUID="clientUUID"
                    :placeholder="$t('helpdesk.assign_contractor_placeholder')"
                    searchKey="search"
                    labelKey="string_view"
                    :listObject="false"
                    :default-active-first-option="false"
                    :filter-option="false"
                    :not-found-content="null"
                    @select="selectClientId"
                    @change="changeCustomerCard()">
                    <template #suffixSlot>
                        <a-spin v-if="getClientLoading" size="small" />
                        <a-button
                            v-else
                            type="ui"
                            ghost
                            shape="circle"
                            size="small"
                            flaticon
                            v-tippy
                            :content="$t('helpdesk.add_contractor')"
                            icon="fi-rr-user-add"
                            @click="addClient()"/>
                    </template>
                </DSelect>
            </a-form-model-item>

            <transition name="slide-fade">
                <a-form-model-item
                    v-if="form.customer_card"
                    ref="work_contour"
                    :label="$t('helpdesk.work_contour')"
                    class="form-row flex items-center h-9"
                    :class="{ 'form-row--mobile': isMobile }"
                    prop="analytics_key">
                    <ContractSelect
                        :key="`helpdesk_contract_select_${contractSelectKey}_${form.customer_card || 'empty'}`"
                        v-model="form.analytics_key"
                        class="w-full"
                        :apiUrl="contractSelectApiUrl"
                        :params="contractSelectParams"
                        listObject="filteredSelectList"
                        inputType="ghost"
                        size="default"
                        :title="$t('helpdesk.work_contour')"
                        valueKey="id"
                        labelKey="string_view"
                        searchKey="search"
                        :showIcon="false"
                        :showSearch="true"
                        :showRecent="false"
                        :showClear="true"
                        :showArrow="true"
                        :initList="Boolean(form.customer_card)"
                        :useSearchApi="false"
                        :disabled="!form.customer_card"
                        :placeholder="$t('helpdesk.select_work_contour')" />
                </a-form-model-item>
            </transition>

            <transition name="slide-fade">
                <a-form-model-item
                    v-if="form.customer_card"
                    ref="contact_person"
                    :label="$t('helpdesk.contact_person')"
                    class="form-row flex items-center h-9"
                    :class="[{ 'contact_person': !form.contact_person }, { 'form-row--mobile': isMobile }]"
                    prop="contact_person">
                    <ListViewModal
                        :endpoint="contactPersonEndpoint"
                        tableType="contact_person"
                        :title="$t('helpdesk.contact_persons')"
                        pageName="helpdesk_contact_person_all"
                        model="help_desk.ContactPersonModel"
                        @select="selectContactPerson"
                        :add="addContact"
                        @close="getSLA"
                        ref="listViewModalConctactPersonRef">
                        <template v-slot:headerLeft="{ rowSelected }">
                            <SLASelect
                                v-if="rowSelected"
                                :selectItem="rowSelected"
                                :params="{ contractor: orgAdminClient }"
                                pageName="helpdesk_contact_person_all"
                                model="help_desk.ContactPersonModel" />
                        </template>
                    </ListViewModal>

                    <DSelect
                        :key="form.customer_card + personKey"
                        v-model="form.contact_person"
                        :apiUrl="contactPersonEndpoint"
                        class="w-full"
                        :selectUID="contactUUID"
                        infinity
                        :useOptionFlex="false"
                        :disabled="(form.customer_card ? false : true) || disabled_massage"
                        size="default"
                        inputType="ghost"
                        :showAllHandler="showAllContactPersonsHandler"
                        :initOptionList="initListConctactPerson"
                        showSearch
                        useSearchApi
                        showPlaceholder
                        :placeholder="$t('helpdesk.assign_contractor')"
                        searchKey="search"
                        labelKey="name"
                        :listObject="false"
                        :default-active-first-option="false"
                        :filter-option="false"
                        :not-found-content="null"
                        @change="getSLA()"
                        @changeFull="changeFullPerson">
                        <template #suffixSlot>
                            <div class="flex items-center gap-2">
                                <a-button
                                    v-if="form.contact_person && fullPerson"
                                    type="ui"
                                    ghost
                                    shape="circle"
                                    size="small"
                                    flaticon
                                    v-tippy
                                    :content="$t('helpdesk.edit_contact_person')"
                                    icon="fi-rr-user-pen"
                                    @click="editContact()"/>
                                <a-button
                                    type="ui"
                                    ghost
                                    shape="circle"
                                    size="small"
                                    flaticon
                                    :disabled="form.customer_card ? false : true"
                                    v-tippy
                                    :content="$t('helpdesk.add_contact_person')"
                                    icon="fi-rr-user-add"
                                    @click="addContact()"/>
                            </div>
                        </template>
                    </DSelect>

                    <ContactModal
                        v-if="visible"
                        slaSelect
                        :contractor="orgAdminClient"
                        @change="getSLA()" />
                </a-form-model-item>
            </transition>

            <transition name="slide-fade">
                <a-form-model-item
                    v-if="form.customer_card"
                    ref="specialist"
                    :label="$t('helpdesk.responsible')"
                    class="form-row flex items-center h-9"
                    :class="{ 'form-row--mobile': isMobile }"
                    prop="specialist">
                    <UserMiniSelect
                        v-model="form.specialist"
                        inputType="input"
                        :showIcon="false"
                        :key="form.customer_card"
                        :apiUrl="`/help_desk/customer_cards/${form.customer_card}/specialists/actual/?display=user`"
                        :disabled="(form.customer_card ? false : true) || disabledSpecialist"
                        :storeName="
                            form.customer_card
                                ? `${form.customer_card}_user_select`
                                : 'users_mini_select_empty'
                        "
                        placement="bottomLeft"
                        :placeholder="$t('helpdesk.select_responsible')">
                        <template #item="{ work }">
                            <div>
                                <a-avatar :size="20" icon="team" :src="work.avatar ? work.avatar.path : null" />
                            </div>
                            <div class="ml-2 truncate">
                                <div class="truncate">{{ work.full_name }}</div>
                                <div
                                    class="truncate gray lowercase"
                                    style="font-size: 10px;line-height: 12px;">
                                    {{ work.is_reserve ? $t('helpdesk.is_reserve') : $t('helpdesk.is_reserve_main') }}
                                </div>
                            </div>
                        </template>
                    </UserMiniSelect>
                </a-form-model-item>
            </transition>

            <a-form-model-item
                ref="visors"
                :label="$t('helpdesk.observers')"
                class="form-row flex items-center h-9"
                :class="{ 'form-row--mobile': isMobile }"
                prop="visors">
                <UserDrawer
                    v-model="form.visors"
                    :taskId="ticket ? ticket.id : null"
                    :id="ticket ? ticket.id : defaultUserSelectId"
                    inputType="ghost"
                    :metadata="{ key: 'visors', value: form.metadata }"
                    :changeMetadata="changeMetadata"
                    multiple
                    :title="$t('helpdesk.select_observers')"
                    :inputPlaceholder="$t('helpdesk.assign_observers')"
                    class="w-full user-drawer"/>
            </a-form-model-item>

            <a-form-model-item
                ref="category"
                :label="$t('helpdesk.category')"
                class="form-row flex items-center h-9"
                :class="{ 'form-row--mobile': isMobile }"
                prop="category">
                <ListViewModal
                    :endpoint="categoryEndpoint"
                    tableType="helpdesk_categories"
                    :title="$t('helpdesk.category')"
                    pageName="helpdesk_categories_all"
                    model="help_desk.HelpDeskTicketCategoryModel"
                    @select="selectCategory"
                    @close="getSLA"
                    :add="actionInfo?.create_category && createCategory"
                    ref="listViewModalCategoriesRef">
                    <template v-slot:headerLeft="{ rowSelected }">
                        <SLASelect
                            v-if="rowSelected"
                            :selectItem="rowSelected"
                            :params="{ contractor: orgAdminClient }"
                            pageName="helpdesk_categories_all"
                            model="help_desk.HelpDeskTicketCategoryModel" />
                    </template>
                </ListViewModal>

                <ModalCategoryCreate
                    v-if="orgAdminClient"
                    ref="modalCategoryCreateRef"
                    model="help_desk.HelpDeskTicketCategoryModel"
                    slaSelect
                    :afterCreate="afterCreateCategory"
                    :contractor="orgAdminClient" />

                <DSelect
                    ref="selectCategoryRef"
                    v-model="form.category"
                    :apiUrl="categoryEndpoint"
                    class="w-full"
                    oneSelect
                    :showAllHandler="showAllCategoriesHandler"
                    infinity
                    :initList="false"
                    :disabled="!orgAdminClient"
                    showSearch
                    size="default"
                    inputType="ghost"
                    :initOptionList="initListCategory"
                    :placeholder="$t('helpdesk.select_category')"
                    :listObject="false"
                    labelKey="name"
                    valueKey="id"
                    :default-active-first-option="false"
                    :filter-option="false"
                    :not-found-content="null"
                    @change="getSLA()">
                    <!-- ✅ ВМЕСТО "ПОКАЗАТЬ ВСЕ" -> кнопки Создать / Редактировать -->
                    <template #suffixSlot>
                        <div class="flex items-center gap-2">
                            <a-button
                                v-if="form.category && actionInfo?.edit_category"
                                type="ui"
                                ghost
                                shape="circle"
                                size="small"
                                flaticon
                                v-tippy
                                content="Редактировать категорию"
                                icon="fi-rr-user-pen"
                                :disabled="!orgAdminClient"
                                @click="editCategory()">
                            </a-button>

                            <a-button
                                v-if="actionInfo?.create_category"
                                type="ui"
                                ghost
                                shape="circle"
                                size="small"
                                :disabled="!orgAdminClient"
                                flaticon
                                v-tippy
                                content="Добавить категорию"
                                icon="fi-rr-add"
                                @click="createCategory()">
                            </a-button>
                        </div>
                    </template>
                </DSelect>
            </a-form-model-item>

            <a-form-model-item
                ref="receipt_date"
                :label="$t('helpdesk.receipt_date')"
                class="form-row flex items-center h-9"
                :class="{ 'form-row--mobile': isMobile }"
                prop="receipt_date">
                <div class="flex items-center justify-between calendar-widget w-full">
                    <a-date-picker
                        v-model="form.receipt_date"
                        inputType="ghost"
                        :showTime="{ format: 'HH:mm' }"
                        format="DD.MM.YYYY HH:mm"
                        :getCalendarContainer="getCalendarContainer"
                        class="w-full"
                        :placeholder="$t('helpdesk.receipt_date')"
                        showToday>
                        <template #renderExtraFooter>
                            <div class="dp-shortcuts mt-1" style="display:flex;flex-wrap:wrap;gap:6px;">
                                <a-button
                                    v-for="item in quickShortcuts"
                                    :key="item.key"
                                    size="small"
                                    type="ui"
                                    :title="item.title"
                                    @click="setReceiptDateFromShortcut(item.moment)">
                                    {{ item.label }}
                                </a-button>
                            </div>
                        </template>
                    </a-date-picker>
                </div>
            </a-form-model-item>

            <a-form-model-item
                ref="dead_line"
                :label="$t('helpdesk.deadline')"
                class="form-row flex items-center h-9"
                :class="{ 'form-row--mobile': isMobile }"
                prop="dead_line">
                <div class="flex items-center justify-between calendar-widget w-full">
                    <a-date-picker
                        ref="deadlinePicker"
                        v-model="form.dead_line"
                        inputType="ghost"
                        :showTime="{ defaultValue: defaultDeadlineTime, format: 'HH:mm' }"
                        format="DD.MM.YYYY HH:mm"
                        :getCalendarContainer="getCalendarContainer"
                        class="w-full"
                        showToday
                        :placeholder="$t('helpdesk.specify_deadline')"
                        @change="handleDeadlineChange">
                        <template #renderExtraFooter>
                            <div class="dp-shortcuts mt-1" style="display:flex;flex-wrap:wrap;gap:6px;">
                                <a-button
                                    v-for="item in quickShortcuts"
                                    :key="item.key"
                                    size="small"
                                    type="ui"
                                    :title="item.title"
                                    @click="setDeadlineFromShortcut(item.moment)">
                                    {{ item.label }}
                                </a-button>
                            </div>
                        </template>
                    </a-date-picker>
                </div>
            </a-form-model-item>

            <a-form-model-item
                ref="priority"
                :label="$t('helpdesk.priority')"
                class="form-row flex items-center h-9"
                :class="{ 'form-row--mobile': isMobile }"
                prop="priority">
                <div class="priority_picker flex items-center gap-2">
                    <div
                        v-for="(item, index) in priorityList"
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
            </a-form-model-item>

            <a-spin class="w-full" :spinning="slaLoading" size="small">
                <transition name="slide-fade">
                    <component v-if="slaInfo" :is="ModalFormSLA" :sla="slaInfo" />
                </transition>
            </a-spin>
        </a-form-model>

        <template #footer>
            <div
                class="flex gap-1 items-center"
                :class="{ 'modal-footer--mobile': isMobile }"
                ref="modal_footer">

                <!-- ===== MOBILE (как в примере: кнопка + точки -> ActivityDrawer) ===== -->
                <template v-if="isMobile">
                    <div class="flex items-center w-full">
                        <div class="w-full">
                            <a-button
                                type="primary"
                                block
                                size="large"
                                :loading="loading"
                                @click="formSubmit()">
                                {{ $t('helpdesk.create_and_close') }}
                            </a-button>
                        </div>
                        <div>
                            <a-button
                                type="primary"
                                :disabled="loading"
                                size="large"
                                class="ml-1 dots_btn"
                                flaticon
                                icon="fi-rr-menu-dots-vertical"
                                @click="openFooterDrawer" />
                        </div>



                    </div>
                    <ActivityDrawer v-model="footerDrawerVisible">
                        <ActivityItem
                            v-if="loading"
                            key="menu_loader">
                            <div class="w-full flex justify-center">
                                <a-spin size="small" />
                            </div>
                        </ActivityItem>

                        <template v-else>
                            <ActivityItem
                                v-for="item in footerMenuItems"
                                :key="item.key"
                                @click="item.handler">
                                <i class="fi mr-2" :class="item.icon"></i>
                                <span :style="item.style || null">{{ item.label }}</span>
                            </ActivityItem>
                        </template>
                    </ActivityDrawer>
                </template>

                <!-- ===== DESKTOP (оставил как было: dropdown) ===== -->
                <template v-else>
                    <a-dropdown :getPopupContainer="() => $refs.modal_footer">
                        <a-button
                            type="primary"
                            size="large"
                            class="flex items-center"
                            :loading="loading"
                            @click="formSubmit()">
                            {{ $t('helpdesk.create_and_close') }}
                            <i class="fi fi-rr-angle-small-down ml-2" />
                        </a-button>

                        <a-menu slot="overlay">
                            <a-menu-item class="flex items-center" @click="formSubmit({create_more: true})">
                                <i class="fi fi-rr-add mr-2" />
                                {{ $t('helpdesk.create_and_create') }}
                            </a-menu-item>
                            <a-menu-item class="flex items-center" @click="formSubmit({is_open: true})">
                                <i class="fi fi-rr-redo mr-2" />
                                {{ $t('helpdesk.create_and_open') }}
                            </a-menu-item>
                            <template v-if="isUser">
                                <a-menu-item
                                    class="flex items-center"
                                    style="color: #722ed1;"
                                    @click="formSubmit({in_work: true})">
                                    <i class="fi fi-rr-play mr-2" />
                                    {{ $t('helpdesk.create_and_run') }}
                                </a-menu-item>
                                <a-menu-item
                                    class="flex items-center"
                                    style="color: #368225;"
                                    @click="formSubmit({in_complete: true})">
                                    <i class="fi fi-rr-check-circle mr-2" />
                                    {{ $t('helpdesk.create_and_completed') }}
                                </a-menu-item>
                            </template>
                        </a-menu>
                    </a-dropdown>

                    <a-button
                        type="ui_ghost"
                        ghost
                        size="large"
                        @click="visible = false">
                        {{ $t('helpdesk.cancel') }}
                    </a-button>
                </template>
            </div>
        </template>
    </a-modal>
</template>

<script>
import eventBus from "@/utils/eventBus";
import priorityMixin from "../../priorityMixin.js";
import { v1 as uuidv1 } from "uuid";
import { errorHandler } from "@/utils/index.js";
import moment from "moment";
import { ActivityItem, ActivityDrawer } from "@/components/ActivitySelect";

const createDefaultForm = () => ({
    metadata: { visors: [] },
    name: "",
    in_work: false,
    receipt_date: moment(),
    specialist: null,
    category: null,
    dead_line: null,
    description: "",
    visors: [],
    priority: 0,
    status: null,
    customer_card: null,
    contact_person: null,
    analytics_key: null,
});

export default {
    mixins: [priorityMixin],
    components: {
        SLASelect: () => import("../SLASelect.vue"),
        UserDrawer: () => import("@apps/DrawerSelect/index.vue"),
        DSelect: () => import("@apps/DrawerSelect/Select.vue"),
        ContractSelect: () => import("@apps/DrawerSelect/ContractSelect.vue"),
        ContactModal: () => import("../ContactModal.vue"),
        UserMiniSelect: () => import("@apps/DrawerSelect/UserMiniSelect.vue"),
        ListViewModal: () => import("@/components/ListView/ListViewModal.vue"),
        ModalCategoryCreate: () => import("../ModalCategoryCreate.vue"),
        HelpButton: () => import("@apps/Support/components/HelpButton.vue"),
        ActivityItem,
        ActivityDrawer,
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile;
        },
        showAllClientsHandler() {
            return this.isMobile ? false : this.openAllClients;
        },
        showAllContactPersonsHandler() {
            return this.isMobile ? false : this.openAllConctactPersons;
        },
        showAllCategoriesHandler() {
            return this.isMobile ? false : this.openAllCategories;
        },

        // ===== MOBILE MODAL SETTINGS =====
        modalWidth() {
            return this.isMobile ? "100%" : 675;
        },
        modalWrapClass() {
            return `ticket_form_modal body_top_pd${this.isMobile ? " ticket_form_modal--mobile" : ""}`;
        },
        modalDialogStyle() {
            if (!this.isMobile) return {};
            return {
                top: "0px",
                margin: "0px",
                maxWidth: "100vw",
                paddingBottom: "0px",
            };
        },
        modalBodyStyle() {
            if (!this.isMobile) return {};
            return {
                padding: "12px",
                overflow: "auto",
            };
        },
        formLabelCol() {
            return this.isMobile
                ? { span: 24, style: { textAlign: "left" } }
                : { span: 6, style: { textAlign: "left" } };
        },
        formWrapperCol() {
            return this.isMobile ? { span: 24 } : { span: 18 };
        },
        // =================================

        // ===== MOBILE FOOTER MENU (ActivityDrawer) =====
        footerMenuItems() {
            const items = [
                {
                    key: "create_more",
                    icon: "fi-rr-add",
                    label: this.$t("helpdesk.create_and_create"),
                    handler: () => this.runFooterAction({ create_more: true }),
                },
                {
                    key: "is_open",
                    icon: "fi-rr-redo",
                    label: this.$t("helpdesk.create_and_open"),
                    handler: () => this.runFooterAction({ is_open: true }),
                },
            ];

            if (this.isUser) {
                items.push(
                    {
                        key: "in_work",
                        icon: "fi-rr-play",
                        label: this.$t("helpdesk.create_and_run"),
                        style: "color:#722ed1;",
                        handler: () => this.runFooterAction({ in_work: true }),
                    },
                    {
                        key: "in_complete",
                        icon: "fi-rr-check-circle",
                        label: this.$t("helpdesk.create_and_completed"),
                        style: "color:#368225;",
                        handler: () => this.runFooterAction({ in_complete: true }),
                    }
                );
            }

            return items;
        },
        // ===============================================

        quickShortcuts() {
            const items = [
                { key: "tomorrow", label: this.$t("task.date_tomorrow"), make: () => this.$moment().add(1, "day") },
                { key: "end_week", label: this.$t("task.date_end_week"), make: () => this.$moment().endOf("isoWeek") },
                { key: "plus_week", label: this.$t("task.date_plus_week"), make: () => this.$moment().add(1, "week") },
                { key: "end_month", label: this.$t("task.date_end_month"), make: () => this.$moment().endOf("month") },
            ];

            return items.map((it) => {
                const m = this.applyDefaultTime(it.make());
                const title = this.tooltipFormat(m);
                return { ...it, moment: m, title };
            });
        },
        categoryEndpoint() {
            return `help_desk/ticket_categories/?contractor=${this.orgAdminClient}`;
        },
        contactPersonEndpoint() {
            return `help_desk/customer_cards/${this.form.customer_card}/contact_persons/`;
        },
        contractSelectApiUrl() {
            return "/customer_contracts/analytics_keys/";
        },
        contractSelectParams() {
            if (!this.form.customer_card) return {};
            return {
                customer_card: this.form.customer_card
            };
        },
        ckEditor() {
            if (this.visible) return () => import("@apps/CKEditor");
            return null;
        },
        ModalFormSLA() {
            if (this.slaInfo) return () => import("./ModalFormSLA.vue");
            return null;
        },
        user() {
            return this.$store.state.user.user;
        },
        isUser() {
            return this.form.specialist?.id === this.user?.id;
        },
    },
    data() {
        return {
            model: "help_desk.HelpDeskTicketModel",
            pageName: "help_desk.HelpDeskTicketModel_page",
            clientUUID: null,
            contactUUID: null,
            edit: false,
            visible: false,
            loading: false,
            ticket: null,
            personKey: Date.now(),
            defaultUserSelectId: "empty_ticket",
            editorGate: false,
            slaLoading: false,
            slaInfo: null,
            fullPerson: null,
            contractSelectKey: Date.now(),

            // mobile footer drawer
            footerDrawerVisible: false,
            plannerCreate: false,

            form: createDefaultForm(),
            defaultDeadlineTime: moment("18:00:00", "HH:mm:ss"),
            rules: {
                customer_card: [
                    {
                        required: true,
                        message: this.$t("helpdesk.required_field"),
                        trigger: "change",
                    },
                ],
                contact_person: [
                    {
                        required: true,
                        message: this.$t("helpdesk.required_field"),
                        trigger: "change",
                    },
                ],
            },
            nameRules: {
                name: [
                    {
                        required: true,
                        message: this.$t("helpdesk.required_field"),
                        trigger: "change",
                    },
                ],
            },
            initListClient: [],
            initListCategory: [],
            initListConctactPerson: [],
            orgAdminClient: null,
            disabled_massage: false,
            disabledSpecialist: false,
            actionInfo: null,
            getClientLoading: false,
        };
    },
    methods: {
        // ===== MOBILE FOOTER MENU =====
        openFooterDrawer() {
            if (this.loading) return;
            this.footerDrawerVisible = true;
        },
        runFooterAction(payload) {
            this.footerDrawerVisible = false;
            this.formSubmit(payload);
        },
        // =============================

        setReceiptDateFromShortcut(m) {
            if (!m) return;
            const v = m.clone ? m.clone() : this.$moment(m);
            this.form.receipt_date = v;
        },
        setDeadlineFromShortcut(m) {
            if (!m) return;
            const v = m.clone ? m.clone() : this.$moment(m);
            this.form.dead_line = v;
        },
        applyDefaultTime(baseMoment) {
            const m = this.$moment(baseMoment).clone();
            const def = this.defaultDeadlineTime;

            return m
                .hour(def.hour())
                .minute(def.minute())
                .second(def.second())
                .millisecond(def.millisecond());
        },
        tooltipFormat(m) {
            const fmt = "DD.MM.YYYY HH:mm";
            return this.$moment(m).format(fmt);
        },

        async getSLA() {
            this.slaInfo = null;
            if (this.form.customer_card) {
                if (this.form.contact_person || this.form.category) {
                    try {
                        const payload = { customer_card: this.form.customer_card };
                        if (this.form.contact_person) payload.contact_person = this.form.contact_person;
                        if (this.form.category) payload.category = this.form.category;

                        this.slaLoading = true;
                        const { data } = await this.$http.post("help_desk/tickets/sla/", payload);
                        if (data?.sla) this.slaInfo = data;
                    } catch (error) {
                        console.log(error);
                    } finally {
                        this.slaLoading = false;
                    }
                }
            }
        },

        // ✅ после создания/редактирования категории — сразу выбираем
        afterCreateCategory(category) {
            // обновим список
            if (this.$refs.selectCategoryRef) this.$refs.selectCategoryRef.listReload();

            // если модалка вернула созданную/обновлённую категорию — сразу выберем её
            if (category?.id) {
                this.form.category = category.id;
                this.initListCategory = [{ id: category.id, name: category.name }];
                this.getSLA();
            }
        },

        // ✅ открыть создание категории
        createCategory() {
            if (this.$refs.modalCategoryCreateRef) this.$refs.modalCategoryCreateRef.open();
        },

        // ✅ редактирование категории прямо из формы
        async editCategory() {
            if (!this.form.category || !this.$refs.modalCategoryCreateRef) return;

            try {
                const { data } = await this.$http.get(`help_desk/ticket_categories/${this.form.category}/`);
                if (data) this.$refs.modalCategoryCreateRef.startEdit(data);
            } catch (e) {
                console.error("Не удалось получить категорию для редактирования", e);
            }
        },

        selectCategory(category) {
            this.form.category = category.id;
            this.initListCategory = [{ id: category.id, name: category.name }];
            this.getSLA();
        },

        selectClient(client) {
            this.slaInfo = null;
            this.form.customer_card = client.id;
            this.form.analytics_key = null;
            this.contractSelectKey = Date.now();
            this.initListClient = [{ id: client.id, string_view: client.name }];
            this.handleSelectClient(client.id);
        },

        selectContactPerson(item) {
            this.changeFullPerson(item);
            this.form.contact_person = item.id;
            this.initListConctactPerson = [{ id: item.id, name: item.name }];
            this.getSLA();
        },

        selectClientId(clientId) {
            this.slaInfo = null;
            this.handleSelectClient(clientId);
        },

        async loadSpecialistsForCustomerCard(clientId) {
            const url = `/help_desk/customer_cards/${clientId}/specialists/actual/?display=user`;
            try {
                const { data } = await this.$http.get(url);
                if (data.count === 1) this.form.specialist = data.results[0];
            } catch (e) {
                console.error("Не удалось получить специалистов", e);
            }
        },

        handleSelectClient(clientId) {
            const url = `help_desk/customer_cards/${clientId}/`;
            this.form.category = null;
            this.loadSpecialistsForCustomerCard(clientId);

            if (this.$refs.selectCategoryRef) this.$refs.selectCategoryRef.listReload();

            this.getClientLoading = true;
            this.$http
                .get(url)
                .then(({ data }) => {
                    this.orgAdminClient = data.org_admin.id;
                    this.getActionInfoByOrgAdmin(data.org_admin.id);
                })
                .catch((error) => {
                    console.error(error);
                })
                .finally(() => {
                    this.getClientLoading = false;
                });
        },

        getActionInfoByOrgAdmin(orgAdminId) {
            const url = `help_desk/org_admin/${orgAdminId}/action_info/`;
            return this.$http(url).then(({ data }) => {
                this.actionInfo = data;
            });
        },

        async openAllConctactPersons() {
            let contact_person_data;
            try {
                if (this.form.contact_person) {
                    contact_person_data = await this.$http.get(`help_desk/contact_persons/${this.form.contact_person}/`);
                }
            } catch (e) {
                console.log(e);
            }

            if (!this.$refs.listViewModalConctactPersonRef) {
                console.error("Не удалось найти реф listViewModalConctactPersonRef");
                return;
            }

            this.$refs.listViewModalConctactPersonRef.open();

            if (this.form.contact_person) {
                this.$nextTick(async () => {
                    if (
                        this.$refs.listViewModalConctactPersonRef?.$refs?.refListView?.$refs?.tableRef &&
                        contact_person_data
                    ) {
                        this.$refs.listViewModalConctactPersonRef.$refs.refListView.$refs.tableRef.selectedRows = [
                            contact_person_data.data,
                        ];
                    }
                });
            }
        },

        async openAllClients() {
            let customer_card_data;
            try {
                if (this.form.customer_card) {
                    customer_card_data = await this.$http.get(
                        `help_desk/customer_cards/${this.form.customer_card}/customer_card_detail/?page_name=helpdesk_clients_all`
                    );
                }
            } catch (e) {
                console.log(e);
            }

            if (!this.$refs.listViewModalClientsRef) {
                console.error("Не удалось найти реф listViewModalClientsRef");
                return;
            }

            await this.$refs.listViewModalClientsRef.open();

            if (this.form.customer_card) {
                this.$nextTick(async () => {
                    if (this.$refs.listViewModalClientsRef.$refs.refListView.$refs.tableRef && customer_card_data) {
                        this.$refs.listViewModalClientsRef.$refs.refListView.$refs.tableRef.selectedRows = [
                            customer_card_data.data,
                        ];
                    }
                });
            }
        },

        openAllCategories() {
            if (!this.$refs.listViewModalCategoriesRef) {
                console.error("Не удалось найти реф lilistViewModalCategoriesRef");
                return;
            }
            this.$refs.listViewModalCategoriesRef.open();
        },

        changeCustomerCard() {
            this.slaInfo = null;
            this.form.contact_person = null;
            this.form.analytics_key = null;
            this.form.specialist = null;
            this.form.category = null;
            this.contractSelectKey = Date.now();
            this.initListCategory = [];
        },

        changeMetadata({ key, value }) {
            this.$set(this.form.metadata, key, value);
        },

        addClient() {
            eventBus.$emit("helpdesc_add_client", true, { slaSelect: true });
        },
        addClientNoReturn() {
            eventBus.$emit("helpdesc_add_client", false, { slaSelect: true });
        },
        addContact() {
            eventBus.$emit("add_ticket_contact", this.form.customer_card);
        },
        changeFullPerson(data) {
            this.fullPerson = data;
        },
        editContact() {
            eventBus.$emit("edit_contact_person_modal", {
                client: { id: this.form.customer_card },
                contactPerson: this.fullPerson,
            });
        },

        formSubmit({ create_more = false, in_work = false, in_complete = false, is_open = false } = {}) {
            if (!this.loading) {
                this.$refs.ruleForm.validate(async (valid) => {
                    if (!valid) return false;

                    try {
                        this.loading = true;

                        const queryData = JSON.parse(JSON.stringify(this.form));
                        if (queryData.analytics_key && typeof queryData.analytics_key === "object")
                            queryData.analytics_key = queryData.analytics_key.id;
                        if (queryData.specialist) queryData.specialist = queryData.specialist.id;
                        if (queryData.visors) queryData.visors = queryData.visors.map((item) => item.id);
                        if (in_work) queryData.in_work = in_work;

                        if (!this.edit) {
                            let url_create = "/help_desk/tickets/";
                            if (this.form.message_uid) url_create = "/help_desk/tickets/create_from_chat/";

                            const { data } = await this.$http.post(url_create, queryData);

                            if (data) {
                                const query = JSON.parse(JSON.stringify(this.$route.query));
                                query.ticketView = data.id;

                                if (!create_more) this.visible = false;

                                if (in_work || is_open) this.$router.replace({ query });
                                if (in_complete) {
                                    query.in_complete = true;
                                    this.$router.replace({ query });
                                }

                                if (create_more) {
                                    this.clearForm();
                                    this.clientUUID = uuidv1();
                                    this.contactUUID = uuidv1();
                                    this.$nextTick(() => {
                                        this.$refs.editorRef.editorFocus();
                                    });
                                }

                                this.$message.success(this.$t("helpdesk.ticket_created"));
                                eventBus.$emit(`update_filter_${this.model}_${this.pageName}`);
                                eventBus.$emit("ADD_TICKET_KANBAN", data);
                                if (this.plannerCreate) {
                                    eventBus.$emit("PLANNER_TICKET_CREATED", {
                                        ...data,
                                        specialist: data.specialist || this.form.specialist,
                                        receipt_date: data.receipt_date || queryData.receipt_date,
                                        dead_line: data.dead_line || queryData.dead_line,
                                        start_date: data.start_date || queryData.start_date || queryData.receipt_date,
                                        end_date: data.end_date || queryData.end_date || queryData.dead_line
                                    });
                                }
                                if (this.$store.hasModule('workplan')) {
                                    this.$store.dispatch('workplan/reloadList', {
                                        list: 'ticketList'
                                    })
                                }
                                if (this.$route.query?.client) eventBus.$emit("ticket_detail_reload");
                            }
                        }
                    } catch (error) {
                        errorHandler({ error });
                    } finally {
                        this.loading = false;
                    }
                });
            }
        },

        getCalendarContainer(trigger) {
            return trigger.parentNode;
        },

        // Автоподстановка 18:00, если выбран только день (00:00:00)
        handleDeadlineChange(value) {
            if (!value) return;
            const isOnlyDate = value.hour() === 0 && value.minute() === 0 && value.second() === 0;
            if (isOnlyDate) this.form.dead_line = value.clone().hour(18).minute(0).second(0);
        },

        setTodayAt1800() {
            const v = moment().hour(18).minute(0).second(0).millisecond(0);
            this.form.dead_line = v;
            if (this.$refs.deadlinePicker && this.$refs.deadlinePicker.blur) {
                this.$nextTick(() => this.$refs.deadlinePicker.blur());
            }
        },

        async afterVisibleChange(val) {
            if (val) {
                this.clientUUID = uuidv1();
                this.contactUUID = uuidv1();

                eventBus.$on("helpdesc_return_client", (client) => {
                    if (this.initListConctactPerson?.length) this.initListConctactPerson = [];
                    if (this.form.contact_person) {
                        this.form.contact_person = null;
                        eventBus.$emit(`select_exclude_${this.clientUUID}`, client);
                    }
                    this.selectClient(client);
                });

                eventBus.$on("helpdesc_return_contact", (contact) => {
                    this.changeFullPerson(contact);
                    this.form.contact_person = contact.id;
                    eventBus.$emit(`push_select_data_${this.contactUUID}`, contact);
                    this.contactUUID = uuidv1();
                    this.personKey = Date.now();
                    this.initListConctactPerson = [{ ...contact }];
                    this.getSLA();
                });

                this.editorGate = false;
                await this.$nextTick();
                await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
                this.editorGate = true;
            } else {
                eventBus.$off("helpdesc_return_client");
                eventBus.$off("helpdesc_return_contact");
            }
        },

        clearForm() {
            this.slaInfo = null;
            this.contactUUID = null;
            this.clientUUID = null;
            this.edit = false;
            this.fullPerson = null;
            this.disabledSpecialist = false;
            this.disabled_massage = false;

            // закрываем mobile drawer, если был открыт
            this.footerDrawerVisible = false;

            this.form = createDefaultForm();

            this.initListCategory = [];
            this.orgAdminClient = null;
        },

        afterClose() {
            this.clearForm();
        },
    },

    mounted() {
        eventBus.$on("helpdesc_add_tickets", (data) => {
            this.form = createDefaultForm();
            this.plannerCreate = Boolean(data?.plannerCreate);
            this.visible = true;
            this.$nextTick(() => {
                if (data) {
                    if (data.specialist) this.disabledSpecialist = true;
                    this.disabled_massage = data.disabled_massage;

                    this.selectClient(data.customer_card);
                    this.selectContactPerson(data.contact_person);

                    this.form.specialist = data.specialist;
                    this.form.message_uid = data.message_uid;
                    this.form.description = data.description;

                    if(data.receipt_date)
                        this.form.receipt_date = this.$moment(data.receipt_date)
                    if(data.dead_line)
                        this.form.dead_line = this.$moment(data.dead_line)
                }
            });
        });

        eventBus.$on("helpdesc_edit_tickets", (client) => {
            this.plannerCreate = false;
            this.edit = true;
            const ticketData = JSON.parse(JSON.stringify(client));
            this.form = { ...ticketData };
            this.visible = true;
        });
    },

    beforeDestroy() {
        eventBus.$off("helpdesc_add_tickets");
        eventBus.$off("helpdesc_edit_tickets");
    },
};
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

.description_editor {
    min-height: 108.65px;
    &::v-deep {
        .ck-editor__top {
            position: sticky !important;
            top: 0px !important;
            background: white !important;
            z-index: 999999;
        }
        .ck {
            &.ck-toolbar__items {
                margin-right: 0px !important;
            }
            &.ck-toolbar__separator {
                opacity: 0;
                margin-right: 0px !important;
            }
            &.ck-editor__top.ck-reset_all {
                border-radius: 8px !important;
            }
            &.ck-toolbar {
                border: 0px;
            }
            &.ck-content {
                border: 0px !important;
                box-shadow: none !important;
                padding-left: 0px !important;
                padding-right: 0px !important;
            }
            &.ck-editor__main > .ck-editor__editable {
                background-color: transparent;
            }
        }
    }
}

/* кнопка с точками как в примере */
.dots_btn {
    width: 44px;
    min-width: 44px;
    padding: 0 !important;
    display: flex;
    align-items: center;
    justify-content: center;
}

.priority_picker {
    &__item {
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
        &:hover {
            background: #f0f1f6;
        }
        &.active {
            background: #f0f1f6;
        }
    }
}

.user-drawer ::v-deep {
    .user_draw_input {
        min-height: 0;
        height: 32px;
    }
}

.calendar-widget ::v-deep(.ant-calendar-picker-icon) {
    right: 6px !important;
}
</style>

<style lang="scss">
/* старый стиль ошибки */
.contact_person {
    .ant-select-selection {
        border-color: rgb(245, 34, 45) !important;
    }
}

/* ===== MOBILE MODAL ===== */
.ticket_form_modal--mobile {
    .ant-modal {
        top: 0 !important;
        padding-bottom: 0 !important;
        margin: 0 !important;
        width: 100% !important;
        max-width: 100vw !important;
    }

    .ant-modal-content {
        height: 100vh;
        border-radius: 0 !important;
        display: flex;
        flex-direction: column;
    }

    .ant-modal-body {
        flex: 1;
        overflow: auto;
    }

    .ant-modal-footer {
        position: sticky;
        bottom: 0;
        background: #fff;
        z-index: 5;
    }
}

/* ломаем "строку" на мобилке: label сверху, контрол вниз */
.form-row--mobile {
    display: block !important;
    height: auto !important;

    .ant-form-item-label {
        width: 100% !important;
        float: none !important;
        padding: 0 0 6px !important;
        line-height: 1.2;
        text-align: left !important;
    }

    .ant-form-item-control-wrapper {
        width: 100% !important;
        float: none !important;
    }
}

/* футер: элементы один под другим */
.modal-footer--mobile {
    width: 100%;
    display: grid !important;
    grid-template-columns: 1fr;
    gap: 8px !important;
}
/* ======================== */
</style>
