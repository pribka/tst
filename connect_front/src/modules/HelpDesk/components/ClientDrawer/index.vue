<template>
    <DrawerTemplate
        :width="drawerWidth"
        class="client_drawer"
        v-model="visible"
        @afterVisibleChange="afterVisibleChange"
        @close="visible = false">
        <template v-if="client" #title>
            <div class="w-full flex items-center justify-between">
                <div class="drawer_title">{{ client.name }}</div>
                <div class="flex items-center pl-3">
                    <a-button
                        v-if="actions && actions.delete"
                        type="ui"
                        shape="circle"
                        flaticon
                        ghost
                        v-tippy
                        :content="$t('helpdesk.delete')"
                        icon="fi-rr-trash"
                        class="mr-3"
                        @click="deleteClient()" />
                    <!--<a-button
                        v-if="actions && actions.edit"
                        type="ui"
                        ghost
                        v-tippy
                        content="Редактировать"
                        class="mr-2"
                        flaticon
                        shape="circle"
                        icon="fi-rr-edit"
                        @click="editClient()" />-->
                </div>
            </div>
        </template>
        <template v-if="client" #tabs>
            <div class="drawer_tabs">
                <a-tabs
                    v-model="tab"
                    :showContent="false"
                    @change="changeTab">
                    <a-tab-pane
                        v-for="pane in panes"
                        :key="pane.key">
                        <template #tab>
                            {{ pane.label }}
                        </template>
                    </a-tab-pane>
                </a-tabs>
            </div>
        </template>
        <template v-if="client">
            <a-tabs
                :activeKey="tab"
                :showBar="false"
                :destroyInactiveTabPane="true"
                class="body_tab h-full">

                <a-tab-pane
                    v-for="pane in panes"
                    :key="pane.key"
                    class="flex flex-col">
                    <component
                        :key="tab"
                        :is="tabComponent"
                        :client="client"
                        :actions="actions"
                        :clientUpdate="clientUpdate"
                        :model="model"
                        :pageName="pageName"
                        :edit="edit" />
                </a-tab-pane>
            </a-tabs>
        </template>
        <a-skeleton
            v-else
            active
            :paragraph="{ rows: 5 }" />
    </DrawerTemplate>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { clearTabQuery } from '@/utils/routerUtils.js'
import { mobileModuleCheck } from '@/utils/index.js'
import { clientFormKey } from '../../utils/utils.js'
import { errorHandler } from '@/utils/index.js'
export default {
    components: {
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue')
    },
    computed: {
        storeFormInfo() {
            return this.$store.state.formInfo?.formInfo?.[clientFormKey] || {}
        },
        tabComponent() {
            const tabs = {
                'info': () => import('./tabs/Info.vue'),
                'contact_persons': () => import('./tabs/ContactPersons.vue'),
                'specialists': () => import('./tabs/Specialists.vue'),
                'files': () => import('./tabs/Files.vue'),
                'history': () => import('./tabs/History.vue'),
                'notes': () => import('./tabs/Notes.vue'),
                'knowledge-base': () => import('./tabs/KnowledgeBase.vue'),
            }
            return tabs[this.tab] || tabs.info
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        drawerWidth() {
            if(this.windowWidth > 1575)
                return 1575
            else {
                return '100%'
            }
        },
        edit() {
            return this.actions?.edit?.availability || false
        },
        panes() {
            const tabs = [
                {
                    key: 'info',
                    label: this.$t('helpdesk.basic_information'),
                },
                {
                    key: 'contact_persons',
                    label: this.$t('helpdesk.contact_persons')
                },
                {
                    key: 'specialists',
                    label: this.$t('helpdesk.support_specialists')
                },
                {
                    key: 'files',
                    label: this.$t('helpdesk.files')
                },
                {
                    key: 'history',
                    label: this.$t('helpdesk.appeal_history')
                }
            ]
            if(this.actions?.create_notes?.availability || this.actions?.edit_notes?.availability) {
                tabs.push({
                    key: 'notes',
                    label: this.$t('helpdesk.notes')
                })
            }
            return tabs
        }
    },
    watch: {
        '$route.query'(val) {
            if(val.client) {
                // if(mobileModuleCheck()) {
                this.visible = true
                // } else {
                //     this.closeDrawer()
                // }
            }
        }
    },
    mounted() {
        if(this.$route.query?.client) {
            // if(mobileModuleCheck()) {
            this.visible = true
            // } else {
            //     this.closeDrawer()
            // }
        }
    },
    data() {
        return {
            model: "help_desk.CustomerCardModel",
            pageName: "list_help_desk.CustomerCardModel",
            visible: false,
            client: null,
            tab: 'info',
            loading: false,
            actions: null
        }
    },
    methods: {
        async getFormInfo() {
            try {
                if (!Object.keys(this.storeFormInfo)?.length)
                    await this.$store.dispatch('formInfo/getFormInfo', { form: clientFormKey })
            } catch (error) {
                console.log(error)
            }
        },
        clientUpdate(data) {
            this.client.name = data.name
        },
        async getActions(query) {
            try {
                const { data } = await this.$http.get(`/help_desk/customer_cards/${query.client}/action_info/`)
                if(data?.actions) {
                    this.actions = data.actions
                }
            } catch(e) {
                console.log(e)
            }
        },
        deleteClient() {
            this.$confirm({
                title: this.$t('helpdesk.confirm_delete_contractor'),
                closable: true,
                maskClosable: true,
                cancelText: this.$t('helpdesk.cancel'),
                okText: this.$t('helpdesk.delete'),
                okType: 'danger',
                zIndex: 999999,
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post('/table_actions/update_is_active/', [{ id: this.client.id, is_active: false }])
                            .then(() => {
                                this.$message.success(this.$t('helpdesk.contractor_deleted'))
                                eventBus.$emit(`update_filter_${this.model}_${this.pageName}`)
                                this.visible = false
                                resolve()
                            })
                            .catch((error) => {
                                errorHandler({error})
                                reject()
                            })
                    })
                }
            })
        },
        editClient() {
            eventBus.$emit('helpdesc_edit_client', this.client)
        },
        async getClient() {
            try {
                this.loading = true
                const query = Object.assign({}, this.$route.query)
                const { data } = await this.$http.get(`/help_desk/customer_cards/${query.client}/`)
                if(data) {
                    await this.getActions(query)
                    await this.getFormInfo()
                    this.client = data
                }
            } catch(error) {
                if(error.status === 404) {
                    this.$message.error(this.$t('helpdesk.contractor_not_found'))
                } else {
                    if(error && error.detail) {
                        if(error.detail === 'Не найдено.' || error.detail === 'Страница не найдена.' || error.detail === 'У вас недостаточно прав для выполнения данного действия.') {
                            this.$message.warning(this.$t('helpdesk.contractor_not_found'))
                        } else {
                            this.$message.error(this.$t('helpdesk.error'))
                        }
                    } else {
                        this.$message.error(this.$t('helpdesk.error'))
                    }
                }
                this.visible = false
            } finally {
                this.loading = false
            }
        },
        changeTab(val) {
            const query = {...this.$route.query}
            query.ctab = val
            this.$router.replace({query})
        },
        afterVisibleChange(vis) {
            if(vis) {
                if(this.$route.query?.ctab)
                    this.tab = this.$route.query.ctab
                this.getClient()
                eventBus.$on('client_detail_reload', () => {
                    this.getClient()
                })
                eventBus.$on('close_client_drawer', () => {
                    this.visible = false
                })
            } else {
                this.closeDrawer()
                eventBus.$off('client_detail_reload')
                eventBus.$off('close_client_drawer')
            }
        },
        closeDrawer() {
            this.tab = 'info'
            this.actions = null
            this.client = null

            const next = clearTabQuery({ ...this.$route.query, client: undefined, ctab: undefined })
            const same = JSON.stringify(this.$route.query) === JSON.stringify(next)
            if (same) return

            this.$router.replace({
                name: this.$route.name,
                params: this.$route.params,
                query: next
            })
        }
    }
}
</script>