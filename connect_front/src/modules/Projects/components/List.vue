<template>
    <div>
        <div 
            v-if="listEmpty" 
            class="pt-7">
            <a-empty :description="$t('project.no_data')" />
        </div>
        <MobileCard 
            v-for="item in list" 
            :key="item.id"
            :listProject="listProject" 
            :item="item"
            :reloadList="reloadList" />
        <infinite-loading 
            @infinite="getAllGroups"
            :identifier="page_name"
            v-bind:distance="5"
            ref="group_infinity">
            <div 
                slot="spinner"
                class="flex items-center justify-center inf_spinner mt-3">
                <a-spin />
            </div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
    </div>
</template>

<script>
import eventBus from "@/utils/eventBus"
export default {
    name: 'GroupList',
    components: {
        InfiniteLoading: () => import('vue-infinite-loading'),
        MobileCard: () => import('./MobileCard.vue')
    },
    props: {
        listProject: {
            type: Boolean,
            default: true
        },
        pageModel: {
            type: String,
            default: 'workgroups.WorkgroupModel'
        },
        page_name: {
            type: String,
            default: 'page_list_project_workgroups.WorkgroupModel'
        }
    },
    computed: {
        pageH1Title() {
            return this.$route?.meta?.title ? this.$route.meta.title : null
        }
    },
    data() {
        return {
            loading: false,
            next: true,
            page: 0,
            list: [],
            pageSize: 15,
            listEmpty: false
        }
    },
    methods: {
        async getAllGroups($state) {
            if (!this.next) {
                $state && $state.complete()
                return
            }
            if (this.loading) return
            this.loading = true
            this.page += 1
            try {
                const { data } = await this.$http.get('/work_groups/workgroups/', {
                    params: {
                        is_project: this.listProject ? 1 : 0,
                        page: this.page,
                        page_size: this.pageSize,
                        page_name: this.page_name
                    }
                })

                const results = Array.isArray(data.results) ? data.results : []
                if (results.length) this.list = this.list.concat(results)

                if (this.page === 1 && !results.length) {
                    this.listEmpty = true
                    this.next = false
                    $state && $state.complete()
                    return
                }

                const hasNext = !!data.next && results.length === this.pageSize
                this.next = hasNext

                if (!this.next) $state && $state.complete()
                else $state && $state.loaded()
            } catch (e) {
                this.$message.error(this.$t('project.error'))
                this.next = false
                $state && $state.complete()
            } finally {
                this.loading = false
            }
        },
        reloadList() {
            if(this.listEmpty)
                this.listEmpty = false

            this.page = 0
            this.next = true
            this.list = []
            this.$nextTick(() => {
                this.$refs['group_infinity'].stateChanger.reset()
            })
        }
    },
    mounted() {
        eventBus.$on(`update_filter_${this.pageModel}`, () => {
            this.reloadList()
        })
        eventBus.$on('update_list_project', () => {
            this.reloadList()
        })
        eventBus.$on('update_list_group', () => {
            this.reloadList()
        })
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.pageModel}`)
        eventBus.$off('update_list_project')
        eventBus.$off('update_list_group')
    }
}
</script>
