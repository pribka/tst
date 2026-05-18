<template>
    <div
        class="kanban-col item-list mr-2"
        :class="!isMobile && hide && 'hide_item'">
        <div class="kanban-col__header item-title">
            <div class="kanban-col__title flex items-center">
                <span class="kanban-col__counter" :class="`kanban-col-color-${column.color}`">
                    <div class="counter_bg" :class="`kanban-col-bg-${column.color}`" />
                    <span class="counter_num">
                        <template v-if="loading && page === 1">
                            <a-spin size="small" />
                        </template>
                        <template v-else>
                            {{ count }}
                        </template>
                    </span>
                </span>
                <span class="kanban-col__name">
                    {{ column.name }}
                </span>
            </div>
            <template v-if="!isMobile">
                <a-button
                    @click="hideBlock()"
                    ghost
                    type="ui"
                    class="kanban-col__toggle"
                    size="small"
                    flaticon
                    icon="fi-rr-caret-square-left_1">
                </a-button>
            </template>
        </div>
        <div
            size="small"
            class="wrapper-item">
            <div
                class="p-2"
                v-if="column.loading && column.page === 1">
                <a-skeleton
                    active
                    :paragraph="{ rows: 4 }" />
            </div>
            <div
                v-if="isMobile || !hide"
                class="scroll_wrap">
                <draggable
                    v-bind="dragOptions"
                    class="list-group"
                    :id="column.name"
                    :forceFallback="true"
                    :list="list"
                    :group="taskType"
                    @end="end"
                    draggable=".active_task"
                    @change="change">
                    <!--:isCompleted="column.code === 'completed' ? true : false"-->
                    <CardKanban
                        @filter="filterItem"
                        v-for="(element) in list"
                        :key="element.id"
                        :item="element" />
                    <infinite-loading
                        :distance="70"
                        :identifier="column.name"
                        :ref="`infinite_${column.code}`"
                        @infinite="infiniteHandler">
                        <div
                            slot="spinner"
                            class="pt-1">
                            <a-spin v-if="list && list.length" />
                        </div>
                        <div slot="no-more"></div>
                        <div slot="no-results"></div>
                    </infinite-loading>
                </draggable>
            </div>
        </div>
    </div>
</template>

<script>
import InfiniteLoading from 'vue-infinite-loading'
import draggable from "vuedraggable"
// import CardKanban from './CardTypes/CardKanban'
import eventBus from '@/utils/eventBus'
import { mapState } from 'vuex'
export default {
    components: {
        draggable,
        InfiniteLoading,
        CardKanban: () => import('./Item')
    },
    props: {
        column: {
            type: Object,
            required: true
        },
        queryParams: {
            type: Object,
            default: () => null
        },
        selectElement: {
            type: Object,
            default: () => null
        },
        setSelectElement: {
            type: Function,
            default: () => {}
        },
        implementType: {
            type: String,
            default: ''
        },
        implementId: {
            type: [String, Number],
            default: null
        },
        taskType: {
            type: String,
            default: 'tickets'
        },
        page_name: {
            type: String,
            default: ""
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user,
            isMobile: state => state.isMobile
        }),
        filters() {
            if(this.implementId)
                return {
                    [this.implementType]: this.implementId
                }
            else
                return null
        }
    },
    data() {
        return {
            pageSize: 15,
            dragOptions: {
                animation: 200,
                ghostClass: "ghost",
                chosenClass: "drag-chosen",
                dragClass: "dragging-card"
            },
            page: 1,
            loading: false,
            next: true,
            list: [],
            count: 0,
            hide: localStorage.getItem(`tickets_hide_col_${this.column.code}`) ? localStorage.getItem(`tickets_hide_col_${this.column.code}`) : false,
            listCount: 0
        }
    },
    created() {
        if(this.hide)
            this.infiniteHandler()
    },
    methods: {
        checkReload() {
            if(this.listCount < this.count && this.next) {
                this.reload(true)
            }
        },
        reload(last = false) {
            if(this.hide) {
                this.page = 1
                this.count = 0
                this.listCount = 0

                this.next = true
                this.list = []
                this.setSelectElement(null)
                this.infiniteHandler()
            } else {
                if(last) {
                    this.page = this.page - 1
                    this.latUpdateHandler()
                } else {
                    this.page = 1
                    this.count = 0
                    this.listCount = 0

                    this.next = true
                    this.list = []
                    this.setSelectElement(null)

                    this.$nextTick(() => {
                        this.$refs[`infinite_${this.column.code}`].stateChanger.reset()
                    })
                }
            }
        },
        hideBlock() {
            this.hide = !this.hide

            if(this.hide)
                localStorage.setItem(`tickets_hide_col_${this.column.code}`, true)
            else
                localStorage.removeItem(`tickets_hide_col_${this.column.code}`)
        },
        end(e) {
            // console.log(e, 'el')
        },
        changeListCount() {
            this.count += 1
            this.listCount += 1
            if(this.count >= this.pageSize && this.list.length < this.count)
                this.list.splice(this.list.length - 1, 1)
        },
        async change(e) {
            try{
                let element = null

                if(e.added) {
                    element = e.added.element

                    try {
                        const index = this.list.findIndex(f => f.id === element.id)

                        let previous = null,
                            next = null;

                        if(index !== -1) {
                            next = this.list[index - 1] ? this.list[index - 1].id : null
                            previous = this.list[index + 1] ? this.list[index + 1].id : null
                        }

                        await this.$http.put(`/help_desk/tickets/${element.id}/status/`, {
                            current: element.id,
                            status: this.column.code,
                            previous,
                            next
                        })
                        this.changeListCount()
                        eventBus.$emit('update_ticket_data')
                        eventBus.$emit('update_ticket_data_inject')
                        eventBus.$emit('update_ticket_data_detail')
                        eventBus.$emit('update_ticket_data_detail_inject')
                    } catch(e) {
                        console.log(e)
                    }
                }
                if(e.removed) {
                    if(this.count > 0) {
                        this.listCount -= 1
                        this.count -= 1
                    }
                }
                if(e.moved) {
                    element = e.moved.element
                    try {
                        const index = this.list.findIndex(f => f.id === element.id)

                        let previous = null,
                            next = null;

                        if(index !== -1) {
                            next = this.list[index - 1] ? this.list[index - 1].id : null
                            previous = this.list[index + 1] ? this.list[index + 1].id : null
                        }

                        await this.$http.put(`/tasks/task_kanban/${element.id}/status/`, {
                            current: element.id,
                            status: this.column.code,
                            previous,
                            next
                        })
                    } catch(e) {
                        console.log(e)
                    }
                }
            } catch(error) {
                console.log(error)
            }
        },
        filterItem(data){
            const query = Object.assign(this.$route.query, data)
            this.$router.replace({name: "kanban"})
            this.$router.push({name: "kanban", query: query})
        },
        async latUpdateHandler() {
            try {
                const idx = 0
                this.loading = true
                const params = {...this.queryParams}

                if(params.sprint)
                    delete params.sprint

                params['filters'] = {status: this.column.code}
                params['page_name'] = this.page_name
                params['page'] = this.page
                params['page_size'] = this.pageSize

                if(this.filters) {
                    params['filters'] = {
                        ...params['filters'],
                        ...this.filters
                    }
                }

                const res =  await this.$http('help_desk/tickets/', {params} )

                res.data.results.forEach(item => {
                    const find = this.list.find(f => f.id === item.id)
                    if(!find) {
                        this.list.push(item)
                    }
                })

                this.count = res.data.count
                this.listCount = this.list.length

                if(res.data.next) {
                    this.page += 1
                    this.next = true
                } else {
                    this.next = false
                }
            } catch(error){
                this.$message.error(this.$t('task.error') + error)
            } finally {
                this.loading = false
            }
        },
        async infiniteHandler($state = null) {
            if(this.next) {
                if(!this.loading) {
                    try {
                        const idx = 0
                        this.loading = true
                        const params = {...this.queryParams}

                        if(params.sprint)
                            delete params.sprint

                        params['filters'] = {status: this.column.code}
                        params['page_name'] = this.page_name
                        params['page'] = this.page
                        params['page_size'] = this.pageSize

                        if(this.filters) {
                            params['filters'] = {
                                ...params['filters'],
                                ...this.filters
                            }
                        }

                        const res =  await this.$http('help_desk/tickets/', {params} )
                        this.list = this.list.concat(res.data.results)
                        this.count = res.data.count
                        this.listCount = this.list.length

                        if(res.data.next) {
                            this.page += 1
                            this.next = true
                            if($state)
                                $state.loaded()

                        } else {
                            this.next = false
                            if($state)
                                $state.complete()
                        }
                    } catch(error){
                        this.$message.error(this.$t('task.error') + error)
                    } finally {
                        this.loading = false
                    }
                }
            } else
            if($state)
                $state.complete()
        },
        deleteColumnTask(task) {
            if(this.list.length) {
                const index = this.list.findIndex(f => f.id === task.id)
                if(index !== -1) {
                    this.$delete(this.list, index)
                    if(this.count > 0)
                        this.count -= 1

                    if(!this.list.length && this.count)
                        this.$nextTick(() => {
                            this.$refs[`infinite_${this.column.code}`].stateChanger.reset()
                        })
                }
            }
        }
    },
    mounted() {
        if(this.implementId) {
            eventBus.$on(`RELOAD_COLUMN_FROM_${this.implementId}`, () => {
                this.reload()
            })
        }

        eventBus.$on(`RELOAD_COLUMN_${this.column.code}`, () => {
            this.checkReload()
        })

        eventBus.$on('STATUS_TICKET_KANBAN', ({task, status}) => {
            this.deleteColumnTask(task)

            if(this.column.code === status) {
                this.list.unshift(task)
                this.changeListCount()
            }
        })
        eventBus.$on(`update_filter_data_${this.page_name}`, () => {
            this.reload()
        })
        eventBus.$on('DELETE_TICKET_KANBAN', data => {
            this.deleteColumnTask(data)
        })
        eventBus.$on('UPDATE_TICKET_KANBAN', data => {
            if(this.list?.length) {
                const index = this.list.findIndex(f => f.id === data.id)
                if(index !== -1) {
                    this.$set(this.list, index, data)
                }
            }
        })
        eventBus.$on('ADD_TICKET_KANBAN', data => {
            if(this.column.code === 'new') {
                this.list.unshift(data)
                this.changeListCount()
            }
        })
    },
    beforeDestroy() {
        if(this.implementId)
            eventBus.$off(`RELOAD_COLUMN_FROM_${this.implementId}`)
        eventBus.$off(`update_filter_data_${this.page_name}`)
        eventBus.$off(`DELETE_TICKET_KANBAN`)
        eventBus.$off(`UPDATE_TICKET_KANBAN`)
        eventBus.$off(`ADD_TICKET_KANBAN`)
        eventBus.$off('STATUS_TICKET_KANBAN')
        eventBus.$off(`RELOAD_COLUMN_${this.column.code}`)
    }
}
</script>


<style lang="scss" scoped>
.kanban-col__header {
    display: grid;
    grid-template-areas: "title toggle";
    padding: 12px 16px;
}

.kanban-col__title {
    grid-area: title;
    display: flex;
}

.kanban-col__toggle {
    grid-area: toggle;
    justify-self: self-end;
}
.kanban-col-color-purple{
    color: var(--cPurple);
}
.kanban-col-color-geekblue{
    color: var(--cGeekblue);
}
.kanban-col-color-blue{
    color: var(--cBlue);
}
.kanban-col-color-green{
    color: var(--cGreen);
}
.kanban-col-color-lime{
    color: var(--cLime);
}
.kanban-col-color-cyan{
    color: var(--cCyan);
}
.kanban-col-color-gold{
    color: var(--cGold);
}
.kanban-col-color-yellow{
    color: var(--cYellow);
}
.kanban-col-color-orange{
    color: var(--cOrange);
}
.kanban-col-color-volcano{
    color: var(--cVolcano);
}
.kanban-col-color-red{
    color: var(--cRed);
}
.kanban-col-color-magenta{
    color: var(--cMagenta);
}
.kanban-col-color-pink{
    color: var(--cPink);
}
.kanban-col__counter {
    margin-right: 8px;
    min-width: 24px;
    height: 24px;
    border-radius: 24px;
    overflow: hidden;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0 5px;
    .counter_num{
        position: relative;
        z-index: 5;
    }
    .counter_bg{
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        opacity: 0.1;
        background: #fff;
    }
    .kanban-col-bg-purple{
        background: var(--cPurple);
    }
    .kanban-col-bg-geekblue{
        background: var(--cGeekblue);
    }
    .kanban-col-bg-blue{
        background: var(--cBlue);
    }
    .kanban-col-bg-green{
        background: var(--cGreen);
    }
    .kanban-col-bg-lime{
        background: var(--cLime);
    }
    .kanban-col-bg-cyan{
        background: var(--cCyan);
    }
    .kanban-col-bg-gold{
        background: var(--cGold);
    }
    .kanban-col-bg-yellow{
        background: var(--cYellow);
    }
    .kanban-col-bg-orange{
        background: var(--cOrange);
    }
    .kanban-col-bg-volcano{
        background: var(--cVolcano);
    }
    .kanban-col-bg-red{
        background: var(--cRed);
    }
    .kanban-col-bg-magenta{
        background: var(--cMagenta);
    }
    .kanban-col-bg-pink{
        background: var(--cPink);
    }
}
.kanban-col__name{
    &::v-deep{
        .ant-badge-status-text{
            color: #000;
        }
    }
}

.hide_item {
    &.kanban-col {
        width: 50px;
        min-width: 50px;
    }

    .kanban-col__header {
        grid-template-rows: 50px 1fr 1fr;
        grid-template-areas:
            "toggle"
            "title"
            ".";

        justify-content: center;

        height: 100%;
    }

    .kanban-col__title {
        align-self: self-end;
        flex-direction: column-reverse;
    }

    .kanban-col__toggle {
        align-self: self-start;
        transform: rotate(180deg);
    }

    .kanban-col__counter {
        margin: 0;
        margin-bottom: 16px;
        margin-top: 8px;
    }

    .kanban-col__name {
        writing-mode: sideways-lr;
        text-orientation: mixed;
        &::v-deep {
            .ant-badge-status-text {
                margin: 0;
                margin-bottom: 10px;
            }
            .ant-badge-status-dot {
                margin-left: -2px;
            }
        }
    }
}

.list-group::v-deep{
    min-height: 50%;
}

.scroll_wrap{
    padding-left: 7px;
    padding-right: 7px;
    height: 100%;
    overflow-y: auto;
    overflow-x: hidden;
}
.wrapper-item{
    height: calc(100% - 48px);
}

.item-list::v-deep {
    min-width: 340px;
    max-width: 340px;
    height: 100%;
    scroll-snap-align: start;
    flex-grow: 0;
    background-color: #ffffff;
    border-radius: var(--borderRadius);
    flex-shrink: 0;
    padding-bottom: 5px;
    overflow: hidden;

    .ant-card{
        box-shadow: 0 1px 0 rgba(9, 30, 66, 0.15);
        border: 0px;
    }
}
</style>
