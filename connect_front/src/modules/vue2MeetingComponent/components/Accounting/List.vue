<template>
    <div>
        <div 
            v-if="empty" 
            class="mt-5">
            <a-empty :description="$t('calendar.no_data')" />
        </div>
        <TimeCard 
            v-for="item in list.results" 
            :key="item.id" 
            :editTime="editTime"
            :deleteHandler="deleteHandler"
            :pageModel="pageModel"
            :pageName="pageName"
            :meeting="meeting"
            :item="item" />
        <infinite-loading 
            ref="list_infinity"
            @infinite="getList"
            :identifier="infiniteId"
            v-bind:distance="10">
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
import initProps from './props.js'
import { errorHandler } from '@/utils/index.js'
import eventBus from "@/utils/eventBus"
export default {
    components: {
        TimeCard: () => import('./TimeCard.vue'),
        InfiniteLoading: () => import('vue-infinite-loading')
    },
    props: {...initProps},
    data() {
        return {
            loading: false,
            page: 0,
            empty: false,
            infiniteId: this.pageName,
            list: {
                results: [],
                next: true,
                count: 0
            }
        }
    },
    methods: {
        listReload() {
            this.$nextTick(() => {
                this.page = 0
                this.empty = false
                this.list = {
                    results: [],
                    next: true,
                    count: 0
                }
                this.$refs['list_infinity'].stateChanger.reset()
            })
        },
        async getList($state) {
            if(!this.loading && this.list.next) {
                try {
                    this.loading = true
                    this.page += 1
                    const { data } = await this.$http.get('/tasks/time_tracking/', {
                        params: {
                            page: this.page,
                            page_size: 15,
                            page_name: this.pageName,
                            model: this.pageModel,
                            meeting_section: this.meeting.id
                        }
                    })

                    if(data) {
                        this.list.count = data.count
                        this.list.next = data.next
                    }

                    if(data?.results?.length)
                        this.list.results = this.list.results.concat(data.results)

                    if(this.page === 1 && !this.list.results.length) {
                        this.empty = true
                    }  
                    if(this.list.next)
                        $state.loaded()
                    else
                        $state.complete()
                } catch(error) {
                    errorHandler({error, show: false})
                } finally {
                    this.loading = false
                }
            }
        },
    },
    mounted() {
        eventBus.$on(`update_filter_${this.pageModel}_${this.pageName}`, () => {
            this.listReload()
        })
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.pageModel}_${this.pageName}`)
    }
}
</script>