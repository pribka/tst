<template>
    <a-row :gutter="{xs: 15, md: 20, lg: 30, xxl: 30}" class="h-full">
        <a-col
            :xs="24"
            :md="14"
            :xl="16"
            :xxl="16"
            class="h-full" :class="viewType === 'table' && 'flex flex-wrap flex-col'">
            <div class="text-lg font-semibold text-gray-800 mb-4">
                {{ $t('directories.a_brief_summary_of_the_requests') }}
            </div>
            <div class="sprint_stat grid gap-3 md:gap-8 grid-cols-1 md:grid-cols-3 mb-5">
                <div class="sprint_stat__card bg-blue-100 border border-blue-300 grid gap-[10px]">
                    <div class="text-blue-600 text-xs sm:text-sm font-medium sm:mb-1">{{ $t('directories.a_total_number_of_requests') }}</div>
                    <div class="text-xl sm:text-2xl font-bold text-blue-900">{{summary.total}}</div>
                </div>
                <div class="sprint_stat__card bg-yellow-100 border border-yellow-300 grid gap-[10px]">
                    <div class="text-yellow-600 text-xs sm:text-sm font-medium sm:mb-1">{{ $t('directories.a_brief_summary_of_the_requests_active') }}</div>
                    <div class="text-xl sm:text-2xl font-bold text-yellow-900">{{summary.active}}</div>
                </div>
                <div class="sprint_stat__card bg-green-100 border border-green-300 grid gap-[10px]">
                    <div class="text-green-600 text-xs sm:text-sm font-medium sm:mb-1">{{ $t('directories.a_brief_summary_of_the_requests_completed') }}</div>
                    <div class="text-xl sm:text-2xl font-bold text-green-900">{{summary.completed}}</div>
                </div>
            </div>
        </a-col>
        <a-col
            :xs="24"
            :md="10"
            :xl="8"
            :xxl="8"
            class="h-full">
            <DrawerAside>
                <p v-if="edit" class="mb-2">{{ $t('directories.tags') }}</p>
                <Tags
                    v-if="edit"
                    showBorder
                    :model="model"
                    :pageName="pageName"
                    :useAction="actions && actions.edit ? true : false"
                    :related_object="client.id"
                    :contractor="client.org_admin.id" />

                <a-form-model
                    ref="ruleForm"
                    :model="form"
                    class="mini_form"
                    :rules="rules">
                    <ListView inline labelDark>
                        <ListViewItem>
                            <a-form-model-item v-if="edit" ref="name" prop="name">
                                <div class="input_row">
                                    <a-input
                                        v-model="form.name"
                                        ref="nameInput"
                                        inputType="ghost"
                                        class="font-semibold"
                                        size="small"
                                        :placeholder="$t('directories.appeal_name')"
                                        @change="dataChange({field: 'name', useTimer: true})" />
                                    <i class="fi fi-rr-pencil edit_icon_after" />
                                </div>
                            </a-form-model-item>
                            <span v-else class="font-semibold">{{ client.name }}</span>
                        </ListViewItem>

                        <ListViewItem v-if="formInfo.description && checkField({ key: 'description' })">
                            <a-form-model-item v-if="edit" ref="description" label="" prop="description">
                                <div class="input_row input_row--textarea">
                                    <a-textarea
                                        v-model="form.description"
                                        :placeholder="formInfo.description.placeholder || '123'"
                                        inputType="ghost"
                                        size="small"
                                        :auto-size="{ minRows: 1, maxRows: 5 }"
                                        @change="dataChange({field: 'description', useTimer: true})" />
                                    <i class="fi fi-rr-pencil edit_icon_after" />
                                </div>
                            </a-form-model-item>
                            <span v-else>{{ client.description }}</span>
                        </ListViewItem>

                        <ListViewItem :title="$t('directories.status')">
                            <a-form-model-item v-if="edit" ref="status" label="" prop="status">
                                <StatusSelect
                                    v-model="clientStatus"
                                    :loading="statusLoading"
                                    apiUrl="/app_info/select_list/?model=help_desk.CustomerCardStatusModel"
                                    @change="changeStatus" />
                            </a-form-model-item>
                            <a-tag v-else :color="client.status.color" size="large" block>
                                {{ client.status.name }}
                            </a-tag>
                        </ListViewItem>

                        <ListViewItem v-if="formInfo.inn && checkField({ key: 'inn' })" :title="formInfo.inn.title || $t('directories.organization_bin')">
                            <a-form-model-item v-if="edit" ref="inn" prop="inn">
                                <div class="input_row">
                                    <a-input
                                        v-model="form.inn"
                                        ref="nameInput"
                                        inputType="ghost"
                                        :maxLength="12"
                                        size="small"
                                        :placeholder="formInfo.inn.placeholder || $t('directories.enter_organization_bin')"
                                        @change="dataChange({field: 'inn', useTimer: true})">
                                        <template #suffix>
                                            <span style="color: #888888;">{{ form.inn.length }}/{{ binLength }}</span>
                                        </template>
                                    </a-input>
                                    <i class="fi fi-rr-pencil edit_icon_after" />
                                </div>
                            </a-form-model-item>
                            <span v-else>{{ client.inn }}</span>
                        </ListViewItem>

                        <ListViewItem v-if="formInfo.full_name && checkField({ key: 'full_name' })" :title="formInfo.full_name.title || $t('directories.full_name')">
                            <a-form-model-item v-if="edit" ref="full_name" prop="full_name">
                                <div class="input_row">
                                    <a-input
                                        v-model="form.full_name"
                                        ref="nameInput"
                                        inputType="ghost"
                                        size="small"
                                        :placeholder="formInfo.full_name.placeholder || $t('directories.full_name')"
                                        @change="dataChange({field: 'full_name', useTimer: true})" />
                                    <i class="fi fi-rr-pencil edit_icon_after" />
                                </div>
                            </a-form-model-item>
                            <span v-else>{{ client.full_name }}</span>
                        </ListViewItem>

                        <ListViewItem v-if="formInfo.legal_address && checkField({ key: 'legal_address' })" :title="formInfo.legal_address.title || $t('directories.legal_address')">
                            <a-form-model-item v-if="edit" ref="legal_address" prop="legal_address">
                                <div class="input_row">
                                    <a-input
                                        v-model="form.legal_address"
                                        ref="nameInput"
                                        inputType="ghost"
                                        size="small"
                                        :placeholder="formInfo.legal_address.placeholder || $t('directories.enter_legal_address')"
                                        @change="dataChange({field: 'legal_address', useTimer: true})" />
                                    <i class="fi fi-rr-pencil edit_icon_after" />
                                </div>
                            </a-form-model-item>
                            <span v-else>{{ client.legal_address }}</span>
                        </ListViewItem>

                        <ListViewItem v-if="formInfo.org_admin && checkField({ key: 'org_admin' })" :title="formInfo.org_admin.title || $t('directories.support_organization')">
                            <span>{{ client.org_admin.name }}</span>
                        </ListViewItem>
                    </ListView>

                    <div v-if="formInfo.admins" class="collapse_block">
                        <p v-if="edit || client?.admins?.length" class="mb-2">{{ formInfo.admins.title || $t('directories.admin_organization') }}</p>
                        <template v-if="edit && formInfo.admins.fields">
                            <div v-if="form.admins && form.admins.length">
                                <div
                                    v-for="(adminData, index) in form.admins"
                                    :key="index"
                                    class="contact_block">
                                    <a-form-model-item
                                        v-if="formInfo.admins.fields.bin"
                                        :rules="[
                                            { min: binLength, message: $t('directories.min_symbols', {count: binLength}), trigger: 'blur' },
                                            { max: binLength, message: $t('directories.max_symbols', {count: binLength}), trigger: 'blur' },
                                        ]"
                                        :prop="'admins.' + index + '.bin'">
                                        <a-popover
                                            v-model="binVisible[index]"
                                            :trigger="adminData.trigger"
                                            transitionName=""
                                            overlayClassName="select_bin_popup"
                                            :getPopupContainer="getPopupContainer"
                                            placement="bottomLeft">
                                            <div class="input_row">
                                                <a-input
                                                    v-model="adminData.bin"
                                                    :placeholder="formInfo.admins.fields.bin.placeholder || $t('directories.enter_bin')"
                                                    inputType="ghost"
                                                    :ref="`input_bin_${index}`"
                                                    :maxLength="binLength"
                                                    :disabled="adminData.edit"
                                                    noXPadding
                                                    @change="binChange($event, index, adminData)">
                                                    <template #prefix>
                                                        <i class="fi fi-rr-pencil" />
                                                    </template>
                                                    <template #suffix>
                                                        <a-spin :spinning="adminData.loading" size="small">
                                                            <span style="color: #888888;">{{ adminData.bin.length }}/{{ binLength }}</span>
                                                        </a-spin>
                                                    </template>
                                                </a-input>
                                            </div>

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
                                                        {{ $t('directories.close') }}
                                                    </a-button>
                                                </div>
                                            </template>
                                        </a-popover>
                                    </a-form-model-item>

                                    <a-form-model-item
                                        v-if="formInfo.admins.fields.name"
                                        :prop="'admins.' + index + '.name'">
                                        <div class="input_row">
                                            <a-input
                                                v-model="adminData.name"
                                                :placeholder="formInfo.admins.fields.name.placeholder || $t('directories.enter_name')"
                                                inputType="ghost"
                                                :disabled="adminData.selected || adminData.loading"
                                                noXPadding
                                                @change="changeOrgName($event, index)">
                                                <template #prefix>
                                                    <i class="fi fi-rr-pencil" />
                                                </template>
                                            </a-input>
                                        </div>
                                    </a-form-model-item>

                                    <div class="flex items-center gap-2">
                                        <a-button
                                            v-if="adminData.add"
                                            type="flat_primary"
                                            size="small"
                                            :loading="adminData.loading"
                                            @click="saveOrg(index)">
                                            {{ $t('directories.add') }}
                                        </a-button>
                                        <a-button
                                            v-if="form.admins.length > 1"
                                            type="flat_danger"
                                            size="small"
                                            @click="deleteAdmins(index)">
                                            {{ $t('directories.delete') }}
                                        </a-button>
                                    </div>
                                </div>
                            </div>
                            <a-button type="link" size="small" flaticon icon="fi-rr-plus-small" class="mt-2 mb-2" @click="addAdmin()">
                                {{ $t('directories.add_more') }}
                            </a-button>
                        </template>

                        <template v-else>
                            <div v-if="formInfo.admins.fields" class="mb-2">
                                <div
                                    v-for="(admins, index) in client.admins"
                                    :key="index"
                                    class="contact_block">
                                    <ListView size="small">
                                        <ListViewItem v-if="admins.bin && formInfo.admins.fields.bin" :title="formInfo.admins.fields.bin.title || $t('directories.bin')">
                                            {{ admins.bin }}
                                        </ListViewItem>
                                        <ListViewItem v-if="admins.name && formInfo.admins.fields.name" :title="formInfo.admins.fields.name.title || $t('directories.enter_name')">
                                            {{ admins.name }}
                                        </ListViewItem>
                                    </ListView>
                                </div>
                            </div>
                        </template>
                    </div>
                </a-form-model>
            </DrawerAside>
        </a-col>
    </a-row>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { clientFormModel, clientForm, clientFormKey } from '../../../utils/utils.js'
import { mergeForm } from '@/utils/utils.js'
import { errorHandler } from '@/utils/index.js'
let reloadTimer;
let timer;
let clientTimer;
let messageTimer;
let binTimer;
let nameTimer;
let orgDeleteTimer;
export default {
    components: {
        Tags: () => import('@apps/UIModules/Tags.vue'),
        DrawerAside: () => import('@apps/UIModules/DrawerAside'),
        StatusSelect: () => import('@apps/DrawerSelect/StatusSelect.vue'),
    },
    props: {
        client: {
            type: Object,
            required: true
        },
        actions: {
            type: Object,
            default: () => null
        },
        model: {
            type: String,
            default: ""
        },
        pageName: {
            type: String,
            default: ""
        },
        edit: {
            type: Boolean,
            default: false
        },
        clientUpdate: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        storeFormInfo() {
            return this.$store.state.formInfo?.formInfo?.[clientFormKey] || {}
        },
        formInfo() {
            return mergeForm(clientForm, this.storeFormInfo)
        },
        taskComponent() {
            if(this.viewType === 'table')
                return () => import('./components/Table.vue')
            else
                return () => import('./components/Kanban.vue')
        }
    },
    created() {
        if(this.edit) {
            const ticketForm = JSON.parse(JSON.stringify(this.client))
            if(ticketForm.org_admin)
                ticketForm.org_admin = ticketForm.org_admin.id
            if(ticketForm.budget_program_administrator)
                ticketForm.budget_program_administrator = ticketForm.budget_program_administrator.id

            if(!ticketForm.admins?.length) {
                const blank = {
                    bin: '',
                    name: '',
                    selected: false,
                    loading: false,
                    trigger: 'none',
                    results: [],
                    next: null,
                    page: 1,
                    add: true,
                    key: Date.now()
                }
                ticketForm.admins = [blank]
            } else {
                ticketForm.admins = ticketForm.admins.map(item => {
                    return {
                        ...item,
                        selected: false,
                        loading: false,
                        trigger: 'none',
                        results: [],
                        next: null,
                        page: 1,
                        edit: true,
                        key: item.id
                    }
                })
            }

            this.clientStatus = ticketForm.status
            this.form = ticketForm

            // if(!this.form.contact_persons?.length)
            //     this.addContact()
        }
    },
    data() {
        return {
            formKey: clientFormKey,
            deleteLoading: false,
            activeKey: ['1'],
            binLength: 12,
            summary: {
                total:0,
                active:0,
                completed:0,
            },
            statusLoading: false,
            binVisible: {
                0: false
            },
            clientStatus: null,
            rules: {
                org_admin: [{ required: true, message: this.$t('directories.required_field'), trigger: 'change' }],
                inn: [
                    { required: true, message: this.$t('directories.required_field'), trigger: 'change' },
                    { min: 12, message: this.$t('directories.min_symbols', {count: 12}), trigger: 'blur' },
                    { max: 12, message: this.$t('directories.max_symbols', {count: 12}), trigger: 'blur' },
                ],
            },
            form: JSON.parse(JSON.stringify(clientFormModel)),
            excludeFields: [],
            viewType: 'table',
            listType: [
                {
                    key: 'table',
                    title: this.$t('directories.list')
                },
                {
                    key: 'kanban',
                    title: this.$t('directories.kanban')
                }
            ],
            listModel: "help_desk.HelpDeskTicketModel",
            listPageName: `list_help_desk.tickets_${this.client.id}`,
            mainListModel: "help_desk.CustomerCardModel",
            mainListPageName: "list_help_desk.CustomerCardModel"
        }
    },
    mounted() {
        this.getSummary()
    },
    methods: {
        async changeStatus(item) {
            try {
                this.statusLoading = true
                const { data } = await this.$http.post(`/help_desk/customer_cards/${this.client.id}/status/`, {
                    status: item.code
                })
                if(data) {
                    this.$message.success(this.$t('directories.status_changed'))
                    this.listReload()
                }
            } catch(error) {
                errorHandler({error})
            } finally {
                this.statusLoading = false
            }
        },
        async getSummary() {
            try {
                const { data } = await this.$http.get(`/help_desk/customer_cards/${this.client.id}/summary/`)
                if(data) {
                    this.summary = data
                }
            } catch(error) {
                errorHandler({error})
            }
        },
        changeOrgName(e, index) {
            const name = e.target.value
            const org = this.form.admins[index]
            if(org.edit) {
                clearTimeout(nameTimer)
                nameTimer = setTimeout(() => {
                    this.$refs.ruleForm.validate(async valid => {
                        if(valid) {
                            if(org) {
                                try {
                                    await this.$http.patch(`/help_desk/admins/${org.id}/`, {
                                        name
                                    })
                                } catch(error) {
                                    errorHandler({error})
                                }
                            }
                        } else {
                            clearTimeout(messageTimer)
                            messageTimer = setTimeout(() => {
                                this.$message.warning(this.$t('fill_required_fields'))
                            }, 500)
                            return false
                        }
                    })
                }, 500)
            }
        },
        saveOrg(index) {
            this.$refs.ruleForm.validate(async valid => {
                if(valid) {
                    const org = this.form.admins[index]
                    if(org) {
                        try {
                            this.$set(this.form.admins[index], 'loading', true)
                            const { data } = await this.$http.post('/help_desk/admins/', {
                                ...org,
                                org_admin: this.form.org_admin
                            })
                            if(data) {
                                this.$set(this.form.admins[index], 'add', false)
                                this.$set(this.form.admins[index], 'edit', true)
                                this.$set(this.form.admins[index], 'id', data.id)
                                this.dataChange({field: 'admins', useTimer: true, valueKey: 'id', multiple: true})
                                this.$message.success(this.$t('directories.organization_saved'))
                            }
                        } catch(error) {
                            errorHandler({error})
                        } finally {
                            this.$set(this.form.admins[index], 'loading', false)
                        }
                    }
                } else {
                    clearTimeout(messageTimer)
                    messageTimer = setTimeout(() => {
                        this.$message.warning(this.$t('fill_required_fields'))
                    }, 500)
                    return false
                }
            })
        },
        deleteAdmins(index) {
            const org = this.form.admins[index]
            if(org) {
                this.form.admins.splice(index, 1)
                if(org.edit) {
                    clearTimeout(orgDeleteTimer)
                    orgDeleteTimer = setTimeout(() => {
                        this.dataChange({field: 'admins', useTimer: true, valueKey: 'id', multiple: true})
                        this.$message.success(this.$t('directories.organization_removed'))
                    }, 300)
                }
            }
        },
        addAdmin(useFocus = true) {
            const blank = {
                bin: '',
                name: '',
                selected: false,
                loading: false,
                trigger: 'none',
                results: [],
                next: null,
                page: 1,
                add: true,
                key: Date.now()
            }
            this.form.admins.push(blank)
            const index = this.form.admins.length - 1
            this.$set(this.binVisible, index, false)
            if(useFocus)
                setTimeout(() => {
                    this.focusAdminBin(index)
                }, 150)
        },
        selectOrg(org, index) {
            this.$set(this.form.admins, index, {
                ...this.form.admins[index],
                ...org,
                key: Date.now(),
                add: false,
                edit: true
            })
            this.$set(this.binVisible, index, false)
            this.dataChange({field: 'admins', useTimer: true, valueKey: 'id', multiple: true})
            this.$message.success(this.$t('directories.organization_saved'))
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
            this.form.admins = [{
                ...clientFormModel.admins[0],
                add: true,
                key: Date.now()
            }]
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
                                    add: false,
                                    edit: true
                                })
                                this.$set(this.form.admins[index], 'trigger', 'none')
                                this.$set(this.binVisible, index, false)
                                this.dataChange({field: 'admins', useTimer: true, valueKey: 'id', multiple: true})
                                this.$message.success(this.$t('directories.organization_saved'))
                            } else {
                                this.$set(this.binVisible, index, true)
                            }
                        } else {
                            this.$set(this.form.admins[index], 'add', true)
                        }
                    } catch(error) {
                        errorHandler({error})
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
        clientHandler(index) {
            this.$refs.ruleForm.validate(valid => {
                if(valid) {
                    if(!this.form.contact_persons?.[index]?.add)
                        this.form.contact_persons[index].edit = true
                    clearTimeout(clientTimer)
                    clientTimer = setTimeout(() => {
                        this.clientUpdateHandler()
                    }, 1000)
                } else {
                    clearTimeout(messageTimer)
                    messageTimer = setTimeout(() => {
                        this.$message.warning(this.$t('fill_required_fields'))
                    }, 500)
                    return false
                }
            })
        },
        async clientUpdateHandler() {
            try {
                this.deleteLoading = true
                const contactPersons = this.form.contact_persons || []
                const isEmptyContact = (item) =>
                    !item.name?.trim() &&
                    !item.email?.trim() &&
                    !item.telegram?.trim() &&
                    !item.phone?.trim() &&
                    !item.post?.trim()


                await this.form.contact_persons.forEach(async (contectPerson, index) => {
                    if (contectPerson.add && !isEmptyContact(contectPerson)) {
                        const payload = contectPerson
                        const url = `/help_desk/customer_cards/${this.client.id}/contact_persons/add/`
                        const { data } = await this.$http.post(url, payload)
                        this.$set(this.form.contact_persons[index], 'id', data.id)
                        this.$delete(this.form.contact_persons[index], 'add')
                    }
                });

                const formCopy = { ...this.form }
                const editContacts = formCopy.contact_persons.filter(f => f.edit)
                for (const contact of editContacts) {
                    await this.$http.put(`/help_desk/customer_cards/${this.client.id}/contact_persons/update/`, {
                        ...contact,
                        contact_person: contact.id
                    })
                    const editIndex = this.form.contact_persons.findIndex(f => f.id === contact.id)
                    if(editIndex !== -1 && this.form.contact_persons[editIndex]) {
                        this.$delete(this.form.contact_persons[editIndex], 'edit')
                    }
                }
            } catch(error) {
                errorHandler({error})
            } finally {
                this.deleteLoading = false
            }
        },
        addContact() {
            this.form.contact_persons.push({
                ...clientFormModel.contact_persons,
                add: true
            })
        },
        async deleteContactApi(contact, index) {
            if(contact.add) {
                this.form.contact_persons.splice(index, 1)
            } else {
                try {
                    this.deleteLoading = true
                    await this.$http.post(`/help_desk/customer_cards/${this.client.id}/contact_persons/remove/`, {
                        contact_person: contact.id
                    })
                    this.form.contact_persons.splice(index, 1)
                    if(!this.form.contact_persons?.length) {
                        this.addContact()
                    }
                } catch(error) {
                    errorHandler({error})
                } finally {
                    this.deleteLoading = false
                }
            }
        },
        checkField({key, type = 'object'}) {
            if(this.edit)
                return true
            else {
                if(type === 'array') {
                    if(this.client[key]?.length)
                        return true
                } else {
                    if(this.client[key])
                        return true
                }
            }
            return false
        },
        dataChange({field, useTimer = false, valueKey = false, multiple = false}) {
            this.$refs.ruleForm.validate(valid => {
                if(valid) {
                    let value = this.form[field]
                    if(valueKey) {
                        if(multiple) {
                            value = this.form[field].map(fld => fld[valueKey])
                        } else {
                            value = this.form[field][valueKey]
                        }
                    }
                    if(useTimer) {
                        clearTimeout(timer)
                        timer = setTimeout(() => {
                            this.patchField(value, field)
                        }, 600)
                    } else {
                        this.patchField(value, field)
                    }
                } else {
                    return false
                }
            })
        },
        async patchField(value, field) {
            try {
                if(field === 'name' && !value) {
                    this.$message.warning(this.$t('directories.name_required'))
                    return false
                }
                const { data } = await this.$http.patch(`/help_desk/customer_cards/${this.client.id}/`, {
                    [field]: value
                })
                if(data) {
                    this.clientUpdate(data)
                    this.listReload()
                }
            } catch(error) {
                errorHandler({error})
            }
        },
        listReload() {
            clearTimeout(reloadTimer)
            reloadTimer = setTimeout(() => {
                eventBus.$emit(`update_filter_${this.mainListModel}_${this.mainListPageName}`)
            }, 1000)
        },
        getPopupContainer() {
            return this.$refs.clientHeaderWrapper
        }
    }
}
</script>

<style lang="scss" scoped>
/* ✅ минимально: карандаш ПОСЛЕ input */
.input_row{
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    min-width: 0;

    &::v-deep{
        .ant-input,
        .ant-input-affix-wrapper{
            width: 100%;
            min-width: 0;
        }
    }

    &--textarea{
        align-items: flex-start;
        .edit_icon_after{
            margin-top: 6px;
        }
    }
}
.edit_icon_after{
    color: #888888;
    font-size: 14px;
    flex: 0 0 auto;
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
.contact_block{
    background: #fff;
    padding: 10px 15px;
    border-radius: 12px;
    &:not(:last-child){
        margin-bottom: 10px;
    }
}
.collapse_block{
    border-top: 1px solid #DADADA;
    padding-top: 15px;
    margin-top: 15px;
    &::v-deep{
        .ant-collapse-content > .ant-collapse-content-box{
            padding: 0px;
        }
        .ant-collapse > .ant-collapse-item > .ant-collapse-header .ant-collapse-arrow{
            top: 6px!important;
            left: 0!important;
            transform: initial!important;
            &.arrow_active{
                transform: rotate(90deg)!important;
            }
        }
        .ant-collapse-header{
            color: var(--text);
            padding-left: 25px;
            padding-right: 0px;
            padding-top: 0px;
        }
        .ant-collapse-borderless > .ant-collapse-item{
            border-bottom: 0px;
        }
        .ant-collapse-borderless{
            background-color: transparent;
        }
    }
}
</style>

<style lang="scss">
.color_selector{
    .ant-popover-inner-content{
        padding: 5px;
    }
    &.ant-popover-placement-bottom,
    &.ant-popover-placement-bottomLeft,
    &.ant-popover-placement-bottomRight{
        padding-top: 0px;
    }
    &.ant-popover-placement-top,
    &.ant-popover-placement-topLeft,
    &.ant-popover-placement-topRight{
        padding-bottom: 0px;
    }
    .ant-popover-arrow{
        display: none;
    }
}
@keyframes fade-in-up {
    0% {
        opacity: 0;
        transform: translateY(10px);
    }
    100% {
        opacity: 1;
        transform: translateY(0);
    }
}
</style>

<style lang="scss" scoped>
.drawer_item{
    &:not(:last-child){
        margin-bottom: 10px;
    }
    &__label{
        opacity: 0.6;
        margin-bottom: 1px;
    }
}
.body_wrapper{
    padding: 20px;
    background: #F8F9FD;
    border-radius: 6px;
    height: 100%;
}
.client_contact{
    background: #f1f2f7;
    padding: 15px;
    border-radius: 6px;
    &:not(:last-child){
        margin-bottom: 10px;
    }
}
.sprint_name{
    font-weight: 400;
    font-size: 24px;
    line-height: 24px;
    color: #000;
}
.sprint_stat{
    &__card{
        padding: 20px 30px;
        border-radius: 8px;
        color: #000;
        &.green{
            background: #bff3d1;
        }
        &.red{
            background: #f3c0c0;
        }
        &.blue{
            background: rgb(223, 237, 255);
        }
        .label{
            font-weight: 400;
            font-size: 16px;
            line-height: 16px;
        }
    }
}
</style>
