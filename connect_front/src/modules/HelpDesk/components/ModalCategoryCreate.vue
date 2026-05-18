<template>
    <a-modal
        :visible="visible"
        @cancel="close"
        @afterVisibleChange="afterVisibleChange"
        :width="400"
        :afterClose="afterClose"
        :footer="null"
        destroyOnClose>
        <template #title>
            {{ $t('helpdesk.category') }}
        </template>
        <a-form-model
            ref="formRef"
            :model="form"
            :rules="rules">
            <a-form-model-item prop="name" class="mb-2">
                <a-input
                    ref="nameInput"
                    v-model="form.name"
                    size="large"
                    :placeholder="$t('helpdesk.category_name')" />
            </a-form-model-item>
            <a-form-model-item
                v-if="contractorSelect"
                ref="contractor"
                :label="$t('helpdesk.support_organization')"
                :rules="{
                    required: true,
                    message: $t('helpdesk.required_field'),
                    trigger: 'blur'
                }"
                prop="contractor">
                <DSelect
                    v-model="form.contractor"
                    apiUrl="/contractor_permissions/organizations/"
                    class="w-full"
                    oneSelect
                    size="large"
                    firstSelected
                    :placeholder="$t('helpdesk.support_organization')"
                    :listObject="false"
                    labelKey="name"
                    :params="{
                        permission_type: 'help_desk_admin'
                    }"
                    :default-active-first-option="false"
                    :filter-option="false"
                    :not-found-content="null" />
            </a-form-model-item>
            <a-form-model-item v-if="slaSelect" label="SLA">
                <component
                    :is="slaSelectComponent"
                    :listUpdate="false"
                    useInject
                    :slaInitSelected="slaSelected"
                    :params="{contractor: contractor}"
                    @change="SLAChange" />
            </a-form-model-item>
            <a-button block type="primary" size="large" :loading="loading" class="mt-2" @click="submit()">
                {{ editMode ? $t('helpdesk.save') : $t('helpdesk.create') }}
            </a-button>
        </a-form-model>
    </a-modal>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'
export default {
    components: {
        DSelect: () => import("@apps/DrawerSelect/Select.vue")
    },
    props: {
        contractor: {
            type: String,
            default: ""
        },
        model: {
            type: String,
            default: 'help_desk.HelpDeskTicketCategoryModel'
        },
        afterCreate: {
            type: Function,
            default: () => {}
        },
        contractorSelect: {
            type: Boolean,
            default: false
        },
        slaSelect: {
            type: Boolean,
            default: false
        },
        eventsEnabled: {
            type: Boolean,
            default: true
        }
    },
    computed: {
        slaSelectComponent() {
            if(this.slaSelect)
                return () => import('./SLASelect.vue')
            return null
        }
    },
    data() {
        return {
            visible: false,
            loading: false,
            slaSelected: null,
            form: {
                name: '',
                contractor: ''
            },
            rules: {
                name: [
                    {
                        required: true,
                        message: this.$t('helpdesk.required_field'),
                        trigger: "change",
                    },
                ],
            },
            editMode: false
        }
    },
    mounted() {
        if(this.eventsEnabled) {
            eventBus.$on('open_modal_category_create', ({ record }) => this.startEdit(record))
            eventBus.$on('open_modal_category_add', () => {
                this.visible = true
            })
        }
    },
    beforeDestroy() {
        if(this.eventsEnabled) {
            eventBus.$off('open_modal_category_create')
            eventBus.$off('open_modal_category_add')
        }
    },
    methods: {
        SLAChange(value) {
            this.slaSelected = value.id
        },
        afterVisibleChange(vis) {
            if(vis) {
                if(this.contractor)
                    this.form.contractor = this.contractor
                this.$nextTick(() => {
                    if(this.$refs.nameInput)
                        this.$refs.nameInput.focus()
                })
            }
        },
        afterClose() {
            this.slaSelected = null
            this.form = {
                name: '',
                contractor: ''
            }
            this.editMode = false
        },
        async saveSLA(data) {
            if(this.slaSelected) {
                try {
                    await this.$http.post('/sla/set_objects/', {
                        sla: this.slaSelected,
                        related_objects: [data.id]
                    })
                } catch(error) {
                    errorHandler({error})
                }
            }
        },
        submit() {
            this.$refs.formRef
                .validate(async valid => {
                    if (valid) {
                        try {
                            this.loading = true
                            const payload = JSON.parse(JSON.stringify(this.form))
                            if(this.editMode) {
                                const { data } = await this.$http.put(`help_desk/ticket_categories/${this.form.id}/`, payload)
                                if(data) {
                                    if(this.slaSelected)
                                        await this.saveSLA(data)
                                    this.$message.success(this.$t('helpdesk.category_updated'))
                                    eventBus.$emit(`update_filter_${this.model}`)
                                    this.afterCreate(data)

                                    this.close()
                                }
                            } else {
                                const { data } = await this.$http.post('/help_desk/ticket_categories/', payload)
                                if(data) {
                                    if(this.slaSelected)
                                        await this.saveSLA(data)
                                    this.$message.success(this.$t('helpdesk.category_created'))
                                    eventBus.$emit(`update_filter_${this.model}`)
                                    this.afterCreate(data)

                                    this.close()
                                }
                            }
                        } catch(error) {
                            errorHandler({error})
                        } finally {
                            this.loading = false
                        }
                    }
                })
        },
        startEdit(record) {
            this.form = {
                ...this.form,
                ...record
            }
            if(record.sla)
                this.slaSelected = record.sla.id
            this.editMode = true
            this.open()
        },
        openModal() {
            this.visible = true
        },
        open() {
            this.visible = true
        },
        close() {
            this.visible = false
        },
    }
}

</script>