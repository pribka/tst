<template>
    <a-modal
        :width="isMobile ? '100%' : 600"
        :afterClose="afterClose"
        destroyOnClose
        :wrapClassName="`client_modal ${isMobile ? 'client_modal_fullscreen' : ''}`"
        :dialog-style="isMobile ? { top: '0px', paddingBottom: '0' } : { top: '20px' }"
        :visible="visible"
        @cancel="visible = false"
        @afterVisibleChange="afterVisibleChange">

        <template #title v-if="!formLoading">
            <a-form-model ref="nameForm" :model="form">
                <a-form-model-item
                    ref="name"
                    prop="name"
                    class="mb-0"
                    :rules="{ required: true, message: $t('helpdesk.required_field'), trigger: 'change' }">
                    <div class="flex items-center justify-between">
                        <a-input
                            v-model="form.name"
                            ref="nameInput"
                            inputType="ghost"
                            :placeholder="$t('helpdesk.contractor_name')"
                            size="large"
                            @pressEnter="onSubmit()" />
                        <HelpButton partCode="helpdesk" class="ml-2" />
                    </div>
                </a-form-model-item>
            </a-form-model>
        </template>

        <a-form-model
            v-if="!formLoading"
            ref="ruleForm"
            :model="form"
            class="client_form mini_form">

            <a-form-model-item
                v-if="formInfo.inn"
                ref="inn"
                prop="inn"
                :rules="formInfo?.inn?.rules ?? [
                    { required: true, message: $t('helpdesk.required_field'), trigger: 'change' },
                    { min: 12, message: $t('helpdesk.min_symbols', {count: 12}), trigger: 'blur' },
                    { max: 12, message: $t('helpdesk.max_symbols', {count: 12}), trigger: 'blur' },
                ]">
                <a-input
                    v-model="form.inn"
                    inputType="ghost"
                    :maxLength="binLength"
                    noXPadding
                    :placeholder="formInfo.inn.placeholder || ''"
                    @pressEnter="onSubmit()">
                    <template #prefix>
                        <i class="fi fi-rr-pencil" />
                    </template>
                    <template #suffix>
                        <span style="color: #888888;">{{ form.inn.length }}/{{ binLength }}</span>
                    </template>
                </a-input>
            </a-form-model-item>

            <a-form-model-item v-if="formInfo.full_name" ref="full_name" prop="full_name">
                <a-input
                    v-model="form.full_name"
                    inputType="ghost"
                    noXPadding
                    :placeholder="formInfo.full_name.placeholder || ''"
                    @pressEnter="onSubmit()">
                    <template #prefix>
                        <i class="fi fi-rr-pencil" />
                    </template>
                </a-input>
            </a-form-model-item>

            <a-form-model-item v-if="formInfo.legal_address" ref="legal_address" prop="legal_address">
                <a-input
                    v-model="form.legal_address"
                    inputType="ghost"
                    noXPadding
                    :placeholder="formInfo.legal_address.placeholder || $t('helpdesk.enter_legal_address')"
                    @pressEnter="onSubmit()">
                    <template #prefix>
                        <i class="fi fi-rr-pencil" />
                    </template>
                </a-input>
            </a-form-model-item>

            <a-form-model-item
                ref="org_admin"
                prop="org_admin"
                :rules="{ required: true, message: $t('helpdesk.required_field'), trigger: 'change' }"
                v-if="!hideOrgAdmin && formInfo.org_admin">
                <DSelect
                    v-model="form.org_admin"
                    apiUrl="/contractor_permissions/organizations/"
                    class="w-full"
                    oneSelect
                    inputType="ghost"
                    size="default"
                    firstSelected
                    :placeholder="formInfo.org_admin.placeholder || $t('helpdesk.support_organization')"
                    :listObject="false"
                    labelKey="name"
                    :params="{ permission_type: 'help_desk_manager,help_desk_admin' }"
                    :default-active-first-option="false"
                    :filter-option="false"
                    :not-found-content="null"
                    @change="selectOrgAdmin">
                    <template #prefixIcon>
                        <i class="fi fi-rr-users" />
                    </template>
                </DSelect>
            </a-form-model-item>

            <transition name="slide-fade">
                <div v-if="form.org_admin && formInfo.admins" class="mb-2">
                    <div class="mb-3">{{ formInfo.admins.title || $t('helpdesk.admin_organization') }}</div>

                    <template v-if="formInfo.admins.fields">
                        <div>
                            <div
                                v-for="(adminData, index) in form.admins"
                                :key="index"
                                class="contact_block">

                                <a-form-model-item
                                    v-if="formInfo.admins.fields.bin"
                                    :rules="[
                                        { min: binLength, message: $t('helpdesk.min_symbols', {count: binLength}), trigger: 'blur' },
                                        { max: binLength, message: $t('helpdesk.max_symbols', {count: binLength}), trigger: 'blur' },
                                    ]"
                                    :prop="'admins.' + index + '.bin'">
                                    <a-popover
                                        v-model="binVisible[index]"
                                        :trigger="adminData.trigger"
                                        transitionName=""
                                        overlayClassName="select_bin_popup"
                                        :getPopupContainer="getPopupContainer"
                                        placement="bottomLeft">
                                        <a-input
                                            v-model="adminData.bin"
                                            :placeholder="formInfo.admins.fields.bin.placeholder || $t('helpdesk.enter_bin')"
                                            inputType="ghost"
                                            :ref="`input_bin_${index}`"
                                            :maxLength="binLength"
                                            noXPadding
                                            @change="binChange($event, index, adminData)"
                                            @pressEnter="onSubmit()">
                                            <template #prefix>
                                                <i class="fi fi-rr-pencil" />
                                            </template>
                                            <template #suffix>
                                                <a-spin :spinning="adminData.loading" size="small">
                                                    <span style="color: #888888;">{{ adminData.bin.length }}/{{ binLength }}</span>
                                                </a-spin>
                                            </template>
                                        </a-input>

                                        <template #content>
                                            <div class="org_list truncate">
                                                <div
                                                    v-for="org in form.admins[index].results"
                                                    :key="org.id"
                                                    class="org_list__item truncate"
                                                    :title="`${org.name} - ${org.bin}`"
                                                    :class="adminData.bin === org.bin && 'active'"
                                                    @click="selectOrg(org, index)">
                                                    <div class="org_name truncate">{{ org.name }}</div>
                                                    <div class="org_bin truncate">{{ org.bin }}</div>
                                                </div>
                                            </div>
                                            <div class="mt-1">
                                                <a-button type="ui_ghost" size="small" block @click="binVisible[index] = false">
                                                    {{ $t('helpdesk.close') }}
                                                </a-button>
                                            </div>
                                        </template>
                                    </a-popover>
                                </a-form-model-item>

                                <a-form-model-item
                                    v-if="formInfo.admins.fields.name"
                                    :prop="'admins.' + index + '.name'">
                                    <a-input
                                        v-model="adminData.name"
                                        :placeholder="formInfo.admins.fields.name.placeholder || $t('helpdesk.enter_name')"
                                        inputType="ghost"
                                        :disabled="adminData.selected || adminData.loading"
                                        noXPadding
                                        @pressEnter="onSubmit()">
                                        <template #prefix>
                                            <i class="fi fi-rr-pencil" />
                                        </template>
                                    </a-input>
                                </a-form-model-item>

                                <a-button
                                    v-if="form.admins.length > 1"
                                    type="flat_danger"
                                    size="small"
                                    @click="deleteAdmins(index)">
                                    {{ $t('helpdesk.delete') }}
                                </a-button>
                            </div>
                        </div>

                        <a-button
                            type="link"
                            size="small"
                            flaticon
                            icon="fi-rr-plus-small"
                            class="mt-2"
                            @click="addAdmin()">
                            {{ $t('helpdesk.add_more') }}
                        </a-button>
                    </template>
                </div>
            </transition>

            <template v-if="formInfo.contact_persons">
                <div class="mb-3">{{ formInfo.contact_persons.title || $t('helpdesk.contact_person') }}</div>

                <a-spin v-if="formInfo.contact_persons.fields" :spinning="deleteLoading" size="small">
                    <div
                        v-for="(contact_person, index) in form.contact_persons"
                        :key="index"
                        class="contact_block">

                        <a-form-model-item v-if="formInfo.contact_persons.fields.name" :prop="'contact_persons.' + index + '.name'">
                            <a-input
                                v-model="contact_person.name"
                                :placeholder="formInfo.contact_persons.fields.name.placeholder || $t('helpdesk.enter_full_name')"
                                inputType="ghost"
                                noXPadding
                                @change="checkEdit(index)"
                                @pressEnter="onSubmit()">
                                <template #prefix>
                                    <i class="fi fi-rr-pencil" />
                                </template>
                            </a-input>
                        </a-form-model-item>

                        <a-form-model-item v-if="formInfo.contact_persons.fields.phone" :prop="'contact_persons.' + index + '.phone'">
                            <a-input
                                v-model="contact_person.phone"
                                :placeholder="formInfo.contact_persons.fields.phone.placeholder || $t('helpdesk.enter_phone')"
                                inputType="ghost"
                                noXPadding
                                @change="checkEdit(index)"
                                @pressEnter="onSubmit()">
                                <template #prefix>
                                    <i class="fi fi-rr-pencil" />
                                </template>
                            </a-input>
                        </a-form-model-item>

                        <a-form-model-item v-if="formInfo.contact_persons.fields.telegram" :prop="'contact_persons.' + index + '.telegram'">
                            <a-input
                                v-model="contact_person.telegram"
                                :placeholder="formInfo.contact_persons.fields.telegram.placeholder || $t('helpdesk.enter_telegram')"
                                inputType="ghost"
                                noXPadding
                                @change="checkEdit(index)"
                                @pressEnter="onSubmit()">
                                <template #prefix>
                                    <i class="fi fi-rr-pencil" />
                                </template>
                            </a-input>
                        </a-form-model-item>

                        <a-form-model-item
                            v-if="formInfo.contact_persons.fields.email"
                            :prop="'contact_persons.' + index + '.email'"
                            :rules="[{ type: 'email', message: $t('helpdesk.email_invalid'), trigger: 'blur' }]">
                            <a-input
                                v-model="contact_person.email"
                                :placeholder="formInfo.contact_persons.fields.email.placeholder || $t('helpdesk.enter_email')"
                                inputType="ghost"
                                noXPadding
                                @change="checkEdit(index)"
                                @pressEnter="onSubmit()">
                                <template #prefix>
                                    <i class="fi fi-rr-pencil" />
                                </template>
                            </a-input>
                        </a-form-model-item>

                        <a-form-model-item v-if="formInfo.contact_persons.fields.post_inst" :prop="'contact_persons.' + index + '.post_inst'">
                            <ListViewModal
                                v-if="form.org_admin"
                                :endpoint="`/help_desk/contact_person_post/?contractor=${form.org_admin}`"
                                tableType="helpdesk_positions_select"
                                pageName="help_desk.ContactPersonPostModel_all"
                                title="Должности"
                                model="help_desk.ContactPersonPostModel"
                                @select="selectPost($event, index)"
                                :add="() => addPost(index)"
                                ref="listViewModalPostRef">
                                <template v-slot:headerLeft="{ rowSelected }">
                                    <SLASelect
                                        v-if="rowSelected"
                                        :selectItem="rowSelected"
                                        :params="{ contractor: form.org_admin }"
                                        pageName="help_desk.ContactPersonPostModel_all"
                                        model="help_desk.ContactPersonPostModel" />
                                </template>
                            </ListViewModal>

                            <DSelect
                                ref="selectPostRef"
                                v-model="contact_person.post_inst"
                                apiUrl="/help_desk/contact_person_post/"
                                class="w-full"
                                oneSelect
                                :key="form.org_admin"
                                :showAllHandler="() => openAllPost(index)"
                                infinity
                                :initList="false"
                                :disabled="!form.org_admin"
                                showSearch
                                size="default"
                                inputType="ghost"
                                :initOptionList="initListPost"
                                :placeholder="formInfo.contact_persons.fields.post_inst.placeholder || 'Выберите должность'"
                                :listObject="false"
                                :params="{ contractor: form.org_admin }"
                                labelKey="name"
                                valueKey="id"
                                :default-active-first-option="false"
                                :filter-option="false"
                                :not-found-content="null">

                                <template #prefixIcon>
                                    <i class="fi fi-rr-id-badge" />
                                </template>

                                <template #suffixSlot>
                                    <a-spin v-if="getPostLoading" size="small" />
                                    <a-button
                                        v-else
                                        type="ui"
                                        ghost
                                        shape="circle"
                                        size="small"
                                        :disabled="!form.org_admin"
                                        flaticon
                                        v-tippy
                                        content="Добавить должность"
                                        icon="fi-rr-add"
                                        @click="addPost(index)"/>
                                </template>
                            </DSelect>

                            <PositionFormModal
                                v-if="form.org_admin"
                                :contractor="form.org_admin"
                                slaSelect
                                :index="index"
                                model="help_desk.ContactPersonPostModel"
                                @change="changePostModal($event, index)" />
                        </a-form-model-item>

                        <a-form-model-item v-if="formInfo.contact_persons.fields.is_main">
                            <a-checkbox
                                v-model="contact_person.is_main"
                                @change="checkEdit(index)">
                                {{ formInfo.contact_persons.fields.is_main.title || $t('helpdesk.is_main') }}
                            </a-checkbox>
                        </a-form-model-item>

                        <a-form-model-item v-if="slaSelect">
                            <component
                                :is="slaSelectComponent"
                                :listUpdate="false"
                                useInject
                                inputType="ghost"
                                :disabled="!form.org_admin"
                                :key="form.org_admin"
                                :slaInitSelected="contact_person.sla"
                                :params="{ contractor: form.org_admin }"
                                @change="SLAChange($event, index)">
                                <template #prefixIcon>
                                    <i class="fi fi-rr-bookmark mr-3" />
                                </template>
                            </component>
                        </a-form-model-item>

                        <template v-if="edit">
                            <a-button type="flat_danger" size="small" @click="deleteContactApi(contact_person, index)">
                                {{ $t('helpdesk.delete') }}
                            </a-button>
                        </template>
                        <template v-else>
                            <a-button
                                v-if="form.contact_persons.length > 1"
                                type="flat_danger"
                                size="small"
                                @click="deleteContact(index)">
                                {{ $t('helpdesk.delete') }}
                            </a-button>
                        </template>
                    </div>
                </a-spin>

                <a-button type="link" size="small" flaticon icon="fi-rr-plus-small" class="mt-2" @click="addContact()">
                    {{ $t('helpdesk.add_more') }}
                </a-button>
            </template>
        </a-form-model>

        <a-skeleton v-else active />

        <template #footer>
            <!-- MOBILE: как в примере (primary + маленькая кнопка справа) -->
            <div v-if="isMobile" class="flex items-center w-full">
                <a-button
                    type="primary"
                    size="large"
                    block
                    class="flex-1"
                    :loading="loading"
                    :disabled="formLoading"
                    @click="onSubmit()">
                    {{ edit ? $t('helpdesk.save') : $t('helpdesk.create_contractor') }}
                </a-button>
            </div>

            <!-- DESKTOP: как было -->
            <div v-else class="flex gap-1 items-center">
                <a-button
                    type="primary"
                    size="large"
                    :loading="loading"
                    :disabled="formLoading"
                    @click="onSubmit()">
                    {{ edit ? $t('helpdesk.save') : $t('helpdesk.create_contractor') }}
                </a-button>

                <a-button
                    type="ui_ghost"
                    ghost
                    size="large"
                    @click="visible = false">
                    {{ $t('helpdesk.close') }}
                </a-button>
            </div>
        </template>
    </a-modal>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { clientFormModel, clientForm, clientFormKey } from '../utils/utils.js'
import { mergeForm } from '@/utils/utils.js'
import { errorHandler } from '@/utils/index.js'

let binTimer;

export default {
    components: {
        SLASelect: () => import('./SLASelect.vue'),
        DSelect: () => import('@apps/DrawerSelect/Select.vue'),
        PositionFormModal: () => import('./PositionFormModal.vue'),
        ListViewModal: () => import("@/components/ListView/ListViewModal.vue"),
        HelpButton: () => import('@apps/Support/components/HelpButton.vue')
    },
    computed: {
        storeFormInfo() {
            return this.$store.state.formInfo?.formInfo?.[this.formKey] || {}
        },
        formInfo() {
            return mergeForm(clientForm, this.storeFormInfo)
        },
        slaSelectComponent() {
            if(this.slaSelect)
                return () => import('./SLASelect.vue')
            return null
        },
        isMobile() {
            return this.$store.state.isMobile
        },
    },
    data() {
        return {
            slaSelect: false,
            getPostLoading: false,
            initListPost: [],
            model: "help_desk.CustomerCardModel",
            pageName: "list_help_desk.CustomerCardModel",
            edit: false,
            visible: false,
            deleteLoading: false,
            activeKey: '1',
            loading: false,
            isReturn: false,
            binLength: 12,
            deleteContacts: [],
            formKey: clientFormKey,
            formLoading: true,
            binVisible: {
                0: false
            },
            form: JSON.parse(JSON.stringify(clientFormModel)),
            hideOrgAdmin: false,
            lead: null,
        }
    },
    methods: {
        SLAChange(value, index) {
            this.$set(this.form.contact_persons[index], 'sla', value.id)
        },
        selectPost(post, index) {
            if(post) {
                this.$set(this.form.contact_persons[index], 'post_inst', post.id)
                this.initListPost = [{ ...post }]
            }
        },
        changePostModal(data, index) {
            this.$set(this.form.contact_persons[index], 'post_inst', data.id)
            this.initListPost.push(data)
        },
        addPost(index) {
            eventBus.$emit(`open_modal_position_add_in_${index}`)
        },
        openAllPost(index) {
            this.$nextTick(() => {
                if(this.$refs?.listViewModalPostRef?.[index])
                    this.$refs.listViewModalPostRef[index].open()
            })
        },
        afterVisibleChange(vis) {
            if(vis) {
                this.getFormInfo()
            } else {
                this.initListPost = []
            }
        },
        async getFormInfo() {
            try {
                if (!Object.keys(this.storeFormInfo)?.length)
                    await this.$store.dispatch('formInfo/getFormInfo', { form: this.formKey })
            } catch (error) {
                console.log(error)
            } finally {
                this.formLoading = false
                this.$nextTick(() => {
                    this.$refs.nameInput?.focus()
                })
            }
        },
        getPopupContainer(trigger) {
            return trigger.parentNode
        },
        selectOrg(org, index) {
            this.$set(this.form.admins, index, {
                ...this.form.admins[index],
                ...org,
                key: Date.now(),
                add: false
            })
            this.$set(this.binVisible, index, false)
            this.$set(this.form.admins[index], 'selected', true)
        },
        focusAdminBin(index = 0) {
            this.$nextTick(() => {
                requestAnimationFrame(() => {
                    if(this.$refs[`input_bin_${index}`]?.[0]) {
                        const comp = this.$refs[`input_bin_${index}`][0]
                        if (comp && comp.$el) {
                            const el = comp.$el.querySelector('input.ant-input')
                            if (el) el.focus()
                        }
                    }
                })
            })
        },
        selectOrgAdmin() {
            if(this.form.contact_persons?.length) {
                this.form.contact_persons.forEach((item, index) => {
                    this.$set(this.form.contact_persons[index], 'post_inst', null)
                })
            }
            this.form.admins = [{
                ...clientFormModel.admins[0],
                add: true,
                key: Date.now()
            }]
            this.initListPost = []
            setTimeout(() => {
                this.focusAdminBin()
            }, 150)
        },
        async binChange(e, index, admin) {
            const value = e.target.value
            clearTimeout(binTimer)

            if(value.length) {
                binTimer = setTimeout(async () => {
                    try {
                        this.$set(this.form.admins[index], 'trigger', 'none')
                        this.$set(this.binVisible, index, false)
                        this.$set(this.form.admins[index], 'loading', true)
                        this.$set(this.form.admins[index], 'selected', false)
                        if(this.form.admins[index].name) {
                            this.$set(this.form.admins[index], 'name', "")
                        }
                        const { data } = await this.$http.get('/help_desk/admins/', {
                            params: {
                                search: value,
                                org_admin: this.form.org_admin,
                                page: admin.page
                            }
                        })
                        if(data?.results?.length) {
                            this.$set(this.form.admins[index], 'trigger', 'click')
                            this.$set(this.form.admins[index], 'next', data.next)
                            this.$set(this.form.admins[index], 'results', data.results)
                            if(value.length && data.results.length === 1) {
                                this.$set(this.form.admins, index, {
                                    ...this.form.admins[index],
                                    ...data.results[0],
                                    add: false
                                })
                                this.$set(this.form.admins[index], 'selected', true)
                                this.$set(this.form.admins[index], 'trigger', 'none')
                                this.$set(this.binVisible, index, false)
                            } else {
                                this.$set(this.binVisible, index, true)
                            }
                        } else {
                            this.$set(this.form.admins[index], 'add', true)
                        }
                    } catch(e) {
                        console.log(e)
                    } finally {
                        this.$set(this.form.admins[index], 'loading', false)
                    }
                }, 600)
            } else {
                this.$set(this.form.admins[index], 'trigger', 'none')
                this.$set(this.form.admins[index], 'next', true)
                this.$set(this.form.admins[index], 'results', [])
                this.$set(this.binVisible, index, false)
                this.$set(this.form.admins[index], 'add', true)
                this.$set(this.form.admins[index], 'name', "")
            }
        },
        async deleteContactApi(contact, index) {
            try {
                this.deleteLoading = true
                await this.$http.post(`/help_desk/customer_cards/${this.form.id}/contact_persons/remove/`, {
                    contact_person: contact.id
                })
                this.form.contact_persons.splice(index, 1)
                if (this.$route.query?.client)
                    eventBus.$emit('client_detail_reload')
                if(!this.form.contact_persons.length) {
                    this.addContact()
                }
            } catch(error) {
                errorHandler({error})
            } finally {
                this.deleteLoading = false
            }
        },
        checkEdit(index) {
            if(this.form.contact_persons?.[index] && !this.form.contact_persons?.[index].add) {
                this.form.contact_persons[index].edit = true
            }
        },
        deleteAdmins(index) {
            this.form.admins.splice(index, 1)
        },
        deleteContact(index) {
            this.form.contact_persons.splice(index, 1)
        },
        addAdmin() {
            this.form.admins.push(JSON.parse(JSON.stringify(clientFormModel.admins[0])))
            const index = this.form.admins.length - 1
            this.$set(this.binVisible, index, false)
            setTimeout(() => {
                this.focusAdminBin(index)
            }, 150)
        },
        addContact() {
            this.form.contact_persons.push({
                ...clientFormModel.contact_persons,
                add: true
            })
        },
        onSubmit() {
            this.$refs.ruleForm.validate(async valid => {
                this.$refs.nameForm.validate(async valid2 => {
                    if (valid && valid2) {
                        try {
                            this.loading = true
                            const contactPersons = this.form.contact_persons || []

                            const isEmptyContact = (item) =>
                                !item.name?.trim() &&
                                !item.email?.trim() &&
                                !item.telegram?.trim() &&
                                !item.phone?.trim() &&
                                !item.post_inst?.trim()

                            const formCopy = { ...this.form }
                            formCopy.contact_persons = contactPersons.filter(item => !isEmptyContact(item))

                            const queryData = { ...formCopy }

                            if(queryData.admins?.length) {
                                const admins = [...queryData.admins].map(item => {
                                    return {
                                        name: item.name,
                                        key: item.key,
                                        add: item.add,
                                        id: item.id || null,
                                        bin: item.bin,
                                        org_admin: this.form.org_admin
                                    }
                                })
                                const addAdmins = admins.filter(item => item.add && item.bin)

                                if(addAdmins.length) {
                                    for(const key in addAdmins) {
                                        const { data } = await this.$http.post('/help_desk/admins/', addAdmins[key])
                                        if(data) {
                                            const index = admins.findIndex(f => f.key === addAdmins[key].key)
                                            if(index !== -1) {
                                                this.$set(admins, index, data)
                                            }
                                        }
                                    }
                                }

                                queryData.admins = admins.filter(item => item.bin).map(item => item.id)
                            }

                            if (this.edit) {
                                delete queryData.contact_persons

                                const { data } = await this.$http.put(`/help_desk/customer_cards/${queryData.id}/`, queryData)
                                if (data) {
                                    const newContacts = formCopy.contact_persons.filter(f => f.add)
                                    for (const contact of newContacts) {
                                        await this.$http.post(`/help_desk/customer_cards/${queryData.id}/contact_persons/add/`, contact)
                                    }
                                    const editContacts = formCopy.contact_persons.filter(f => f.edit)
                                    for (const contact of editContacts) {
                                        await this.$http.put(`/help_desk/customer_cards/${queryData.id}/contact_persons/update/`, {
                                            ...contact,
                                            contact_person: contact.id
                                        })
                                    }
                                    this.visible = false
                                    this.$message.success(this.$t('helpdesk.contractor_updated'))
                                    eventBus.$emit(`update_filter_${this.model}_${this.pageName}`)
                                    eventBus.$emit(`update_filter_${this.model}`)
                                    if (this.$route.query?.client)
                                        eventBus.$emit('client_detail_reload')
                                    if (this.$route.query?.ticketView)
                                        eventBus.$emit('ticket_in_client_reload')
                                }
                            } else {
                                if (this.lead){
                                    queryData['lead'] = this.lead
                                }
                                const { data } = await this.$http.post('/help_desk/customer_cards/', queryData)
                                if (data) {
                                    if(this.isReturn)
                                        eventBus.$emit('helpdesc_return_client', data)
                                    this.visible = false
                                    this.$message.success(this.$t('helpdesk.contractor_created'))
                                    eventBus.$emit(`update_filter_${this.model}_${this.pageName}`)
                                    eventBus.$emit(`update_filter_${this.model}`)
                                    if (this.$route.query?.client)
                                        eventBus.$emit('client_detail_reload')
                                    if (this.$route.query?.ticketView)
                                        eventBus.$emit('ticket_in_client_reload')
                                }
                            }
                        } catch (error) {
                            errorHandler({error})
                        } finally {
                            this.loading = false
                        }
                    } else
                        return false
                })
            })
        },
        afterClose() {
            this.slaSelect = false
            this.edit = false
            this.activeKey = '1'
            this.isReturn = false
            this.hideOrgAdmin = false
            this.deleteContacts = []
            this.form = JSON.parse(JSON.stringify(clientFormModel))
            this.binVisible = { 0: false }
        }
    },
    mounted() {
        eventBus.$on('helpdesc_add_client', (is_return = false, { hideOrgAdmin=false, formPreset = {}, lead=null, slaSelect = false } = {}) => {
            this.isReturn = is_return
            this.hideOrgAdmin = hideOrgAdmin
            this.formLoading = true
            this.slaSelect = slaSelect
            this.form = {
                ...this.form,
                ...formPreset
            }
            this.lead = lead
            this.visible = true
        })
    },
    beforeDestroy() {
        eventBus.$off('helpdesc_add_client')
    }
}
</script>

<style lang="scss">
.select_bin_popup{
    .ant-popover-arrow{
        display: none;
    }
    &.ant-popover-placement-bottom,
    &.ant-popover-placement-bottomLeft,
    &.ant-popover-placement-bottomRight{
        padding-top: 0px;
    }
}

/* ===== MOBILE FULLSCREEN MODAL ===== */
.client_modal_fullscreen {
    .ant-modal {
        width: 100% !important;
        max-width: 100% !important;
        top: 0 !important;
        margin: 0 !important;
        padding-bottom: 0 !important;
    }
    .ant-modal-content {
        height: 100vh;
        border-radius: 0 !important;
        display: flex;
        flex-direction: column;
    }
    .ant-modal-header {
        flex: 0 0 auto;
    }
    .ant-modal-body {
        flex: 1 1 auto;
        overflow: auto;
        -webkit-overflow-scrolling: touch;
    }
    .ant-modal-footer {
        flex: 0 0 auto;
        padding: 12px 16px;
    }
}
</style>

<style lang="scss" scoped>
.slide-fade-enter-active {
    transition: all .3s ease;
}
.slide-fade-leave-active {
    transition: all .3s cubic-bezier(1.0, 0.5, 0.8, 1.0);
}
.slide-fade-enter, .slide-fade-leave-to{
    transform: translateY(-10px);
    opacity: 0;
}
.org_list{
    max-width: 300px;
    min-width: 300px;
    position: relative;
    max-height: 250px;
    overflow-y: auto;
    &__item{
        border-radius: 8px;
        padding: 8px 12px;
        cursor: pointer;
        font-weight: normal;
        font-size: 14px;
        line-height: 22px;
        user-select: none;
        transition: background 0.3s ease;
        &:hover{
            background-color: #f7f9fc;
        }
        &.active{
            background-color: #e6f7ff;
        }
        &:not(:last-child){
            margin-bottom: 3px;
        }
        .org_bin{
            font-size: 12px;
            line-height: 12px;
            color: #888888;
        }
    }
}
.client_editor{
    &::v-deep{
        .ck-content{
            min-height: 300px;
        }
    }
}
.contact_block{
    background: #f7f9fc;
    padding: 5px 15px;
    border-radius: 8px;
    &:not(:last-child){
        margin-bottom: 10px;
    }
}
.client_form{
    &::v-deep{
        .ant-form-item{
            margin-bottom: 10px;
        }
        .ant-tabs-ink-bar{
            background-color: #ffa819;
        }
        .ant-tabs-bar{
            .ant-tabs-tab{
                margin: 0px;
                padding: 10px 5px;
                user-select: none;
                span{
                    font-size: 13px;
                    display: flex;
                    align-items: center;
                }
                &.ant-tabs-tab-active{
                    color: #000;
                }
            }
        }
    }
}
.dots_btn {
    min-width: 46px;
    width: 46px;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
}

</style>
