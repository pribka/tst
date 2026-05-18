<template>
    <div class="tab_list">
        <div
            v-for="item in list.results" 
            :key="item.id"
            class="card">
            <div 
                v-for="column in tableInfo.columns" 
                :key="column.key"
                class="card_item">
                <span v-if="column.title" class="font-semibold card_item_head">
                    {{ column.title }}:
                </span>
                <WidgetSwitch 
                    :column="column"
                    :row="item"
                    :allColumns="tableInfo.columns"
                    :code="code"
                    :task="task"
                    :item="item[column.key]"
                    actionsAsBlock
                    actionsButtonType="default" />
                    
            </div>
        </div>
        <infinite-loading 
            @infinite="getList"
            :identifier="task.id+code"
            :distance="10">
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
.card {
    &:not(:last-child) {
        margin-bottom: 15px;
    }
}
.card_item {
    &:not(:last-child) {
        margin-bottom: 0.2em;
    }
}
.card_item_head {
    &:not(:last-child) {
        margin-bottom: 0.3rem;
    }
}
</style>