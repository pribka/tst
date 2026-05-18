<template>
    <a-popover 
        v-model="visible" 
        :title="viewCountText" 
        trigger="click"
        :getPopupContainer="getPopupContainer"
        overlayClassName="views_popup"
        transitionName=""
        @visibleChange="visibleChange">
        <slot />
        <template #content>
            <div class="popup_task_list">
                <div v-for="task in list.results" :key="task.id" class="truncate task_item cursor-pointer" :title="`#${task.counter} ${task.name}`" @click="openTask(task)">
                    <div class="truncate">
                        <span style="opacity: 0.6;">#{{ task.counter }}</span> <span class="blue_color">{{ task.name }}</span>
                    </div>
                    <div v-if="task.dead_line" class="flex items-center mt-1 text-xs">
                        <i class="fi fi-rr-calendar-clock mr-2" />
                        {{ $moment(task.dead_line).format('DD.MM.YYYY HH:mm') }}
                    </div>
                </div>
                <infinite-loading 
                    v-if="visible && list.next"
                    ref="task_infinity"
                    @infinite="getList"
                    :identifier="infiniteId"
                    v-bind:distance="10">
                    <div 
                        slot="spinner"
                        class="flex items-center justify-center inf_spinner">
                        <a-spin size="small" />
                    </div>
                    <div slot="no-more"></div>
                    <div slot="no-results"></div>
                </infinite-loading>
            </div>
            <div class="footer_content">
                <a-button type="ui_ghost" size="small" block @click="visible = false">
                    {{ $t('close') }}
                </a-button>
            </div>
        </template>
    </a-popover>
</template>

<script>
import { declOfNum } from '@/utils/utils.js'
import { errorHandler } from '@/utils/index.js'
export default {
    props: {
        item: {
            type: Object,
            required: true
        },
        getPopupContainer: {
            type: Function,
            default: () => document.body
        }
    },
    components: {
        InfiniteLoading: () => import('vue-infinite-loading'),
    },
    computed: {
        viewCount() {
            const count = this.item.task_count
            if(count < 0)
                return 0
            return count
        },
        viewCountText() {
            return `${this.viewCount} ${declOfNum(this.viewCount, [this.$t('comment.task_count_1'), this.$t('comment.task_count_2'), this.$t('comment.task_count_3')])}`
        },
        isMobile() {
            return this.$store.state.isMobile
        },
    },
    data() {
        return {
            visible: false,
            infiniteId: Date.now(),
            page: 0,
            loading: false,
            list: {
                next: true,
                count: 0,
                results: []
            }
        }
    },
    methods: {
        openTask(task) {
            if(this.$route.query?.task) {
                if(this.$route.query.task !== task.id) {
                    const query = JSON.parse(JSON.stringify(this.$route.query))
                    delete query.task
                    delete query.stab
                    this.$router.replace({query})
                    setTimeout(() => {
                        const query2 = JSON.parse(JSON.stringify(this.$route.query))
                        query2.task = task.id
                        this.$router.push({query: query2})
                    }, 400)
                }
            } else {
                const query = JSON.parse(JSON.stringify(this.$route.query))
                query.task = task.id
                this.$router.push({query})
            }
        },
        visibleChange(vis) {
            if(!vis)
                this.clearList()
        },
        clearList() {
            if (this.$refs.task_infinity) {
                this.$refs.task_infinity.stateChanger.complete()
            }

            this.infiniteId = Date.now()
            this.page = 0
            this.list = {
                next: true,
                count: 0,
                results: []
            }
        },
        openPopup() {
            this.visible = true
        },
        async getList($state) {
            if(!this.loading && this.list.next) {
                try {
                    this.loading = true
                    this.page += 1
                    const { data } = await this.$http.get('/tasks/list_from_reason/', {
                        params: {
                            reason: this.item.id,
                            page: this.page,
                            page_size: 15
                        }
                    })

                    if(data) {
                        this.list.count = data.count
                        this.list.next = data.next
                    }

                    if (data?.results?.length)
                        this.list.results = this.list.results.concat(data.results)

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
    }
}
</script>

<style lang="scss" scoped>
.popup_task_list{
    max-width: 270px;
    min-width: 270px;
    padding: 12px 16px;
    overflow-y: auto;
    max-height: 220px;
}
.footer_content{
    padding: 8px 16px;
}
.task_item{
    background: #eef2f4;
    border-radius: 8px;
    max-width: 300px;
    padding: 6px 10px;
    &:not(:last-child){
        margin-bottom: 10px;
    }
}
</style>

<style lang="scss">
.views_popup{
    .ant-popover-arrow{
        display: none;
    }
    .ant-popover-title{
        border-bottom: 0px;
    }
    &.ant-popover-placement-top, 
    &.ant-popover-placement-topLeft, 
    &.ant-popover-placement-topRight{
        padding-bottom: 0px;
    }
    &.ant-popover-placement-bottom, 
    &.ant-popover-placement-bottomLeft, 
    &.ant-popover-placement-bottomRight{
        padding-top: 0px;
    }
    .ant-popover-inner-content{
        padding: 0px;
    }
}
</style>