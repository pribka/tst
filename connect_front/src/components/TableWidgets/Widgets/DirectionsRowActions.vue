<template>
    <a-dropdown
        :trigger="['click']"
        :getPopupContainer="getPopupContainer"
        @visibleChange="visibleChange">
        <a-button
            type="ui"
            ghost
            flaticon
            shape="circle"
            :loading="loading"
            size="small"
            icon="fi-rr-menu-dots-vertical"
            :destroyPopupOnHide="false" />
        <a-menu slot="overlay">
            <template v-if="hasNoActions">
                <a-menu-item
                    class="text-muted flex items-center"
                    key="no_action">
                    {{ $t('no_actions') }}
                </a-menu-item>
            </template>
            <template v-else>
                <a-menu-item
                    v-if="actions?.edit?.availability"
                    class="flex items-center"
                    key="edit"
                    @click="editItem">
                    <i class="fi fi-rr-edit mr-2" />
                    {{ $t('edit') }}
                </a-menu-item>
                <a-menu-item
                    v-if="actions?.edit?.availability"
                    class="flex items-center"
                    key="archive"
                    @click="archiveItem">
                    <i class="fi fi-rr-box mr-2" />
                    {{ $t('directories.to_archive') }}
                </a-menu-item>
                <a-menu-item
                    v-if="actions?.delete?.availability"
                    class="text-red-500 flex items-center"
                    key="delete"
                    @click="deleteItem">
                    <i class="fi fi-rr-trash mr-2" />
                    {{ $t('Delete') }}
                </a-menu-item>
            </template>
            <a-menu-item v-if="listLoading">
                <div class="flex justify-center">
                    <a-spin size="small" />
                </div>
            </a-menu-item>
        </a-menu>
    </a-dropdown>
</template>

<script>
import eventBus from '@/utils/eventBus'

export default {
    props: {
        record: {
            type: Object,
            required: true
        },
        colParams: {
            type: Object,
            default: () => null
        }
    },
    data() {
        return {
            loading: false,
            listLoading: false,
            actions: null,
            listModel: 'catalogs.WorkDirectionModel',
            lastEditAt: 0
        }
    },
    computed: {
        hasNoActions() {
            if (this.actions) {
                return Object.keys(this.actions).length === 0
            }
            return false
        }
    },
    methods: {
        getPopupContainer() {
            return this.colParams?.getPopupContainer ? this.colParams.getPopupContainer() : document.body
        },
        editItem() {
            const now = Date.now()
            if (now - this.lastEditAt < 400) return
            this.lastEditAt = now
            eventBus.$emit('open_modal_work_direction_edit', { record: this.record })
        },
        archiveItem() {
            this.$confirm({
                title: 'Вы действительно хотите отправить направление в архив?',
                cancelText: 'Отмена',
                okText: 'В архив',
                okType: 'danger',
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.patch(`/catalogs/work_directions/${this.record.id}/`, {
                            is_archive: true
                        })
                            .then(() => {
                                this.$message.success('Направление отправлено в архив')
                                eventBus.$emit(`update_filter_${this.listModel}`)
                                resolve()
                            })
                            .catch(error => {
                                console.log(error)
                                reject(error)
                            })
                    })
                }
            })
        },
        deleteItem() {
            this.$confirm({
                title: 'Вы действительно хотите удалить направление?',
                cancelText: 'Отмена',
                okText: 'Удалить',
                okType: 'danger',
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.patch(`/catalogs/work_directions/${this.record.id}/`, {
                            is_archive: true
                        })
                            .then(() => {
                                this.$message.success('Направление удалено')
                                eventBus.$emit(`update_filter_${this.listModel}`)
                                resolve()
                            })
                            .catch(error => {
                                console.log(error)
                                reject(error)
                            })
                    })
                }
            })
        },
        async getActions() {
            if (!this.actions) {
                try {
                    this.loading = true
                    this.listLoading = true
                    const { data } = await this.$http.get(`/catalogs/work_directions/${this.record.id}/action_info/`)
                    if (data?.actions) {
                        this.actions = data.actions
                    }
                } catch (error) {
                    console.log(error)
                } finally {
                    this.loading = false
                    this.listLoading = false
                }
            }
        },
        visibleChange(visible) {
            if (visible) {
                this.getActions()
            }
        }
    }
}
</script>
