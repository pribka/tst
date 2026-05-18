<template>
    <a-modal
        :visible="visible"
        @afterVisibleChange="afterVisibleChange"
        :width="400"
        @cancel="visible = false"
        :footer="null"
        destroyOnClose>
        <template #title>
            {{ $t('directories.position') }}
        </template>
        <a-form-model
            ref="formRef"
            :model="form"
            :rules="rules">
            <a-form-model-item prop="name" class="mb-2">
                <a-input 
                    v-model="form.name"
                    ref="nameInput"
                    size="large" 
                    :placeholder="$t('directories.position_print')" />
            </a-form-model-item>
            <a-form-model-item
                v-if="contractorSelect"
                ref="contractor"
                :label="$t('directories.support_organization')"
                :rules="{
                    required: true,
                    message: $t('directories.required_field'),
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
                    :placeholder="$t('directories.support_organization')"
                    :listObject="false"
                    labelKey="name"
                    :params="{
                        permission_type: 'help_desk_admin'
                    }"
                    :default-active-first-option="false"
                    :filter-option="false"
                    :not-found-content="null" />
            </a-form-model-item>
        </a-form-model>
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
            {{ edit ? $t('directories.save') : $t('directories.create') }}
        </a-button>
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
            default: 'help_desk.ContactPersonPostModel'
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
        index: {
            type: Number,
            default: 0
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
            slaSelected: null,
            visible: false,
            loading: false,
            form: {
                name: '',
                contractor: ''
            },
            rules: {
                name: [
                    {
                        required: true,
                        message: this.$t('directories.required_field'),
                        trigger: "change",
                    },
                ],
            },
            edit: false
        }
    },
    mounted() {
        if(this.eventsEnabled) {
            eventBus.$on('open_modal_position_edit', ({ record }) => {
                this.form = {
                    ...this.form,
                    ...record
                }
                if(record.sla)
                    this.slaSelected = record.sla.id
                this.edit = true
                this.visible = true
            })
            eventBus.$on('open_modal_position_add', () => {
                this.visible = true
            })
            eventBus.$on(`open_modal_position_add_in_${this.index}`, () => {
                this.visible = true
            })
        }
    },
    beforeDestroy() {
        if(this.eventsEnabled) {
            eventBus.$off('open_modal_position_edit')
            eventBus.$off('open_modal_position_add')
            eventBus.$off(`open_modal_position_add_in_${this.index}`)
        }
    },
    methods: {
        openModal() {
            this.visible = true
        },
        SLAChange(value) {
            this.slaSelected = value.id
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
                            if(this.edit) {
                                const { data } = await this.$http.put(`/help_desk/contact_person_post/${this.form.id}/`, payload)
                                if(data) {
                                    if(this.slaSelected)
                                        await this.saveSLA(data)
                                    this.$message.success(this.$t('directories.position_updated'))
                                    eventBus.$emit(`update_filter_${this.model}`)
                                    this.$emit('change', data)
                                    this.visible = false
                                }
                            } else {
                                const { data } = await this.$http.post('/help_desk/contact_person_post/', payload)
                                if(data) {
                                    if(this.slaSelected)
                                        await this.saveSLA(data)
                                    this.$message.success(this.$t('directories.position_created'))
                                    eventBus.$emit(`update_filter_${this.model}`)
                                    this.$emit('change', data)
                                    this.visible = false
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
        afterVisibleChange(vis) {
            if(vis) {
                if(this.contractor)
                    this.form.contractor = this.contractor
                this.$nextTick(() => {
                    if(this.$refs.nameInput)
                        this.$refs.nameInput.focus()
                })
            } else {
                this.slaSelected = null
                this.edit = false
                this.form = {
                    name: '',
                    contractor: ''
                }
            }
        },

    }
}

</script>
