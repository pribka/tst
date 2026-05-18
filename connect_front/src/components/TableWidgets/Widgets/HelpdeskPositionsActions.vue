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
        pageName: {
            type: String,
            default: ''
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
            listModel: "help_desk.ContactPersonPostModel",
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
            eventBus.$emit('open_modal_position_edit', { record: this.record })
        },
        deleteItem() {
            this.$confirm({
                title: 'Вы действительно хотите удалить должность?',
                cancelText: 'Отмена',
                okText: 'Удалить',
                okType: 'danger',
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post('/table_actions/update_is_active/', [{ id: this.record.id, is_active: false }])
                            .then(() => {
                                this.$message.success('Должность удалена')
                                eventBus.$emit(`update_filter_${this.listModel}`)
                                this.visible = false
                                resolve()
                            })
                            .catch((e) => {
                                console.log(e)
                                reject()
                            })
                    })
                }
            })
        },
        async getActions() {
            if(!this.actions) {
                try {
                    this.loading = true
                    this.listLoading = true
                    const { data } = await this.$http.get(`help_desk/contact_person_post/${this.record.id}{/action_info/`)
                    if(data?.actions) {
                        this.actions = data.actions
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.loading = false
                    this.listLoading = false
                }
            }
        },
        visibleChange(visible) {
            if(visible) {
                this.getActions()
            }
        }
    }
}
</script>