<template>
    <div class="page_padding">
        <h1 v-if="showPageTitle && pageH1Title" class="m_page_title">
            {{ pageH1Title }}
        </h1>
        <div>
            <ListItem
                v-for="item in list" 
                :item="item" 
                :key="item.id" />
            <infinite-loading
                :ref="getRef"
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
            <div 
                v-if="showEmpty" 
                class="pt-8">
                <a-empty />
            </div>
        </div>
        <div class="float_add">
            <slot name="viewButton" />
            <div class="filter_slot">
                <PageFilter 
                    :model="model"
                    :key="name"
                    :name="name"
                    size="large"
                    :page_name="page_name" />
            </div>
            <a-button
                v-if="showAddButton"
                flaticon
                shape="circle"
                size="large"
                type="primary"
                icon="fi-rr-plus"
                @click="createConsolidation" />
        </div>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import InfiniteLoading from 'vue-infinite-loading'

export default {
    name: 'ConsolidationListMobile',
    components: {
        InfiniteLoading,
        ListItem: () => import('./ListItem.vue'),
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
        name: {
            type: String,
            default: ''
        },
        showPageTitle: {
            type: Boolean,
            default: () => false
        },
        addButton: {
            type: Boolean,
            default: () => false
        },
        isScheduled: {
            type: Boolean,
            default: () => false
        },
        createConsolidation: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        pageH1Title() {
            return this.$route?.meta?.title ? this.$route.meta.title : null
        },
        getRef() {
            return `infiniteLoading_${this.page_name}`
        }
    },
    data() {
        return {
            loading: false,
            list: [],
            page: 1,
            pageSize: 15,
            infiniteId: new Date(),
            showEmpty: false,
            showAddButton: false
        }
    },
    created() {
    },
    mounted() {
        if(this.addButton) {
            this.getShowAddButton()
        }

        eventBus.$on('update_consolidation_in_list', data => {
            this.updateConsolidationInList(data)
        })

        eventBus.$on('consolidation_list_reload', () => {
            this.reloadList()
        })
      
        eventBus.$on(`update_filter_${this.model}_${this.name}`, () => {
            this.reloadList()
        })
    },
    methods: {
        async getShowAddButton() {
            try {
                const { data } = await this.$http.get(`/consolidation/get_org_administrators`)
                this.showAddButton = data.length ? true : false
            } catch(e) {
                console.log(e)
            }
        },
        checkAndSetShowEmpty() {
            if(this.list && !this.list.length) 
                this.showEmpty = true
            else 
                this.showEmpty = false
        },
        updateConsolidationInList(data) {
            const index = this.list.findIndex(f => f.id === data.id)
            if(index !== -1) {
                this.$set(this.list, index, data)
            }
        },
        openConsolidation(id) {
            const query = Object.assign({}, this.$route.query)
            if(query.consolidation && query.consolidation !== id || !query.consolidation) {
                query.consolidation = id
                this.$router.push({query})
            }
        },
        reloadList() {
            this.page = 1
            this.list = []
            
            this.$nextTick(()=>{
                if(this.$refs[`infiniteLoading_${this.page_name}`]){
                    this.$refs[`infiniteLoading_${this.page_name}`].stateChanger.reset()
                }
            })

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
    beforeDestroy() {
        eventBus.$off('consolidation_list_reload')
        eventBus.$off('update_consolidation_in_list')
        eventBus.$off(`update_filter_${this.model}_${this.name}`)
    }
}
</script>

<style lang="scss" scoped>
.page_padding{
    padding: 15px;
    width: 100%;
    height: calc(100vh - 166px);
    overflow-y: auto;
}
</style>