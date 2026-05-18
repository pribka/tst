<template>
    <a-row :gutter="{xs: 15, md: 20, lg: 30, xxl: 30}" class="h-full">
        <a-col
            v-if="!isMobile"
            :xs="24"
            :md="showAside ? 14 : 24"
            :xl="showAside ? 16 : 24"
            :xxl="showAside ? 16 : 24"
            class="h-full">
            <ChatList
                ref="chatList"
                :ticket="ticket"
                :changeShowAside="changeShowAside"
                edit
                :actions="actions"
                :showAside="showAside" />
        </a-col>

        <a-col
            v-if="showAside"
            :xs="24"
            :md="showAside ? 10 : 24"
            :xl="8"
            :xxl="8"
            class="h-full">

            <!-- STATUS ACTIONS (MOBILE) -->
            <a-spin
                v-if="isMobile"
                :spinning="statusLoader"
                size="small"
                class="w-full pb-3">
                <!-- только статусный блок: делаем колонкой, чтобы ничего не перекрывало -->
                <div class="status_actions">
                    <a-button
                        v-if="isStatusAvailable('completed')"
                        type="flat_primary"
                        size="large"
                        flaticon
                        icon="fi-rr-check"
                        block
                        @click="ticketEnd()">
                        {{ $t('helpdesk.accept_result') }}
                    </a-button>

                    <a-button
                        v-if="isStatusAvailable('on_rework')"
                        type="flat_danger"
                        size="large"
                        flaticon
                        icon="fi-rr-rotate-right"
                        block
                        @click="changeStatus('on_rework')">
                        {{ availableStatusByCode.on_rework?.name || $t('helpdesk.needs_rework') }}
                    </a-button>

                    <a-button
                        v-if="isStatusAvailable('rejected')"
                        class="border-none"
                        type="danger"
                        ghost
                        @click="changeStatus('rejected')">
                        {{ $t('helpdesk.cancel_action') }}
                    </a-button>
                </div>
            </a-spin>

            <transition v-if="isMobile" name="slide-fade">
                <div v-if="ticket.status.code === 'completed' && !ticket.rating" class="pb-2">
                    <div class="rew_wrapper_info pt-0">
                        <h2>{{ $t('helpdesk.rate_service_quality') }}</h2>
                        <SmileSelect v-model="rewForm.rating" class="mb-5" />
                        <a-textarea
                            v-model="rewForm.description"
                            size="large"
                            :placeholder="$t('helpdesk.rating_comment')"
                            :auto-size="{ minRows: 3, maxRows: 12 }" />
                        <a-button
                            type="primary"
                            size="large"
                            block
                            class="mt-2"
                            :loading="completedLoading"
                            @click="completedTicket(false)">
                            {{ $t('helpdesk.send') }}
                        </a-button>
                    </div>
                </div>
            </transition>

            <DrawerAside v-if="ticket.org_admin || ticket.created_at">
                <ListView>
                    <ListViewItem v-if="ticket.org_admin" :title="$t('helpdesk.organization')">
                        {{ ticket.org_admin.name }}
                    </ListViewItem>
                    <ListViewItem v-if="ticket.created_at"  :title="$t('helpdesk.creation_date')">
                        {{ $moment(ticket.created_at).format('DD.MM.YYYY') }}
                    </ListViewItem>
                </ListView>
            </DrawerAside>

            <DrawerAside>
                <ListView :inline="!isMobile" labelDark>
                    <ListViewItem>
                        <span class="font-semibold">{{ ticket.name }}</span>
                    </ListViewItem>
                    <ListViewItem v-if="checkField({ key: 'description' })">
                        <TextViewer
                            class="body_text"
                            :body="ticket.description" />
                    </ListViewItem>
                    <ListViewItem v-if="ticket.status" :title="$t('helpdesk.status')">
                        <a-tag :color="ticket.status.color" block size="large">
                            {{ ticket.status.name }}
                        </a-tag>
                    </ListViewItem>
                    <ListViewItem v-if="checkField({ key: 'category' })" :title="$t('helpdesk.category')">
                        {{ ticket.category.name }}
                    </ListViewItem>
                    <ListViewItem v-if="checkField({ key: 'dead_line' })" :title="$t('helpdesk.deadline')">
                        {{ $moment(ticket.dead_line).format('DD.MM.YYYY') }}
                    </ListViewItem>
                    <ListViewItem v-if="checkField({ key: 'contact_person_user' })" :title="$t('helpdesk.user')">
                        <Profiler
                            :avatarSize="22"
                            nameClass="text-sm"
                            :user="ticket.contact_person_user" />
                    </ListViewItem>
                    <ListViewItem v-if="checkField({ key: 'specialist' })" :title="$t('helpdesk.responsible')">
                        <Profiler
                            :avatarSize="22"
                            nameClass="text-sm"
                            :user="ticket.specialist" />
                    </ListViewItem>
                    <ListViewItem v-if="ticket.channel" :title="$t('helpdesk.communication_channel')">
                        <div class="flex items-center justify-between pr-1">
                            <span class="pr-2">{{ ticket.channel.name }}</span>
                            <div v-if="ticket.channel.icon">
                                <img
                                    v-if="isSVG(ticket.channel.icon)"
                                    :src="require(`@/assets/svg/${ticket.channel.icon}`)"
                                    class="lazyload mr-2 channel_icon" />
                                <i
                                    v-else
                                    class="mr-2 fi"
                                    :class="ticket.channel.icon" />
                            </div>
                        </div>
                    </ListViewItem>
                    <ListViewItem v-if="showRelatedChat" :title="$t('helpdesk.created_from_chat')">
                        <a class="related-chat-link" @click.prevent="openRelatedChat">
                            {{ ticket.related_chat.name }}
                        </a>
                    </ListViewItem>
                </ListView>
            </DrawerAside>

            <transition name="slide-fade">
                <div v-if="ticket.work_log_duration > 0" class="completed_banner mb-2">
                    {{ formattedTimer }}
                </div>
            </transition>

            <!-- STATUS ACTIONS (DESKTOP) -->
            <a-spin
                v-if="!isMobile"
                :spinning="statusLoader"
                size="small"
                class="w-full pb-3">
                <!-- только статусный блок: делаем колонкой, чтобы ничего не перекрывало -->
                <div class="status_actions">
                    <a-button
                        v-if="isStatusAvailable('completed')"
                        type="flat_primary"
                        size="large"
                        flaticon
                        icon="fi-rr-check"
                        block
                        @click="ticketEnd()">
                        {{ $t('helpdesk.accept_result') }}
                    </a-button>

                    <a-button
                        v-if="isStatusAvailable('on_rework')"
                        type="flat_danger"
                        size="large"
                        flaticon
                        icon="fi-rr-rotate-right"
                        block
                        @click="changeStatus('on_rework')">
                        {{ availableStatusByCode.on_rework?.name || $t('helpdesk.needs_rework') }}
                    </a-button>

                    <a-button
                        v-if="isStatusAvailable('rejected')"
                        class="border-none"
                        ghost
                        type="danger"
                        @click="changeStatus('rejected')">
                        {{ $t('helpdesk.cancel_action') }}
                    </a-button>
                </div>
            </a-spin>

            <transition v-if="!isMobile" name="slide-fade">
                <div v-if="ticket.status.code === 'completed' && !ticket.rating" class="pb-2">
                    <div class="rew_wrapper_info">
                        <h2>{{ $t('helpdesk.rate_service_quality') }}</h2>
                        <SmileSelect v-model="rewForm.rating" class="mb-5" />
                        <a-textarea
                            v-model="rewForm.description"
                            size="large"
                            :placeholder="$t('helpdesk.rating_comment')"
                            :auto-size="{ minRows: 3, maxRows: 12 }" />
                        <a-button
                            type="primary"
                            size="large"
                            block
                            class="mt-2"
                            :loading="completedLoading"
                            @click="completedTicket(false)">
                            {{ $t('helpdesk.send') }}
                        </a-button>
                    </div>
                </div>
            </transition>

            <transition name="slide-fade">
                <DrawerAside v-if="ticket.status.code === 'completed' && ticket.rating">
                    <ListView :inline="!isMobile" labelDark>
                        <ListViewItem :title="$t('helpdesk.rating')">
                            <ViewRating :rating="ticket.rating.rating" labelView />
                        </ListViewItem>
                        <ListViewItem v-if="ticket.rating.description">
                            {{ ticket.rating.description }}
                        </ListViewItem>
                    </ListView>
                </DrawerAside>
            </transition>

            <div v-if="isMobile" class="h-1" />
        </a-col>

        <a-modal
            title=""
            :visible="endVisible"
            :width="500"
            @cancel="closeEndVisible()">
            <div class="rew_wrapper">
                <h2>{{ $t('helpdesk.rate_service_quality') }}</h2>
                <SmileSelect v-model="rewForm.rating" class="mb-5" />
                <a-textarea
                    v-model="rewForm.description"
                    size="large"
                    :placeholder="$t('helpdesk.rating_comment')"
                    :auto-size="{ minRows: 3, maxRows: 12 }" />
            </div>
            <template #footer>
                <a-button
                    type="primary"
                    size="large"
                    block
                    :loading="completedLoading"
                    @click="completedTicket(true)">
                    {{ $t('helpdesk.accept_result') }}
                </a-button>
            </template>
        </a-modal>
    </a-row>
</template>

<script>
import eventBus from '@/utils/eventBus'
let reloadTimer;
import { errorHandler } from '@/utils/index.js'
export default {
    components: {
        DrawerAside: () => import('@apps/UIModules/DrawerAside'),
        ChatList: () => import('../components/ChatList/index.vue'),
        TextViewer: () => import('@apps/CKEditor/TextViewer.vue'),
        SmileSelect: () => import('../components/SmileSelect.vue'),
        ViewRating: () => import('../components/ViewRating.vue')
    },
    props: {
        ticket: {
            type: Object,
            required: true
        },
        edit: {
            type: Boolean,
            default: false
        },
        listPageName: {
            type: String,
            required: true
        },
        listModel: {
            type: String,
            required: true
        },
        actions: {
            type: Object,
            default: () => null
        },
        getTicket: {
            type: Function,
            default: () => {}
        },
        tab: {
            type: String,
            default: "info"
        },
        getActions: {
            type: Function,
            default: () => {}
        },
        forceReload: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        showRelatedChat() {
            const channelCode = this.ticket?.channel?.code
            const isInternalChat = channelCode === 'internal_chat' || channelCode === 'internal'
            return Boolean(isInternalChat && this.ticket?.related_chat?.name && (this.ticket?.related_chat?.chat_uid || this.ticket?.related_chat?.id))
        },

        // === только для статусов ===
        palette() {
            return {
                red: '#fed4d4',
                volcano: '#FA541C',
                orange: '#FA8C16',
                gold: '#FAAD14',
                yellow: '#FADB14',
                lime: '#A0D911',
                green: '#52C41A',
                cyan: '#13C2C2',
                blue: '#e8ecfa',
                geekblue: '#2F54EB',
                purple: '#722ED1',
                magenta: '#EB2F96',
                grey: '#666666',
            }
        },
        availableStatuses() {
            return Array.isArray(this.actions?.change_status?.available_statuses)
                ? this.actions.change_status.available_statuses
                : []
        },
        availableStatusByCode() {
            const map = {}
            for (const st of this.availableStatuses) {
                if (st?.code) map[st.code] = st
            }
            return map
        },

        formattedTimer() {
            const s = Number(this.ticket.work_log_duration || 0)
            if (s < 60) {
                return `${this.$t('helpdesk.work_efforts')}: ${s} ${this.plural(s, this.$t('helpdesk.second'), this.$t('helpdesk.seconds_2_4'), this.$t('helpdesk.seconds_many'))}`
            }
            if (s < 3600) {
                const m = Math.floor(s / 60)
                const sec = s % 60
                return `${this.$t('helpdesk.work_efforts')}: ${m} ${this.plural(m, this.$t('helpdesk.minute'), this.$t('helpdesk.minutes_2_4'), this.$t('helpdesk.minutes_many'))} ${sec} ${this.plural(sec, this.$t('helpdesk.second'), this.$t('helpdesk.seconds_2_4'), this.$t('helpdesk.seconds_many'))}`
            }
            const hours = Math.floor(s / 3600)
            const minutes = Math.floor((s % 3600) / 60)
            const seconds = s % 60
            const pad = n => String(n).padStart(2, '0')
            return `${this.$t('helpdesk.work_efforts')}: ${pad(hours)}:${pad(minutes)}:${pad(seconds)} ${this.$t('helpdesk.hour_short')}`
        }
    },
    watch: {
        tab(val) {
            if(val === 'info') {
                this.$nextTick(() => {
                    if(this.$refs?.chatList)
                        this.$refs.chatList.scrollToBottom()
                })
            }
        }
    },
    data() {
        return {
            durationLoading: true,
            duration: 0,
            elapsedSeconds: 0,
            statusLoader: false,
            showAside: true,
            execution_result: "",
            spamLoading: false,
            endVisible: false,
            completedLoading: false,
            rewForm: {
                description: "",
                rating: null
            }
        }
    },
    methods: {
        isSVG(icon) {
            return icon.endsWith('.svg')
        },
        openRelatedChat() {
            const chatUid = this.ticket?.related_chat?.chat_uid || this.ticket?.related_chat?.id
            if (!chatUid) return
            this.$router.push({
                name: 'chat',
                query: { chat_id: chatUid }
            })
        },

        // === только для статусов ===
        isStatusAvailable(code) {
            return !!this.availableStatusByCode?.[code]
        },
        toHex(colorKeyOrHex) {
            if (!colorKeyOrHex) return null
            if (typeof colorKeyOrHex === 'string' && colorKeyOrHex.startsWith('#')) return colorKeyOrHex
            return this.palette?.[colorKeyOrHex] || null
        },
        contrastText(hex) {
            // простая контрастность (для жёлтых/лаймовых делаем чёрный текст)
            const h = hex.replace('#', '')
            if (h.length !== 6) return '#fff'
            const r = parseInt(h.slice(0, 2), 16)
            const g = parseInt(h.slice(2, 4), 16)
            const b = parseInt(h.slice(4, 6), 16)
            const yiq = (r * 299 + g * 587 + b * 114) / 1000
            return yiq >= 160 ? '#111' : '#fff'
        },
        statusBtnStyle(code) {
            const colorKey = this.availableStatusByCode?.[code]?.color
            const hex = this.toHex(colorKey)
            if (!hex) return null
            return {
                backgroundColor: hex,
                borderColor: hex,
                color: hex
            }
        },
        // === конец статусов ===

        async completedTicket(status = true) {
            try {
                this.completedLoading = true
                if(this.rewForm.rating) {
                    await this.$http.post('/vote/rating/', {
                        ...this.rewForm,
                        related_object: this.ticket.id
                    })
                }
                if(status)
                    await this.changeStatus('completed')
                else {
                    await this.getTicket()
                    this.listReload()
                }
                this.rewForm = {
                    description: "",
                    rating: null
                }
                this.endVisible = false
            } catch(error) {
                errorHandler({error})
            } finally {
                this.completedLoading = false
            }
        },
        async changeStatus(status) {
            try {
                this.statusLoader = true
                const queryData = {
                    status
                }
                const { data } = await this.$http.put(`/help_desk/tickets/${this.ticket.id}/status/`, queryData)
                if(data) {
                    await this.getTicket()
                    this.listReload()
                    this.execution_result = ""
                    eventBus.$emit('STATUS_TICKET_KANBAN', {
                        task: data,
                        status
                    })
                }
            } catch(error) {
                errorHandler({error})
            } finally {
                this.statusLoader = false
            }
        },
        closeEndVisible() {
            this.endVisible = false
        },
        ticketEnd() {
            this.endVisible = true
        },
        plural(n, one, few, many) {
            const n10 = n % 10
            const n100 = n % 100
            if (n10 === 1 && n100 !== 11) return one
            if (n10 >= 2 && n10 <= 4 && (n100 < 12 || n100 > 14)) return few
            return many
        },
        changeShowAside(value) {
            this.showAside = value
        },
        listReload() {
            clearTimeout(reloadTimer)
            reloadTimer = setTimeout(() => {
                eventBus.$emit(`update_filter_${this.listModel}_${this.listPageName}`)
            }, 1000)
        },
        checkField({key, type = 'object'}) {
            if(type === 'array') {
                if(this.ticket[key]?.length)
                    return true
            } else {
                if(this.ticket[key])
                    return true
            }
            return false
        },
        getCalendarContainer(trigger) {
            return trigger.parentNode
        }
    }
}
</script>

<style lang="scss" scoped>
/* ✅ ТОЛЬКО статусный блок: фикс перекрытия текста */
.status_actions{
    display: flex;
    flex-direction: column;
    gap: 10px;
}

/* разрешаем перенос именно внутри статусных кнопок */
.status_actions ::v-deep .ant-btn,
.status_actions ::v-deep button{
    white-space: normal;
    height: auto;
    line-height: 1.25;
}

/* остальное — как было */
.rew_wrapper_info{
    padding-top: 10px;
    h2{
        text-align: center;
        margin-bottom: 15px;
        font-size: 18px;
        font-weight: 600;
    }
}
.rew_wrapper{
    padding-top: 30px;
    h2{
        text-align: center;
        margin-bottom: 15px;
        font-size: 18px;
        font-weight: 600;
    }
}
.completed_banner{
    background: #E6EFE3;
    color: var(--text);
    padding: 15px;
    border-radius: 12px;
    word-break: break-word;
}
.slide-fade-enter-active {
  transition: all .3s ease;
}
.slide-fade-leave-active {
  transition: all .3s cubic-bezier(1.0, 0.5, 0.8, 1.0);
}
.slide-fade-enter, .slide-fade-leave-to{
  transform: translateY(10px);
  opacity: 0;
}
.badge-fade-slide-enter-active, .badge-fade-slide-leave-active {
    transition: all 0.3s ease
}
.badge-fade-slide-enter, .badge-fade-slide-leave-to {
    transform: translateX(-8px);
    opacity: 0
}
.description_editor{
    &::v-deep{
        .ck-editor__top{
            position: sticky !important;
            top: 0px !important;
            background: transparent !important;
            z-index: 999999;
        }
        .ck{
            &.ck-toolbar__items{
                margin-right: 0px!important;
            }
            &.ck-toolbar__separator{
                opacity: 0;
                margin-right: 0px!important;
            }
            &.ck-toolbar{
                border: 0px;
                padding-left: 0px!important;
                padding-right: 0px!important;
                margin-left: -7px;
            }
            &.ck-content{
                border: 0px!important;
                box-shadow: none!important;
                padding-left: 0px!important;
                padding-right: 0px!important;
                background: transparent!important;
            }
        }
    }
}
.execution_result{
    min-width: 400px;
}
.channel_icon{
    max-width: 16px;
}
.related-chat-link {
    color: #1677ff;
    cursor: pointer;
    text-decoration: underline;
}
.priority_icon{
    position: relative;
    overflow: hidden;
    width: 28px;
    height: 28px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    &__bg{
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        opacity: 0.1;
    }
    i{
        position: relative;
        z-index: 5;
    }
}
</style>
