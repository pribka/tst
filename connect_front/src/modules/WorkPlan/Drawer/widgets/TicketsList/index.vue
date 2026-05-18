<template>
    <div class="list_card">
        <div class="mb-3 flex items-center gap-2">
            <a-input
                v-model="search"
                :placeholder="$t('workplan.search')"
                size="large"
                class="tab_search"
                :class="useInject && 'bg_invert'"
                @change="changeSearch()">
                <template #suffix>
                    <transition name="fade-scale" mode="out-in">
                        <a-button
                            v-if="search.length"
                            type="ui_ghost"
                            size="small"
                            flaticon
                            shape="circle"
                            icon="fi-rr-cross-small"
                            @click="clearSearch()" />
                        <i v-else class="fi fi-rr-search mr-1" />
                    </transition>
                </template>
            </a-input>
            <div>
                <a-button v-if="isMobile" type="primary" style="min-width: auto;" shape="circle" size="large" flaticon icon="fi-rr-plus" @click="addTicket()" />
                <a-button v-else type="primary" style="min-width: auto;" size="large" flaticon icon="fi-rr-plus" @click="addTicket()">
                    {{ $t('workplan.add_ticket') }}
                </a-button>
            </div>
        </div>
        <div class="mb-3 flex">
            <div :class="isMobile && 'mob_scroll'">
                <div :style="isMobile && 'padding-left:15px;padding-right:15px;'">
                    <Segmented
                        v-model="role"
                        deselectable
                        :bgInvert="useInject"
                        :options="roleList"
                        @change="reloadTicketData" />
                </div>
            </div>
        </div>

        <div v-if="list.results && list.results.length" class="ticket_block_item">
            <h2 class="ticket_block_title">
                <a-badge status="processing" class="mr-1" />
                {{ $t('workplan.activity_today') }}
            </h2>
            <template v-if="list.page === 1 && list.loading">
                <CardLoading v-for="i in 3" :key="i" :useInject="useInject" />
            </template>
            <Card
                v-for="ticket in list.results"
                :key="ticket.id"
                :storeKey="storeKey"
                :isActiveTab="isActiveTab"
                :useInject="useInject"
                listType="ticketList"
                :ticket="ticket" />
            <a-button
                v-if="list.results.length && list.next"
                :loading="list.loading"
                type="ui"
                ghost
                block
                @click="nextLoading('activity')">
                {{ $t('workplan.load_more') }}
            </a-button>
        </div>

        <div class="ticket_block_item">
            <h2 class="ticket_block_title">
                <a-badge status="default" class="mr-1" />
                {{ $t('workplan.others') }}
            </h2>
            <a-empty v-if="otherList.empty" :description="$t('workplan.no_tickets')" />
            <template v-if="otherList.page === 1 && otherList.loading">
                <CardLoading v-for="i in 5" :key="`other_${i}`" :useInject="useInject" />
            </template>
            <Card
                v-for="ticket in otherList.results"
                :key="`other_${ticket.id}`"
                :storeKey="storeKey"
                :isActiveTab="isActiveTab"
                :useInject="useInject"
                listType="ticketOtherList"
                :ticket="ticket" />
            <a-button
                v-if="otherList.results.length && otherList.next"
                :loading="otherList.loading"
                type="ui"
                ghost
                block
                @click="nextLoading('other')">
                {{ $t('workplan.load_more') }}
            </a-button>
        </div>
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
import eventBus from '@/utils/eventBus'

const listType = 'ticketList'
const listOtherType = 'ticketOtherList'
let searchTimer;

export default {
    props: {
        storeKey: {
            type: String,
            required: true
        },
        isActiveTab: {
            type: Boolean,
            default: false
        },
        useInject: {
            type: Boolean,
            default: false
        }
    },
    components: {
        Card: () => import('./Card.vue'),
        CardLoading: () => import('./CardLoading.vue'),
        Segmented: () => import('@apps/UIModules/Segmented')
    },
    data() {
        return {
            roleList: [
                {
                    key: 'is_operator',
                    title: this.$t('workplan.role_do')
                },
                {
                    key: 'is_owner',
                    title: this.$t('workplan.role_delegate')
                }
            ]
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        list() {
            return this.$store.state.workplan[listType]?.[this.storeKey] || null
        },
        otherList() {
            return this.$store.state.workplan[listOtherType]?.[this.storeKey] || null
        },
        search: {
            get() {
                return this.list?.search || ""
            },
            set(value) {
                this.$store.commit('workplan/CHANGE_LIST_FIELD', {
                    field: 'search',
                    value,
                    storeKey: this.storeKey,
                    list: listType
                })
                this.$store.commit('workplan/CHANGE_LIST_FIELD', {
                    field: 'search',
                    value,
                    storeKey: this.storeKey,
                    list: listOtherType
                })
            }
        },
        role: {
            get() {
                return this.$store.state.workplan.ticketRole?.[this.storeKey] || null
            },
            set(value) {
                this.$store.commit('workplan/CHANGE_FIELD', {
                    value,
                    field: 'ticketRole',
                    storeKey: this.storeKey
                })
            }
        }
    },
    methods: {
        addTicket() {
            eventBus.$emit('helpdesc_add_tickets')
        },
        clearSearch() {
            this.search = ""
            clearTimeout(searchTimer)
            this.reloadList()
        },
        changeSearch() {
            clearTimeout(searchTimer)
            searchTimer = setTimeout(() => {
                this.reloadList()
            }, 700)
        },
        reloadTicketData() {
            this.reloadList()
        },
        reloadList() {
            this.$store.commit('workplan/CLEAR_LIST', {
                storeKey: this.storeKey,
                list: listType
            })
            this.$store.commit('workplan/CLEAR_LIST', {
                storeKey: this.storeKey,
                list: listOtherType
            })
            this.getList()
            this.getOtherList()
        },
        nextLoading(group = 'activity') {
            let listGroup = listType

            if(group === 'other') {
                listGroup = listOtherType
                this.$store.commit('workplan/CHANGE_LIST_FIELD', {
                    field: 'page',
                    value: this.otherList.page + 1,
                    storeKey: this.storeKey,
                    list: listGroup
                })
            } else {
                this.$store.commit('workplan/CHANGE_LIST_FIELD', {
                    field: 'page',
                    value: this.list.page + 1,
                    storeKey: this.storeKey,
                    list: listGroup
                })
            }

            if(group === 'other')
                this.getOtherList()
            else
                this.getList()
        },
        async getList(reload = false, loading = true) {
            try {
                await this.$store.dispatch('workplan/getTicketList', { storeKey: this.storeKey, list: listType, group: 'activity', reload, loading })
            } catch(error) {
                errorHandler({error, show: false})
            }
        },
        async getOtherList(reload = false, loading = true) {
            try {
                await this.$store.dispatch('workplan/getTicketList', { storeKey: this.storeKey, list: listOtherType, group: 'other', reload, loading })
            } catch(error) {
                errorHandler({error, show: false})
            }
        },
        resetVisibleTicketTimers() {
            const lists = [this.list?.results || [], this.otherList?.results || []]

            lists.forEach(items => {
                items.forEach(item => {
                    if (!item?.is_current) return
                    this.$set(item, 'is_current', false)
                    this.$set(item, 'started_timer', false)
                })
            })
        },
        handleGlobalTimerSync(payload = {}) {
            if (payload?.entity === 'task' && payload?.action === 'start_timer') {
                this.resetVisibleTicketTimers()
            }
        }
    },
    sockets: {
        ticket_update({ data }) {
            if(data) {
                this.$store.dispatch('workplan/updateItem', {
                    item: data,
                    list: 'ticketList'
                })
            }
        }
    },
    mounted() {
        this.$socket.client.emit('tickets')

        if(!this.list.results?.length && !this.list.empty)
            this.getList()
        if(!this.otherList.results?.length && !this.otherList.empty)
            this.getOtherList()
        if(!this.list.results?.length && this.list.empty && !this.otherList.results?.length && this.otherList.empty)
            this.reloadList()
        eventBus.$on('global_timer_sync_required', this.handleGlobalTimerSync)
    },
    beforeDestroy() {
        eventBus.$off('global_timer_sync_required', this.handleGlobalTimerSync)
        if(!this.useInject) return
        this.$store.commit('workplan/CLEAR_LIST', {
            storeKey: this.storeKey,
            list: listType
        })
        this.$store.commit('workplan/CLEAR_LIST', {
            storeKey: this.storeKey,
            list: listOtherType
        })
    }
}
</script>

<style lang="scss" scoped>
.ticket_block_item{
    &:not(:last-child){
        margin-bottom: 15px;
    }
}
.ticket_block_title{
    font-weight: 600;
    font-size: 18px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
}
.fade-scale-enter-active,
.fade-scale-leave-active {
    transition: opacity .15s ease, transform .15s ease
}
.fade-scale-enter,
.fade-scale-leave-to {
    opacity: 0;
    transform: scale(.55)
}
.tab_search{
    &.bg_invert{
        &::v-deep{
            .ant-input{
                background: #f7f9fc;
            }
        }
    }
}
</style>
