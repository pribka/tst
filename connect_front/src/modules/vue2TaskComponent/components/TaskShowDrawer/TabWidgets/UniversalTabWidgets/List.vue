<template>
    <div 
        v-if="tableInfo" 
        class="tab_list">
        <div 
            class="grid table_head"
            :style="gridColumns && `grid-template-columns: ${gridColumns};`">
            <div 
                v-for="column in tableInfo.columns" 
                :key="column.key" 
                class="col">
                {{ column.title }}
            </div>
        </div>
        <div 
            v-if="list && list.results.length"
            class="table_body">
            <div 
                v-for="item in list.results" 
                :key="item.id" 
                class="grid table_item" 
                :style="gridColumns && `grid-template-columns: ${gridColumns};`">
                <div 
                    v-for="column in tableInfo.columns" 
                    :key="column.key" 
                    class="col">
                    <WidgetSwitch 
                        :column="column"
                        :row="item"
                        :allColumns="tableInfo.columns"
                        :code="code"
                        :task="task"
                        :item="item[column.key]" />
                </div>
            </div>
        </div>
        <infinite-loading 
            @infinite="getList"
            :identifier="task.id+code"
            v-bind:distance="10">
            <div 
                slot="spinner"
                class="flex items-center justify-center inf_spinner py-2">
                <a-spin />
            </div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
    </div>
</template>

<script>
import { mapGetters } from 'vuex'
import WidgetSwitch from './ListWidgets/WidgetSwitch.vue'
import InfiniteLoading from 'vue-infinite-loading'
import eventBus from '@/utils/eventBus'
export default {
    components: {
        WidgetSwitch,
        InfiniteLoading
    },
    props: {
        task: {
            type: Object,
            default: () => null
        },
        code: {
            type: [String, Number],
            required: true
        }
    },
    computed: {
        ...mapGetters({
            getTabList: 'task/getTabList',
            getTabTable: 'task/getTabTable'
        }),
        tableInfo() {
            return this.getTabTable(this.task.id, this.code)
        },
        gridColumns() {
            if(this.tableInfo?.columns?.length) {
                let columsSetting = []
                this.tableInfo.columns.forEach((item) => {
                    if(item.width)
                        columsSetting.push(`${item.width}px`)
                    else
                        columsSetting.push('1fr')
                })
                return columsSetting.join(' ')
            } else
                return null
        },
        defaultPageSize() {
            return this.tableInfo?.pagination?.defaultPageSize ? this.tableInfo.pagination.defaultPageSize : 15
        }
    },
    data() {
        return {
            page: 0,
            loading: false,
            list: {
                count: 0,
                next: true,
                results: []
            }
        }
    },
    methods: {
        async getList($state) {
            if(!this.loading && this.list.next) {
                try {
                    this.page += 1
                    this.loading = true
                    const {data} = await this.$http(`/tasks/${this.code}/`, {
                        params: {
                            task: this.task.id,
                            page: this.page,
                            page_size: this.defaultPageSize
                        }
                    })

                    if(data) {
                        this.list.results = this.list.results.concat(data.results)
                        this.list.count = data.count
                        this.list.next = data.next
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
            } else
                $state.complete()
        }
    },
    mounted() {
        eventBus.$on(`universal_tab_add_${this.task.id}_${this.code}`, data => {
            this.list.count += 1
            this.list.results.unshift(data)
            if(this.list.count >= this.defaultPageSize && this.list.results.length < this.list.count) {
                console.log(this.list.results.length, this.list.count)
                this.list.results.splice(this.list.results.length - 1, 1)
            }
        })
        eventBus.$on(`universal_tab_update_${this.task.id}_${this.code}`, data => {
            if(this.list.results?.length) {
                const index = this.list.results.findIndex(f => f.id === data.id)
                if(index !== -1)
                    this.$set(this.list.results, index, data)
            }
        })
        eventBus.$on(`universal_tab_delete_${this.task.id}_${this.code}`, id => {
            if(this.list.results?.length) {
                const index = this.list.results.findIndex(f => f.id === id)
                if(index !== -1)
                    this.$delete(this.list.results, index)
            }
        })
    },
    beforeDestroy() {
        eventBus.$off(`universal_tab_add_${this.task.id}_${this.code}`)
        eventBus.$off(`universal_tab_update_${this.task.id}_${this.code}`)
        eventBus.$off(`universal_tab_delete_${this.task.id}_${this.code}`)
    }
}
</script>

<style lang="scss" scoped>
.tab_list{
    .table_head{
        border-bottom: 1px solid var(--borderColor);
        background: #fafafa;
        .col{
            padding: 13px 10px;
            display: flex;
            align-items: center;
            font-weight: 600;
        }
    }
    .table_body{
        .col{
            padding: 13px 10px;
            display: flex;
            align-items: center;
        }
        .table_item{
            &:not(:last-child){
                border-bottom: 1px solid var(--borderColor);
            }
        }
    }
}
</style>