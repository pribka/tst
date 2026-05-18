<template>
    <div class="page_block">
        <div v-if="actions && actions.renovation_info && actions.renovation_info.availability" class="mb-4">
            <a-button 
                type="primary" 
                size="large" 
                :block="isMobile" 
                ghost 
                class="px-8" 
                @click="addHanlder()">
                {{ $t('sports.addRepairInfo') }}
            </a-button>
        </div>
        <a-empty v-if="empty" :description="$t('sports.noProjects')" />
        <div class="repair_info_list">
            <RepairCard 
                v-for="item in list.results" 
                :key="item.id"
                :item="item" />
        </div>
        <infinite-loading
            ref="repair_infinity"
            @infinite="getList"
            v-bind:distance="10">
            <div
                slot="spinner"
                class="flex items-center justify-center inf_spinner">
                <a-spin />
            </div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
        <RepairDrawer v-if="actions && actions.renovation_info && actions.renovation_info.availability" />
    </div>
</template>

<script>
import InfiniteLoading from 'vue-infinite-loading'
import eventBus from '@/utils/eventBus'
import { mapState } from 'vuex'
export default {
    components: {
        InfiniteLoading,
        RepairCard: () => import('../components/RepairCard'),
        RepairDrawer: () => import('../components/RepairDrawer')
    },
    computed: {
        ...mapState({
            actions: state => state.facilities.projectActions
        }),
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    data() {
        return {
            list: {
                results: [],
                next: true,
                count: 0
            },
            page: 0,
            empty: false
        }
    },
    methods: {
        addHanlder() {
            eventBus.$emit('add_repair_info')
        },
        listReload() {
            this.page = 0
            this.empty = false
            this.list = {
                results: [],
                next: true,
                count: 0
            }
            this.$nextTick(() => {
                this.$refs['repair_infinity'].stateChanger.reset()
            })
        },
        async getList($state) {
            if(!this.loading && this.list.next) {
                try {
                    this.loading = true
                    this.page += 1
                    let params = {
                        page: this.page,
                        page_size: 8,
                        sport_facility: this.$route.params.id
                    }
                    const { data } = await this.$http.get('/sports_facilities/renovation/', { params })
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
                } catch(e) {
                    console.log(e)
                } finally {
                    this.loading = false
                }
            }
        }
    },
    mounted(){
        eventBus.$on('repair_list_reload', () => {
            this.listReload()
        })
    },
    beforeDestroy() {
        eventBus.$off('repair_list_reload')
    }
}
</script>