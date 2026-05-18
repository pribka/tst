<template>
    <div class="h-full">
        <div
            v-if="empty"
            class="mt-5">
            <a-empty :description="$t('workplan.day_pulse_empty')" />
        </div>
        <EmployeePulseMobileCard
            v-for="item in list.results"
            :key="item.id"
            :item="item"
            :open="openCard" />
        <infinite-loading
            ref="list_infinity"
            :identifier="infiniteId"
            @infinite="getList"
            :distance="10">
            <div
                slot="spinner"
                class="flex items-center justify-center inf_spinner">
                <a-spin />
            </div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
    </div>
</template>

<script>
import { dateFormat } from '../../utils.js'

export default {
    components: {
        InfiniteLoading: () => import('vue-infinite-loading'),
        EmployeePulseMobileCard: () => import('../../components/EmployeePulseMobileCard.vue')
    },
    props: {
        initPageName: {
            type: String,
            default: ""
        },
        initPageModel: {
            type: String,
            default: ""
        },
        openUserModal: {
            type: Function,
            default: () => {}
        },
        dateRange: {
            type: Array,
            default: () => []
        }
    },
    computed: {
        startDate() {
            if (!this.dateRange?.[0]) return null
            return dateFormat(this.$moment(this.dateRange[0]).clone().startOf('day'))
        },
        endDate() {
            if (!this.dateRange?.[1]) return null
            return dateFormat(this.$moment(this.dateRange[1]).clone().endOf('day'))
        },
        hasDateRange() {
            return Boolean(this.startDate && this.endDate)
        },
        dateRangeKey() {
            const start = this.dateRange?.[0] ? this.$moment(this.dateRange[0]).format('YYYY-MM-DDTHH:mm:ss') : ''
            const end = this.dateRange?.[1] ? this.$moment(this.dateRange[1]).format('YYYY-MM-DDTHH:mm:ss') : ''
            return `${start}_${end}`
        }
    },
    watch: {
        dateRangeKey() {
            this.listReload()
        }
    },
    data() {
        return {
            loading: false,
            empty: false,
            page: 0,
            infiniteId: Date.now(),
            list: {
                results: [],
                next: true,
                count: 0
            }
        }
    },
    methods: {
        openCard(record) {
            this.openUserModal(record)
        },
        listReload() {
            this.$nextTick(() => {
                this.page = 0
                this.empty = false
                this.loading = false
                this.list = {
                    results: [],
                    next: true,
                    count: 0
                }
                if (this.$refs['list_infinity']?.stateChanger)
                    this.$refs['list_infinity'].stateChanger.reset()
                else
                    this.infiniteId = Date.now()
            })
        },
        async getList($state) {
            if (this.loading) return
            if (!this.hasDateRange || !this.list.next) {
                this.empty = !this.list.results.length
                $state.complete()
                return
            }

            try {
                this.loading = true
                this.page += 1
                const { data } = await this.$http.get('/day_summary/note/list_latest/', {
                    params: {
                        page: this.page,
                        page_size: 15,
                        page_name: this.initPageName,
                        model: this.initPageModel,
                        start: this.startDate,
                        end: this.endDate
                    }
                })
                this.list.count = data?.count || 0
                this.list.next = Boolean(data?.next)

                const results = Array.isArray(data?.results) ? data.results : []
                if (results.length)
                    this.list.results = this.list.results.concat(results)

                this.empty = this.page === 1 && !this.list.results.length
                if (this.list.next)
                    $state.loaded()
                else
                    $state.complete()
            } catch (e) {
                $state.complete()
            } finally {
                this.loading = false
            }
        }
    }
}
</script>
