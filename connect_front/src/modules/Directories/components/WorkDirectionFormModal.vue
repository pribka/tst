<template>
    <a-modal
        :visible="visible"
        @afterVisibleChange="afterVisibleChange"
        :width="400"
        @cancel="visible = false"
        :footer="null"
        destroyOnClose>
        <template #title>
            {{ $t('directories.direction') }}
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
                    :placeholder="$t('directories.direction_name')" />
            </a-form-model-item>
            <a-form-model-item
                v-if="contractorSelect"
                ref="contractor"
                :label="$t('directories.organization')"
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
                    :disabled="edit"
                    oneSelect
                    size="large"
                    firstSelected
                    :placeholder="$t('directories.organization')"
                    :listObject="false"
                    labelKey="name"
                    :params="{
                        permission_type: 'admin'
                    }"
                    :default-active-first-option="false"
                    :filter-option="false"
                    :not-found-content="null" />
            </a-form-model-item>
            <a-form-model-item
                v-if="edit"
                class="mb-2">
                <div class="archive_switch">
                    <a-switch
                        :checked="form.is_archive"
                        @change="onArchiveChange" />
                    <span
                        class="archive_switch__label"
                        @click="toggleArchive">
                        {{ $t('directories.to_archive') }}
                    </span>
                </div>
            </a-form-model-item>
        </a-form-model>
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
        afterCreate: {
            type: Function,
            default: () => {}
        },
        model: {
            type: String,
            default: 'catalogs.WorkDirectionModel'
        },
        contractorSelect: {
            type: Boolean,
            default: false
        },
        eventsEnabled: {
            type: Boolean,
            default: true
        }
    },
    data() {
        return {
            visible: false,
            loading: false,
            form: {
                id: '',
                name: '',
                contractor: '',
                is_archive: false
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
        if (this.eventsEnabled) {
            eventBus.$on('open_modal_work_direction_edit', ({ record }) => {
                this.startEdit(record)
            })
            eventBus.$on('open_modal_work_direction_add', () => {
                this.visible = true
            })
        }
    },
    beforeDestroy() {
        if (this.eventsEnabled) {
            eventBus.$off('open_modal_work_direction_edit')
            eventBus.$off('open_modal_work_direction_add')
        }
    },
    methods: {
        submit() {
            this.$refs.formRef
                .validate(async valid => {
                    if (valid) {
                        try {
                            this.loading = true
                            if (this.edit) {
                                const payload = {
                                    name: this.form.name,
                                    is_archive: this.form.is_archive
                                }
                                const { data } = await this.$http.patch(`/catalogs/work_directions/${this.form.id}/`, payload)
                                if (data) {
                                    this.$message.success(this.$t('directories.direction_updated'))
                                    eventBus.$emit(`update_filter_${this.model}`)
                                    this.afterCreate(data, { edit: true })
                                    this.$emit('change', data)
                                    this.visible = false
                                }
                            } else {
                                const payload = {
                                    name: this.form.name,
                                    contractor: this.form.contractor
                                }
                                const { data } = await this.$http.post('/catalogs/work_directions/', payload)
                                if (data) {
                                    this.$message.success(this.$t('directories.direction_created'))
                                    eventBus.$emit(`update_filter_${this.model}`)
                                    this.afterCreate(data, { edit: false })
                                    this.$emit('change', data)
                                    this.visible = false
                                }
                            }
                        } catch (error) {
                            errorHandler({ error })
                        } finally {
                            this.loading = false
                        }
                    }
                })
        },
        toggleArchive() {
            this.form.is_archive = !this.form.is_archive
        },
        onArchiveChange(value) {
            this.form.is_archive = value
        },
        open() {
            this.visible = true
        },
        startEdit(record) {
            this.form = {
                ...this.form,
                ...record,
                contractor: record?.contractor?.id || record?.contractor || '',
                is_archive: Boolean(record?.is_archive)
            }
            this.edit = true
            this.visible = true
        },
        afterVisibleChange(vis) {
            if (vis) {
                if (this.contractor && !this.edit) {
                    this.form.contractor = this.contractor
                }
                this.$nextTick(() => {
                    if (this.$refs.nameInput)
                        this.$refs.nameInput.focus()
                })
            } else {
                this.edit = false
                this.form = {
                    id: '',
                    name: '',
                    contractor: '',
                    is_archive: false
                }
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.archive_switch{
    display: flex;
    align-items: center;
    gap: 10px;
    &__label{
        font-size: 16px;
        line-height: 1.4;
        color: var(--text);
        cursor: pointer;
    }
}
</style>
