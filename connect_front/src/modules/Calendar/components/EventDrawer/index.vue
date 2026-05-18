<template>
    <DrawerTemplate
        placement="right"
        class="event_drawer"
        :width="drawerWidth"
        destroyOnClose
        v-model="visible"
        useCopyLink
        useOpenLink
        :link="{
            event: event ? event.id : null
        }"
        @afterVisibleChange="afterVisibleChange"
        @close="visible = false">
        <template #title>
            <div ref="drawerHeader" class="d_e_h flex items-center justify-between truncate w-full">
                <div
                    v-if="event"
                    class="text-base font-semibold flex items-center truncate label">
                    <div><div :style="`background: ${event.color};`" class="event_badge"></div></div> <div class="truncate">{{ event.name }}</div>
                </div>
                <a-skeleton
                    v-else
                    active
                    :paragraph="{ rows: 1 }" />
                <div class="flex items-center pl-4">
                    <template v-if="event">
                        <template v-if="actions">
                            <template v-if="actions.edit">
                                <a-button 
                                    v-if="!event.is_finished"
                                    type="green"  
                                    :icon="isMobile && 'fi-rr-check-double'"
                                    flaticon
                                    :loading="closeLoading"
                                    class="mr-3"
                                    @click="closeToggleEvent(true)">
                                    <template v-if="!isMobile">{{ $t('calendar.finish') }}</template>
                                </a-button>
                                <a-button 
                                    v-if="event.is_finished"
                                    type="flat_primary" 
                                    :icon="isMobile && 'fi-rr-rotate-right'"
                                    flaticon
                                    :loading="closeLoading"
                                    class="mr-3"
                                    @click="closeToggleEvent(false)">
                                    <template v-if="!isMobile">{{ $t('calendar.mark_active') }}</template>
                                </a-button>
                            </template>
                            <template v-else>
                                <a-button 
                                    v-if="isMobile"
                                    icon="fi-rr-remove-user"
                                    flaticon
                                    class="mr-2 text_red"
                                    shape="circle"
                                    type="ui" 
                                    ghost
                                    :loading="leaveLoader"
                                    @click="leaveEvent()" />
                                <a-button 
                                    v-else
                                    icon="fi-rr-remove-user"
                                    flaticon
                                    class="mr-3"
                                    type="danger" 
                                    ghost
                                    :loading="leaveLoader"
                                    @click="leaveEvent()">
                                    {{ $t('calendar.leave_event') }}
                                </a-button>
                            </template>
                        </template>
                        <template v-if="isMobile">
                            <a-button 
                                type="ui"
                                ghost
                                shape="circle"
                                flaticon
                                :diabled="actions ? false : true"
                                :loading="actionLoading"
                                icon="fi-rr-menu-dots-vertical" 
                                @click="openDrawer" />
                            <ActivityDrawer v-if="actions" v-model="menuVisible">
                                <ActivityItem @click="shareHandler()">
                                    <i class="fi fi-rr-share mr-2"></i>
                                    {{ $t('calendar.share') }}
                                </ActivityItem>
                                <ActivityItem @click="copyHandler()">
                                    <i class="fi fi-rr-copy-alt mr-2"></i>
                                    {{ $t('calendar.copy_event') }}
                                </ActivityItem>
                                <ActivityItem v-if="actions.edit" @click="editHandler()">
                                    <i class="fi fi-rr-edit mr-2"></i>
                                    {{ $t('calendar.edit') }}
                                </ActivityItem>
                                <ActivityItem v-if="actions.delete" @click="deleteHanlder()">
                                    <i class="fi fi-rr-trash mr-2"></i>
                                    {{ $t('calendar.delete') }}
                                </ActivityItem>
                            </ActivityDrawer>
                        </template>
                        <a-dropdown 
                            v-else
                            :getPopupContainer="getPopupContainer" 
                            :trigger="['click']">
                            <a-button 
                                type="ui" 
                                ghost 
                                shape="circle"
                                :diabled="actions ? false : true"
                                :loading="actionLoading"
                                icon="fi-rr-menu-dots-vertical" 
                                flaticon />
                            <a-menu slot="overlay">
                                <template v-if="actions">
                                    <a-menu-item key="share" class="flex items-center" @click="shareHandler()">
                                        <i class="fi fi-rr-share mr-2"></i>
                                        {{ $t('calendar.share') }}
                                    </a-menu-item>
                                    <a-menu-item key="copy" class="flex items-center" @click="copyHandler()">
                                        <i class="fi fi-rr-copy-alt mr-2"></i>
                                        {{ $t('calendar.copy_event') }}
                                    </a-menu-item>
                                    <a-menu-item v-if="actions.edit" key="edit" class="flex items-center" @click="editHandler()">
                                        <i class="fi fi-rr-edit mr-2"></i>
                                        {{ $t('calendar.edit') }}
                                    </a-menu-item>
                                    <template v-if="actions.delete">
                                        <a-menu-divider />
                                        <a-menu-item key="delete" class="text-red-500 flex items-center" @click="deleteHanlder()">
                                            <i class="fi fi-rr-trash mr-2"></i> {{ $t('calendar.delete') }}
                                        </a-menu-item>
                                    </template>
                                </template>
                            </a-menu>
                        </a-dropdown>
                    </template>
                </div>
            </div>
        </template>
        <template v-if="event" #tabs>
            <a-tabs 
                v-model="tabKey" 
                class="header_tab">
                <a-tab-pane key="info" :tab="$t('calendar.tab_event')" />
                <a-tab-pane key="accounting" :tab="$t('calendar.accounting')" />
                <a-tab-pane key="files" :tab="$t('calendar.tab_files')" />
            </a-tabs>
        </template>
        <div class="event_body_wrap">
            <a-tabs 
                v-if="event"
                :activeKey="tabKey" 
                class="body_tab">
                <a-tab-pane key="info" tab="">
                    <Event
                        :event="event"
                        :actions="actions"
                        :createMeeting="createMeeting"
                        :toggleMeetingStatus="toggleMeetingStatus"
                        :refreshEventDetails="refreshEventDetails" />
                </a-tab-pane>
                <a-tab-pane key="accounting" tab="">
                    <Accounting :event="event" :actions="actions" />
                </a-tab-pane>
                <a-tab-pane key="files" tab="">
                    <Files :event="event" />
                </a-tab-pane>
            </a-tabs>
            <a-skeleton v-else active />
        </div>
        <template v-if="!isMobile && tabKey === 'info'" #aside>
            <Aside
                v-if="event"
                :event="event"
                :actions="actions"
                :createMeeting="createMeeting"
                :toggleMeetingStatus="toggleMeetingStatus"
                :refreshEventDetails="refreshEventDetails" />
            <a-skeleton v-else active />
        </template>
    </DrawerTemplate>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { ActivityItem, ActivityDrawer } from '@/components/ActivitySelect'
import { errorHandler } from '@/utils/index.js'
export default {
    components: {
        Files: () => import('./TabWidget/Files.vue'),
        Event: () => import('./TabWidget/Event.vue'),
        Accounting: () => import('./TabWidget/Accounting.vue'),
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue'),
        Aside: () => import('./Aside.vue'),
        ActivityItem,
        ActivityDrawer
    },
    computed: {
        windowWidth() {
            return this.$store.state.windowWidth
        },
        drawerWidth() {
            if(this.windowWidth > 1200)
                return 1200
            else {
                return '100%'
            }
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    data() {
        return {
            visible: false,
            loading: false,
            actionLoading: false,
            closeLoading: false,
            event: null,
            menuVisible: false,
            actions: null,
            tabKey: 'info',
            leaveLoader: false,
            zIndex: 1000
        }
    },
    watch: {
        '$route.query'(val) {
            if(val.event) {
                this.openEventDrawer()
            }
        },
    },
    created: function() {
        if(this.$route.query.event)
            this.openEventDrawer()
    },
    methods: {
        async refreshEventDetails() {
            if (!this.event?.id) return null

            const { data } = await this.$http.get(`/calendars/events/${this.event.id}/`)
            if (data) {
                this.event = data
                this.getActions()
                eventBus.$emit('edit_event', data)
            }
            return data || null
        },
        toggleMeetingStatus(value) {
            this.$set(this.event.meeting, 'status', value)
        },
        async createMeeting() {
            try {
                const { data } = await this.$http.post(`/calendars/events/${this.event.id}/create_meeting/`)
                if(data?.meeting) {
                    this.event.meeting = data.meeting
                    eventBus.$emit('edit_event', this.event)
                }
            } catch(error) {
                errorHandler({error})
            }
        },
        openDrawer() {
            this.menuVisible = true
        },
        leaveEvent() {
            this.$confirm({
                title: this.$t('calendar.confirm_leave_title'),
                content: '',
                okText: this.$t('calendar.confirm_ok'),
                okType: 'danger',
                zIndex: 2000,
                closable: true,
                cancelText: this.$t('calendar.confirm_cancel'),
                onOk: () => {
                    this.leaveLoader = true
                    return new Promise((resolve, reject) => {
                        this.$http.post(`/calendars/events/${this.event.id}/escape/`)
                            .then(() => {
                                this.visible = false
                                this.$message.success(this.$t('calendar.left_event_success'))
                                eventBus.$emit('delete_event', this.event.id)
                                this.leaveLoader = false
                                resolve()
                            })
                            .catch(error => {
                                errorHandler({error})
                                this.leaveLoader = false
                                reject(e)
                            })
                    })
                }
            })
        },
        async closeToggleEvent(is_finished) {
            try {
                this.closeLoading = true
                const { data } = await this.$http.patch(`/calendars/events/${this.event.id}/`, {
                    is_finished
                })
                if(data) {
                    this.event.is_finished = is_finished
                    eventBus.$emit('edit_event', this.event)
                    if (this.$store.hasModule('workplan')) {
                        this.$store.dispatch('workplan/updateItem', {
                            item: this.event,
                            list: 'eventList'
                        })
                    }
                    if(is_finished) {
                        this.$message.info(this.$t('calendar.event_finished_msg'))
                    } else {
                        this.$message.info(this.$t('calendar.event_active_msg'))
                    }
                }
            } catch(e) {
                console.log(e)
                this.$message.error(this.$t('calendar.error'))
            } finally {
                this.closeLoading = false
            }
        },
        shareHandler() {
            this.$store.commit('share/SET_SHARE_PARAMS', {
                model: 'event',
                shareId: this.event.id,
                object: this.event,
                shareUrl: `${window.location.origin}/?event=${this.event.id}`,
                shareTitle: this.event.name
            })
        },
        deleteHanlder() {
            this.$confirm({
                title: this.$t('calendar.confirm_delete_title'),
                content: '',
                okText: this.$t('calendar.confirm_ok'),
                okType: 'danger',
                zIndex: 2000,
                closable: true,
                cancelText: this.$t('calendar.confirm_cancel'),
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post('/table_actions/update_is_active/', {
                            id: this.event.id,
                            is_active: false
                        })
                            .then(() => {
                                this.$message.success(this.$t('calendar.event_deleted'))
                                eventBus.$emit('delete_event', this.event.id)
                                if (this.$store.hasModule('workplan')) {
                                    this.$store.dispatch('workplan/deleteItem', {
                                        item: this.event,
                                        list: 'eventList'
                                    })
                                }
                                this.visible = false
                                resolve()
                            })
                            .catch(error => {
                                errorHandler({error})
                                reject(e)
                            })
                    })
                }
            })
        },
        editHandler() {
            this.visible = false
            eventBus.$emit('open_event_form', null, null, this.event)
        },
        copyHandler() {
            const { id, ...eventCopy } = this.event
            this.visible = false
            eventBus.$emit('open_event_form', null, null, eventCopy)
        },
        async getActions() {
            try {
                this.actionLoading = true
                const { data } = await this.$http.get(`/calendars/events/${this.event.id}/action_info/`)
                if(data?.actions) {
                    this.actions = data.actions
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.actionLoading = false
            }
        },
        getPopupContainer() {
            return this.$refs.drawerHeader
        },
        afterVisibleChange(vis) {
            if(vis) {
                if(this.$route.query?.sprint) 
                    this.zIndex = 999999
                this.getFullEvent()
            } else {
                this.event = null
                this.actions = null
                this.tabKey = 'info'
                this.zIndex = 1000
                let query = Object.assign({}, this.$route.query)
                if(query.event) {
                    delete query.event
                    this.$router.push({query})
                }
            }
        },
        openEventDrawer() {
            const query = this.$route.query
            if(query?.task || query?.viewProject || query?.viewGroup) {
                this.zIndex = 1500
            }
            this.visible = true
        },
        async getFullEvent() {
            try {
                this.loading = true
                let { event } = Object.assign({}, this.$route.query)
                const { data } = await this.$http.get(`/calendars/events/${event}/`)
                if(data) {
                    this.event = data
                    this.getActions()
                }
            } catch(e) {
                console.log(e)
                this.$message.error(this.$t('calendar.event_not_found'))
                this.visible = false
            } finally {
                this.loading = false
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.body_tab{
    &::v-deep{
        .ant-tabs-bar{
            display: none;
        }
    }
}
.d_e_h{
    .event_badge{
        height: 15px;
        width: 15px;
        border-radius: 50%;
        margin-right: 8px;
    }
}
</style>
