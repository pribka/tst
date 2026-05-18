<template>
    <a-modal
        :width="isMobile ? '100%' : 675"
        :afterClose="afterClose"
        :visible="visible"
        destroyOnClose
        :title="modalTitle"
        :wrapClassName="`contact_person_modal ${isMobile ? 'contact_person_modal_fullscreen' : ''}`"
        :dialog-style="isMobile ? { top: '0px', paddingBottom: '0' } : { top: '20px' }"
        @afterVisibleChange="afterVisibleChange"
        @cancel="visible = false">

        <template v-if="!formLoading">
            <a-form-model
                v-if="formInfo.contact_persons && formInfo.contact_persons.fields"
                ref="ruleForm"
                :model="form"
                class="mini_form">
                <a-spin :spinning="dataLoading" size="small">
                    <div
                        v-for="(contact_person, index) in form.contact_persons"
                        :key="index"
                        class="contact_block">
                        <a-form-model-item
                            v-if="formInfo.contact_persons.fields.name"
                            :rules="{
                                required: true,
                                message: $t('directories.required_field'),
                                trigger: 'blur',
                            }"
                            :prop="'contact_persons.' + index + '.name'">
                            <a-input
                                v-model="contact_person.name"
                                :placeholder="formInfo.contact_persons.fields.name.placeholder || $t('directories.enter_full_name')"
                                inputType="ghost"
                                @pressEnter="formSubmit()">
                                <template #prefix>
                                    <i class="fi fi-rr-pencil" />
                                </template>
                            </a-input>
                        </a-form-model-item>

                        <a-form-model-item
                            v-if="formInfo.contact_persons.fields.phone"
                            :prop="'contact_persons.' + index + '.phone'">
                            <a-input
                                v-model="contact_person.phone"
                                :placeholder="formInfo.contact_persons.fields.phone.placeholder || $t('directories.enter_phone')"
                                inputType="ghost"
                                @pressEnter="formSubmit()">
                                <template #prefix>
                                    <i class="fi fi-rr-pencil" />
                                </template>
                            </a-input>
                        </a-form-model-item>

                        <a-form-model-item
                            v-if="formInfo.contact_persons.fields.telegram"
                            :prop="'contact_persons.' + index + '.telegram'">
                            <a-input
                                v-model="contact_person.telegram"
                                :placeholder="formInfo.contact_persons.fields.telegram.placeholder || $t('directories.enter_telegram')"
                                inputType="ghost"
                                @pressEnter="formSubmit()">
                                <template #prefix>
                                    <i class="fi fi-rr-pencil" />
                                </template>
                            </a-input>
                        </a-form-model-item>

                        <a-form-model-item
                            v-if="formInfo.contact_persons.fields.email"
                            :prop="'contact_persons.' + index + '.email'"
                            :rules="[
                                { type: 'email', message: $t('directories.email_invalid'), trigger: 'blur' }
                            ]">
                            <a-input
                                v-model="contact_person.email"
                                :placeholder="formInfo.contact_persons.fields.email.placeholder || $t('directories.enter_email')"
                                inputType="ghost"
                                @pressEnter="formSubmit()">
                                <template #prefix>
                                    <i class="fi fi-rr-pencil" />
                                </template>
                            </a-input>
                        </a-form-model-item>
                        <a-form-model-item v-if="formInfo.contact_persons.fields.post_inst" :prop="'contact_persons.' + index + '.post_inst'" class="pl-3">
                            <ListViewModal
                                v-if="form.org_admin"
                                :endpoint="`/help_desk/contact_person_post/?contractor=${form.org_admin}`"
                                tableType="helpdesk_positions_select"
                                pageName="help_desk.ContactPersonPostModel_all"
                                title="Должности"
                                model="help_desk.ContactPersonPostModel"
                                @select="selectPost($event, index)"
                                :add="addPost"
                                ref="listViewModalPostRef">
                                <template v-slot:headerLeft="{ rowSelected }">
                                    <component
                                        v-if="rowSelected"
                                        :is="slaSelectComponent"
                                        :selectItem="rowSelected"
                                        :params="{
                                            contractor: form.org_admin
                                        }"
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
                                :params="{
                                    contractor: form.org_admin
                                }"
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
                                        @click="addPost()"/>
                                </template>
                            </DSelect>
                            <PositionFormModal
                                v-if="form.org_admin"
                                :contractor="form.org_admin"
                                slaSelect
                                model="help_desk.ContactPersonPostModel"
                                @change="changePostModal($event, index)" />
                        </a-form-model-item>
                        <a-form-model-item v-if="formInfo.contact_persons.fields.is_main" class="pl-3">
                            <a-checkbox v-model="contact_person.is_main">
                                {{ formInfo.contact_persons.fields.is_main.title || $t('directories.is_main') }}
                            </a-checkbox>
                        </a-form-model-item>
                        <a-form-model-item v-if="slaSelect" class="pl-3" :help="slaSelectedInfo && slaSelectedInfo.from && `Источник: ${slaSelectedInfo.from}`">
                            <component
                                :is="slaSelectComponent"
                                :listUpdate="false"
                                useInject
                                inputType="ghost"
                                :slaInitSelected="slaSelected"
                                :slaSelectedInfo="slaSelectedInfo"
                                :params="{contractor: contractor}"
                                @change="SLAChange">
                                <template #prefixIcon>
                                    <i class="fi fi-rr-bookmark mr-3" />
                                </template>
                            </component>
                        </a-form-model-item>
                        <a-form-model-item v-if="formInfo.contact_persons.fields.comment" :prop="'contact_persons.' + index + '.comment'">
                            <a-textarea v-model="contact_person.comment" :placeholder="formInfo.contact_persons.fields.comment.placeholder || $t('directories.enter_comment')"  @pressEnter="formSubmit()">
                            </a-textarea>
                        </a-form-model-item>
                    </div>
                </a-spin>
            </a-form-model>
        </template>
        <a-skeleton v-else active />
        <template #footer>
            <!-- MOBILE: как в примере -->
            <div v-if="isMobile" class="flex items-center w-full">
                <a-button
                    v-if="formInfo.contact_persons && formInfo.contact_persons.fields"
                    type="primary"
                    size="large"
                    block
                    class="flex-1"
                    :loading="loading"
                    :disabled="formLoading"
                    @click="formSubmit()">
                    {{ edit ? $t('directories.save') : $t('directories.add') }}
                </a-button>
            </div>

            <!-- DESKTOP: как было -->
            <div v-else class="flex gap-1 items-center">
                <a-button
                    v-if="formInfo.contact_persons && formInfo.contact_persons.fields"
                    type="primary"
                    size="large"
                    :loading="loading"
                    :disabled="formLoading"
                    @click="formSubmit()">
                    {{ edit ? $t('directories.save') : $t('directories.add') }}
                </a-button>

                <a-button type="ui_ghost" ghost size="large" @click="visible = false">
                    {{ $t('directories.cancel') }}
                </a-button>
            </div>
        </template>
    </a-modal>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { clientForm, clientFormKey } from '../utils/utils.js'
import { mergeForm } from '@/utils/utils.js'
import { errorHandler } from '@/utils/index.js'
export default {
    components: {
        DSelect: () => import('@apps/DrawerSelect/Select.vue'),
        PositionFormModal: () => import('./PositionFormModal.vue'),
        ListViewModal: () => import("@/components/ListView/ListViewModal.vue")
    },
    props: {
        contractor: {
            type: String,
            default: ""
        },
        slaSelect: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            getPostLoading: false,
            initListPost: [],
            visible: false,
            client: null,
            slaSelected: null,
            slaSelectedInfo: null,
            clientId: null,
            loading: false,
            dataLoading: false,
            edit: false,
            formLoading: true,
            editContactPerson: null,
            model: 'help_desk.ContactPersonModel',
            form: {
                contact_persons: [
                    {
                        key: Date.now(),
                        name:"",
                        email:"",
                        telegram:"",
                        phone:"" ,
                        post_inst: "",
                        is_main: false,
                        comment: ''
                    }
                ]
            }
        }
    },
    computed: {
        slaSelectComponent() {
            if (this.slaSelect)
                return () => import('./SLASelect.vue')
            return null
        },
        storeFormInfo() {
            return this.$store.state.formInfo?.formInfo?.[clientFormKey] || {}
        },
        formInfo() {
            return mergeForm(clientForm, this.storeFormInfo)
        },
        modalTitle() {
            return this.edit ? this.$t('directories.edit_contact_person') : this.$t('directories.add_contact_person')
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    methods: {
        SLAChange(value) {
            this.slaSelected = value.id
            this.slaSelectedInfo = value
        },
        changePostModal(data, index) {
            this.$set(this.form.contact_persons[index], 'post_inst', data.id)
            this.initListPost.push(data)
        },
        addPost() {
            eventBus.$emit('open_modal_position_add')
        },
        openAllPost(index) {
            this.$nextTick(() => {
                if (this.$refs?.listViewModalPostRef?.[index])
                    this.$refs.listViewModalPostRef[index].open()
            })
        },
        selectPost(post, index) {
            if (post) {
                this.$set(this.form.contact_persons[index], 'post_inst', post.id)
                this.initListPost = [{ ...post }]
            }
        },
        async getFormInfo() {
            try {
                if (!Object.keys(this.storeFormInfo)?.length)
                    await this.$store.dispatch('formInfo/getFormInfo', { form: clientFormKey })
            } catch (error) {
                console.log(error)
            } finally {
                this.formLoading = false
            }
        },
        afterClose() {
            this.initListPost = []
            this.client = null
            this.clientId = null
            this.slaSelected = null
            this.slaSelectedInfo = null
            this.form = {
                contact_persons: [
                    {
                        key: Date.now(),
                        name: "",
                        email: "",
                        telegram: "",
                        phone: "",
                        post_inst: "",
                        is_main: false,
                        comment: ''
                    }
                ]
            }
            this.edit = false
            this.editContactPerson = null
        },
        afterVisibleChange(vis) {
            if (vis)
                this.getClient()
        },
        async getClient() {
            try {
                this.dataLoading = true
                const { data } = await this.$http.get(`/help_desk/customer_cards/${this.clientId}/`)
                if (data) {
                    this.client = data
                    await this.getFormInfo()
                }
            } catch (error) {
                errorHandler({ error, show: false })
            } finally {
                this.dataLoading = false
            }
        },
        editPerson() {
            const payload = {
                contact_person: this.editContactPerson.id,
                ...this.form.contact_persons[0]
            }
            this.$http.put(`help_desk/customer_cards/${this.client.id}/contact_persons/update/`, payload)
                .then(async ({ data }) => {
                    if (data) {
                        if (this.slaSelect)
                            await this.saveSLA(data)
                        this.$emit('change', data)
                        eventBus.$emit('helpdesc_return_contact', data)
                        eventBus.$emit(`update_filter_${this.model}`)
                        eventBus.$emit(`update_filter_help_desk.CustomerCardModel_list_help_desk.CustomerCardModel`)
                        this.$message.success(this.$t('directories.contact_person_updated'))
                        this.visible = false
                    }
                })
                .catch(error => {
                    errorHandler({ error })
                })
        },
        async saveSLA(data) {
            if (this.slaSelected) {
                try {
                    await this.$http.post('/sla/set_objects/', {
                        sla: this.slaSelected,
                        related_objects: [data.id]
                    })
                } catch (error) {
                    errorHandler({ error })
                }
            }
        },
        formSubmit() {
            this.$refs.ruleForm.validate(async valid => {
                if (valid) {
                    if (this.edit) {
                        this.editPerson()
                        return
                    }
                    try {
                        this.loading = true
                        const contactPersons = this.form.contact_persons[0] || []
                        const { data } = await this.$http.post(`/help_desk/customer_cards/${this.client.id}/contact_persons/add/`, contactPersons)
                        if (data) {
                            if (this.slaSelect)
                                await this.saveSLA(data)
                            this.visible = false
                            eventBus.$emit('helpdesc_return_contact', data)
                            eventBus.$emit(`update_filter_${this.model}`)

                            eventBus.$emit(`update_filter_help_desk.CustomerCardModel_list_help_desk.CustomerCardModel`)

                            this.$message.success(this.$t('directories.contact_assigned'))
                        }
                    } catch (error) {
                        errorHandler({ error })
                    } finally {
                        this.loading = false
                    }
                } else
                    return false
            })
        }
    },
    mounted() {
        eventBus.$on('add_ticket_contact', clientId => {
            this.clientId = clientId
            if (this.contractor)
                this.form.org_admin = this.contractor
            this.visible = true
        })

        eventBus.$on('edit_contact_person_modal', ({ client, contactPerson }) => {
            this.clientId = client.id
            this.editContactPerson = contactPerson
            this.edit = true

            const formData = {
                contact_persons: [
                    {
                        key: Date.now(),
                        name: contactPerson.name || "",
                        email: contactPerson.email || "",
                        telegram: contactPerson.telegram || "",
                        phone: contactPerson.phone || "",
                        post_inst: contactPerson?.post_inst?.id || null,
                        is_main: Boolean(contactPerson.is_main),
                        comment: contactPerson.comment || ""
                    }
                ]
            }
            if (this.contractor)
                formData.org_admin = this.contractor
            if (contactPerson.post_inst)
                this.initListPost = [contactPerson.post_inst]
            if (contactPerson.sla?.id) {
                this.slaSelected = contactPerson.sla.id
                this.slaSelectedInfo = contactPerson.sla
            }

            this.form = { ...formData }
            this.visible = true
        })
    },
    beforeDestroy() {
        eventBus.$off('add_ticket_contact')
        eventBus.$off('edit_contact_person_modal')
    }
}
</script>

<style lang="scss">
/* ===== MOBILE FULLSCREEN MODAL ===== */
.contact_person_modal_fullscreen {
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
.contact_block{
    background: #f7f9fc;
    padding: 5px 15px;
    border-radius: 8px;
    &:not(:last-child){
        margin-bottom: 10px;
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

/* чуть компактнее на мобилке, если надо */
@media (max-width: 768px) {
    .contact_block{
        padding: 8px 12px;
    }
}
</style>
