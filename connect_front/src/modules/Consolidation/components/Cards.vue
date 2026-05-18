<template>
    <div class="page_padding" :class="{'mobile-height': isMobile}">
        <div class="cards">
            <TemplateCard
                v-for="item in list" 
                :item="item" 
                :key="item.id" />
        </div>
        <infinite-loading
            :ref="getRef"
            :identifier="infiniteId"
            @infinite="getList"
            :distance="10">
            <div 
                slot="spinner"
                class="mt-[30px]">
                <a-spin />
            </div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
        <div 
            v-if="showEmpty" 
            class="pt-8">
            <a-empty />
        </div>
        <div v-if="isMobile" class="float_add">
            <slot name="viewButton" />
            <div class="filter_slot">
                <PageFilter 
                    :model="model"
                    :key="name"
                    :name="name"
                    size="large"
                    :page_name="page_name" />
            </div>
        </div>
    </div>
</template>

<script>
import InfiniteLoading from 'vue-infinite-loading'
import eventBus from '@/utils/eventBus'

export default {
    name: 'ConsolidationTemplateCards',
    components: {
        InfiniteLoading,
        TemplateCard: () => import('./TemplateCard.vue'),
        PageFilter: () => import('@/components/PageFilter')
    },
    props: {
        page_name: {
            type: String,
            default: ''
        },
        model: {
            type: String,
            default: ''
        },
        isScheduled: {
            type: Boolean,
            default: () => false
        },
        name: {
            type: String,
            default: ''
        },
    },
    computed: {
        getRef() {
            return `infiniteLoading_${this.page_name}`
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    mounted() {
        eventBus.$on(`update_filter_${this.model}_${this.name}`, () => {
            this.reloadList()
        })
        eventBus.$on('consolidation_list_reload', () => {
            this.reloadList()
        })
        eventBus.$on('template_list_reload', () => {
            this.reloadList()
        })
        eventBus.$on('update_status', (id, field, value) => {
            const index = this.list.findIndex(item => item.id === id)
            if(index !== -1) {
                this.list[index][field] = value
            }
        })
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.model}_${this.name}`)
        eventBus.$off('consolidation_list_reload')
        eventBus.$off('template_list_reload')
        eventBus.$off('update_status')
    },
    data() {
        return {
            loading: false,
            list: [],
            page: 1,
            pageSize: 15,
            infiniteId: new Date(),
            showEmpty: false,
        }
    },
    methods: {
        reloadList() {
            this.page = 1
            this.list = []
            
            this.$nextTick(()=>{
                if(this.$refs[`infiniteLoading_${this.page_name}`]){
                    this.$refs[`infiniteLoading_${this.page_name}`].stateChanger.reset()
                }
            })

        },
        checkAndSetShowEmpty() {
            if(this.list && !this.list.length) 
                this.showEmpty = true
            else 
                this.showEmpty = false
        },
        async getList($state) {
            if(!this.loading) {
                let params = {
                    page: this.page,
                    page_size: this.pageSize,
                    page_name: this.page_name,
                    is_scheduled: this.isScheduled
                }
                this.loading = true
                try {
                    const { data } = await this.$http.get('/consolidation/', {
                        params
                    })
                    if(data?.results?.length === 0) {
                        $state.complete()
                    }
                    if(data?.results?.length) {
                        this.list.push(...data.results)
                        if(data.next) {
                            this.page += 1
                            $state.loaded()
                        } else {
                            $state.complete()
                        }
                    }
                    this.checkAndSetShowEmpty()
                } catch(e) {
                    console.log(e)
                } finally {
                    this.loading = false
                }
            }
        },
    },
}
</script>

<style lang="scss" scoped>
.page_padding{
    padding: 15px;
    height: calc(100vh - 211px);
    overflow-y: auto;
    width: 100%;
    .cards{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        grid-template-rows: auto;
        row-gap: 30px;
        column-gap: 30px;
    }
    @media (max-width: 1890px) {
        .cards{
            grid-template-columns: repeat(3, 1fr);
        }
    }
    @media (max-width: 1460px) {
        .cards{
            grid-template-columns: repeat(2, 1fr);
        }
    }
    @media (max-width: 1020px) {
        .cards{
            grid-template-columns: 1fr;
        }
    }
}
.mobile-height{
    height: calc(100vh - 165px);
    padding: 0 15px 15px 15px;
    }
</style>