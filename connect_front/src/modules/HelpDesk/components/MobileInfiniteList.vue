<template>
    <div class="mobile_infinite_list">
        <div v-if="empty && !loading" class="mt-5">
            <slot name="empty">
                <a-empty :description="emptyDescription" />
            </slot>
        </div>

        <template v-for="(item, index) in list.results">
            <slot
                name="item"
                :item="item"
                :index="index"
                :list="list">
                <!-- fallback: если слот не передали, можно отрендерить itemComponent -->
                <component
                    v-if="itemComponent"
                    :is="itemComponent"
                    :key="getKey(item, index)"
                    v-bind="getItemProps(item, index)" />
            </slot>
        </template>

        <infinite-loading
            ref="list_infinity"
            @infinite="getList"
            :identifier="infiniteId"
            :distance="distance">
            <div slot="spinner" class="flex items-center justify-center inf_spinner">
                <slot name="spinner">
                    <a-spin />
                </slot>
            </div>
            <div slot="no-more"><slot name="no-more" /></div>
            <div slot="no-results"><slot name="no-results" /></div>
        </infinite-loading>
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'

export default {
    name: 'MobileInfiniteList',
    components: {
        InfiniteLoading: () => import('vue-infinite-loading')
    },
    props: {
        // строка "/api/..." или функция () => "/api/..."
        url: { type: [String, Function], required: true },

        // чтобы принудительно перезапускать (например ticket.id)
        reloadKey: { type: [String, Number, Boolean, Object, Array], default: null },

        // для infinite-loading
        identifier: { type: [String, Number], default: 'list' },
        distance: { type: Number, default: 10 },

        // подпись в пустом состоянии
        emptyDescription: { type: String, default: '' },

        // опционально: если не хочешь слоты — можно передать компонент
        itemComponent: { type: [Object, Function, String], default: null },
        itemProps: { type: [Object, Function], default: () => ({}) },
        itemKey: { type: String, default: 'id' },

        // опционально: кастомный fetcher вместо this.$http.get
        fetcher: { type: Function, default: null }
    },
    data() {
        return {
            loading: false,
            empty: false,
            infiniteId: this.identifier,

            nextUrl: null,
            list: {
                results: [],
                count: 0
            }
        }
    },
    methods: {
        getFirstUrl() {
            return typeof this.url === 'function' ? this.url() : this.url
        },
        normalizeNextUrl(url) {
            if (!url) return null
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
        async request(url) {
            if (this.fetcher) return this.fetcher(url)
            return this.$http.get(url)
        },
        reset() {
            this.$nextTick(() => {
                this.loading = false
                this.empty = false
                this.list = { results: [], count: 0 }
                this.nextUrl = this.getFirstUrl()

                this.infiniteId = `${this.identifier}_${Date.now()}`
                if (this.$refs.list_infinity?.stateChanger) {
                    this.$refs.list_infinity.stateChanger.reset()
                }

                this.$emit('reset')
            })
        },
        getKey(item, index) {
            return (item && item[this.itemKey]) || item?.id || index
        },
        getItemProps(item, index) {
            return typeof this.itemProps === 'function'
                ? this.itemProps(item, index)
                : (this.itemProps || {})
        },
        async getList($state) {
            if (this.loading) return

            if (!this.nextUrl) {
                $state.complete()
                return
            }

            try {
                this.loading = true

                const url = this.normalizeNextUrl(this.nextUrl)
                const { data } = await this.request(url)

                if (data) {
                    this.list.count = data.count
                    this.nextUrl = this.normalizeNextUrl(data.next)

                    if (Array.isArray(data.results) && data.results.length) {
                        this.list.results = this.list.results.concat(data.results)
                    }
                }

                this.empty = !this.list.results.length

                this.$emit('loaded-page', data)

                if (this.nextUrl) $state.loaded()
                else $state.complete()
            } catch (error) {
                errorHandler({ error, show: false })
                this.$emit('error', error)
                $state.complete()
            } finally {
                this.loading = false
            }
        }
    },
    watch: {
        reloadKey() {
            this.reset()
        }
    },
    mounted() {
        this.nextUrl = this.getFirstUrl()
    }
}
</script>

<style scoped>
.inf_spinner {
    padding: 16px 0;
}
</style>
