<template>
    <a-drawer
        :title="$t('support.section_select')"
        class="select_c_drawer"
        :width="isMobile ? '100%' : 460"
        :zIndex="9999999"
        :destroyOnClose="true"
        :visible="taskDrawer"
        @close="closeHandler()">
        <div 
            class="drawer_body" 
            ref="subtask_scroll">
            <div class="drawer_scroll">
                <div class="p-3 max-w-full">
                    <div
                        class="flex items-center chapter_d_item" 
                        v-for="item in taskList" 
                        :key="item.id"
                        :class="checkSelected(item) && 'selected'"
                        @click="selectTask(item)">
                        {{ item.name }}
                    </div>
                </div>
                <infinite-loading 
                    ref="userInfinite" 
                    @infinite="getTaskList" 
                    v-bind:distance="10">
                    <div slot="spinner">
                        <a-spin />
                    </div>
                    <div slot="no-more"></div>
                    <div slot="no-results"></div>
                </infinite-loading>
            </div>
        </div>
    </a-drawer>
</template>

<script>
import { errorHandler } from '@/utils/index.js'

export default {
    components: {
        InfiniteLoading: () => import('vue-infinite-loading')
    },
    props: {
        value: {
            type: Object
        },
        taskDrawer: {
            type: Boolean,
            default: false
        },
        closeHandler: {
            type: Function,
            required: true
        },
        filters: {
            type: Object,
            default: null
        },
        selectParentTask: {
            type: Function,
            required: true
        }
    },
    data() {
        return {
            taskList: [],
            scrollStatus: true,
            page: 0,
            loading: false
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    methods: {
        getPopupContainer() {
            return this.$refs['subtask_scroll']
        },
        checkSelected(task) {
            if(this.value) {
                if(task.id === this.value.id)
                    return true
                else
                    return false
            } else
                return false
        },
        selectTask(item) {
            this.$emit('input', item)
            this.closeHandler()
            this.selectParentTask(item)
        },
        async getTaskList($state = null) {
            if(!this.loading && this.scrollStatus && this.taskDrawer) {
                try {
                    this.loading = true
                    this.page = this.page+1
                    const params = {
                        page_size: 15,
                        page: this.page
                    }

                    const {data} = await this.$http.get('/wiki/sections/', {params})
                    if(data && data.results.length)
                        this.taskList = this.taskList.concat(data.results)
                    if(!data.next) {
                        if($state)
                            $state.complete()
                        this.scrollStatus = false
                    } else {
                        if($state)
                            $state.loaded()
                    }
                } catch(error) {
                    errorHandler({ error, show: false })
                } finally {
                    this.loading = false
                }
            } else {
                if($state)
                    $state.complete()
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.chapter_d_item{
    padding: 15px;
    cursor: pointer;
    margin-bottom: 10px;
    border: 1px solid var(--border2);
    &.selected{
        border-color: var(--blue);
    }
}
</style>
