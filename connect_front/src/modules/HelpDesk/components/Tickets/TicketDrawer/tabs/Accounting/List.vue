<template>
    <div>
        <div v-if="empty" class="mt-5">
            <a-empty :description="$t('calendar.no_data')" />
        </div>

        <TimeCard
            v-for="item in list.results"
            :key="item.id"
            :ticket="ticket"
            :item="item"
            :pageModel="pageModel"
            :pageName="pageName"
            :colParams="colParams" />

        <infinite-loading
            ref="list_infinity"
            @infinite="getList"
            :identifier="infiniteId"
            v-bind:distance="10">
            <div slot="spinner" class="flex items-center justify-center inf_spinner">
                <a-spin />
            </div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
import eventBus from '@/utils/eventBus'

export default {
    components: {
        TimeCard: () => import('./TimeCard.vue'),
        InfiniteLoading: () => import('vue-infinite-loading')
    },
    props: {
        ticket: { type: Object, required: true },
        pageModel: { type: String, required: true }, // ✅ сюда должен прилетать HelpDeskTicketWorkLogModel
        pageName: { type: String, required: true },
        colParams: { type: Object, default: () => null } // ✅ ticket.id + getTimer + getPopupContainer
    },
    data() {
        return {
            loading: false,
            empty: false,
            infiniteId: this.pageName,

            nextUrl: null,
            list: {
                results: [],
                count: 0
            }
        }
    },
    methods: {
        buildFirstUrl() {
            // первая страница
            return `/help_desk/tickets/${this.ticket.id}/work_log/list/`
        },
        normalizeNextUrl(url) {
            if (!url) return null
            // Если DRF вернул абсолютный next (https://domain/...),
            // режем origin, чтобы axios с baseURL не ломался.
            if (typeof url === 'string' && url.startsWith('http')) {
                try {
                    const u = new URL(url)
                    return u.pathname + u.search
                } catch (e) {
                    return url
                }
            }
            return url
        },
        listReload() {
            this.$nextTick(() => {
                this.loading = false
                this.empty = false
                this.list = { results: [], count: 0 }
                this.nextUrl = this.buildFirstUrl()

                // чтобы InfiniteLoading точно перезапустился
                this.infiniteId = `${this.pageName}_${Date.now()}`

                if (this.$refs.list_infinity?.stateChanger) {
                    this.$refs.list_infinity.stateChanger.reset()
                }
            })
        },
        async getList($state) {
            if (this.loading) return

            // ✅ если nextUrl пустой — значит всё
            if (!this.nextUrl) {
                $state.complete()
                return
            }

            try {
                this.loading = true

                const url = this.normalizeNextUrl(this.nextUrl)
                const { data } = await this.$http.get(url)

                if (data) {
                    this.list.count = data.count
                    this.nextUrl = this.normalizeNextUrl(data.next)

                    if (Array.isArray(data.results) && data.results.length) {
                        this.list.results = this.list.results.concat(data.results)
                    }
                }

                if (!this.list.results.length) {
                    this.empty = true
                }

                if (this.nextUrl) $state.loaded()
                else $state.complete()
            } catch (error) {
                errorHandler({ error, show: false })
                $state.complete()
            } finally {
                this.loading = false
            }
        }
    },
    watch: {
        'ticket.id': function () {
            this.listReload()
        }
    },
    mounted() {
        this.nextUrl = this.buildFirstUrl()

        eventBus.$on(`update_filter_${this.pageModel}_${this.pageName}`, () => {
            this.listReload()
        })
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.pageModel}_${this.pageName}`)
    }
}
</script>

<style scoped>
.inf_spinner {
    padding: 16px 0;
}
</style>
