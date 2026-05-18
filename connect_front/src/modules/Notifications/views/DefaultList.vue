<template>
    <div>
        <CardLoading v-if="loading && page === 1" class="mt-3" />
        <a-list
            v-else
            class="mt-1"
            :size="isMobile ? 'small' : 'large'"
            :style="isMobile && 'min-height: 90vh;'">
            <transition-group
                tag="div"
                name="noty-read-remove">
                <a-list-item
                    v-for="item in list"
                    :key="item.id">
                    <ListItem
                        :item="item"
                        @read="readNoty(item)" />
                </a-list-item>
            </transition-group>
            <a-empty
                v-if="!loading && list.length === 0"
                class="mt-4"
                :description="$t('noty.emptyList')" />
            <infinite-loading
                v-if="showInfinity"
                ref="notify_infinity"
                v-bind:distance="10"
                @infinite="scrollHandler">
                <div slot="spinner">
                    <a-spin
                        class="mt-4"
                        v-show="loading && page > 1 && list.length" />
                </div>
                <div slot="no-more"></div>
                <div slot="no-results"></div>
            </infinite-loading>
        </a-list>
    </div>
</template>

<script>
import { mapActions, mapGetters, mapMutations } from 'vuex'
import { errorHandler } from '@/utils/index.js'
import notySyncChannel from '@/utils/notySyncChannel'

export default {
    name: "DefaultNotificationsList",
    components: {
        InfiniteLoading: () => import('vue-infinite-loading'),
        ListItem: () => import('./ListItem.vue'),
        CardLoading: () => import('./CardLoading.vue')
    },
    props: {
        pageName: {
            type: String,
            required: true
        },
        filters: {
            type: Object,
            default: () => ({})
        },
        filtersKey: {
            type: String,
            default: ''
        },
        suspendFiltersWatcher: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            loading: false,
            showInfinity: false,
            filtersReloadTimer: null,
            notySyncUnsubscribe: null,
            mountedReady: false
        }
    },
    computed: {
        ...mapGetters({
            list: "notifications/getListNoty",
        }),
        isMobile() {
            return this.$store.state.isMobile
        },
        hideReadNotifications() {
            return !!this.$store.state.user.user?.hide_read_notifications
        },
        next() {
            return this.$store.state.notifications.next
        },
        page() {
            return this.$store.state.notifications.page
        }
    },
    watch: {
        filtersKey() {
            if (!this.mountedReady) return
            if (this.suspendFiltersWatcher) return
            this.scheduleFiltersReload()
        }
    },
    methods: {
        ...mapActions({
            getListNoty: "notifications/getListNoty",
            cancelListNotyRequest: "notifications/cancelListNotyRequest",
            readNotyy: "notifications/readNoty",
        }),
        ...mapMutations({
            clearList: "notifications/clearList",
            removeNotyFromList: "notifications/REMOVE_NOTY_FROM_LIST",
            removeNotyByCategories: "notifications/REMOVE_NOTY_BY_CATEGORIES",
            removeMentionNotyFromList: "notifications/REMOVE_MENTION_NOTY_FROM_LIST"
        }),
        readNoty(item) {
            if(!item.is_read)
                this.readNotyy({
                    id: item.id,
                    isMention: !!item.is_mention,
                    categoryCode: item?.category?.code || null,
                    objectId: item?.object_id || null
                }).then(() => {
                    if (this.hideReadNotifications)
                        this.removeNotyFromList(item.id)
                }).catch(() => {})
        },
        onSyncMessage(msg) {
            if (!msg || !msg.type || !this.hideReadNotifications) return

            if (msg.type === 'read_one' && msg.id) {
                this.removeNotyFromList(msg.id)
                return
            }

            if (msg.type === 'read_all') {
                this.clearList()
                return
            }

            if (msg.type === 'read_by_categories' && Array.isArray(msg.category_codes)) {
                this.removeNotyByCategories(msg.category_codes)
                return
            }

            if (msg.type === 'read_mentions') {
                this.removeMentionNotyFromList()
            }
        },
        applyReadAll(payload = {}) {
            if (!this.hideReadNotifications) return

            const categoryCodes = Array.isArray(payload.categoryCodes) ? payload.categoryCodes : []
            if (payload.isMention) {
                this.removeMentionNotyFromList()
                return
            }

            if (categoryCodes.length) {
                this.removeNotyByCategories(categoryCodes)
                return
            }

            this.clearList()
        },
        resetListState() {
            this.$store.commit('notifications/SET_PAGE', 0)
            this.$store.commit('notifications/SET_NEXT', true)
            this.clearList()
        },
        scheduleFiltersReload() {
            if (this.filtersReloadTimer)
                clearTimeout(this.filtersReloadTimer)

            this.filtersReloadTimer = setTimeout(() => {
                this.reload()
                this.filtersReloadTimer = null
            }, 1000)
        },
        async scrollHandler($state = null) {
            if(!this.loading && this.next) {
                try {
                    this.loading = true
                    const res = await this.getListNoty({
                        page_name: this.pageName,
                        filters: this.filters,
                        reset: this.page === 0
                    })
                    if (!res) {
                        if($state)
                            $state.loaded()
                        return
                    }
                    if(!res.next) {
                        if($state)
                            $state.complete()

                    } else {
                        if($state)
                            $state.loaded()
                    }
                } catch(error) {
                    errorHandler({error, show: false})
                } finally {
                    this.loading = false
                }
            } else {
                if($state)
                    $state.complete()
            }
        },
        async reload() {
            this.cancelListNotyRequest()
            this.loading = false
            this.showInfinity = false
            this.resetListState()

            await this.$nextTick()
            await this.scrollHandler()
            this.showInfinity = true
        }
    },
    async mounted() {
        this.resetListState()
        await this.scrollHandler()
        this.showInfinity = true
        this.mountedReady = true
        this.notySyncUnsubscribe = notySyncChannel.subscribe(this.onSyncMessage)
    },
    beforeDestroy() {
        if (this.filtersReloadTimer)
            clearTimeout(this.filtersReloadTimer)
        if (this.notySyncUnsubscribe)
            this.notySyncUnsubscribe()
        this.cancelListNotyRequest()
        this.showInfinity = false
    }
}
</script>

<style lang="scss" scoped>
.noty-read-remove-leave-active {
    transition: transform .24s ease, opacity .24s ease;
}
.noty-read-remove-leave-to {
    opacity: 0;
    transform: translateX(80px);
}
</style>
