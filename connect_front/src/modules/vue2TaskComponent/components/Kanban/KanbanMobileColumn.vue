<template>
    <div 
        class="item-list">
        <div class="flex">
            <a-tag 
                class="w-full mx-0 mb-2 px-2 py-1 text-sm text-center"
                :color="column.color">
                {{ columnTitle }}
            </a-tag>
        </div>
        <template v-if="loading && page === 1">
            <div class="my-2 flex justify-center w-full">
                <a-spin size="default" />
            </div>
        </template>
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
            <div class="scroll_wrap">
                <CardKanban
                    @filter="filterItem"
                    v-for="(element) in list"
                    :key="element.id"
                    activeMobile
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
            </div>
        </div>
    </div>
</template>

<script>
import InfiniteLoading from 'vue-infinite-loading'
import eventBus from '@/utils/eventBus'
import { mapState } from 'vuex'
export default {
    components: {
        InfiniteLoading,
        CardKanban: () => import('./CardTypes/CardKanban')
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
            default: 'task'
        },
        pageName: {
            type: String,
            default: ''
        },
        slideIndex: {
            type: Number,
            required: true
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user,
            isMobile: state => state.isMobile,
            mobileSlideIndex: state => state.task.mobileSlideIndex
        }),
        filters() {
            if(this.implementId)
                return {
                    [this.implementType]: this.implementId
                }
            else
                return null
        },
        columnTitle() {
            if(this.loading && this.page === 1) {
                return `${this.column.name }...`
            }

            let taskLabelForm = this.$t('task.task3')
            if((this.count < 5) || (this.count > 20)) {
                const remaind = this.count % 10
                if(remaind === 1) {
                    taskLabelForm = this.$t('task.task')
                } else if((remaind > 1) && (remaind < 5)) {
                    taskLabelForm = this.$t('task.task-list-page')
                }
            } 
            return `${this.column.name } - ${ this.count } ${ taskLabelForm}`
        },
        isCurrentSlide() {
            return this.mobileSlideIndex[this.pageName] === this.slideIndex
        }
    },
    data() {
        return {
            pageSize: 15,
            pageModel: `page_kanban_${this.taskType}_tasks.TaskModel`,
            dragOptions: {
                animation: 200,
                ghostClass: "ghost"
            },
            page: 1,
            loading: false,
            next: true,
            list: [],
            count: 0,
            listCount: 0
        }
    },
    sockets: {
        task_update({data}) {
            if(data) {
                this.handleSocketTaskUpdate(data)
            }
        }
    },
    methods: {
        getTaskStatusCode(task) {
            if (typeof task?.status === 'string') {
                return task.status
            }
            return task?.status?.code || null
        },
        prepareSocketTask(task, baseTask = null) {
            const authorId = task?.author?.id
            const operatorId = task?.operator?.id
            let can_update_status = false

            if(this.user?.id === authorId || this.user?.id === operatorId) {
                can_update_status = true
            }

            return {
                ...(baseTask || {}),
                ...task,
                can_update_status
            }
        },
        handleSocketTaskUpdate(task) {
            if(!task?.id)
                return

            const index = this.list.findIndex(item => item.id === task.id)
            if(index === -1)
                return

            const nextStatusCode = this.getTaskStatusCode(task)
            const currentTask = this.list[index]

            if(nextStatusCode && nextStatusCode !== this.column.code) {
                this.deleteColumnTask(task)
                eventBus.$emit('TASK_SOCKET_MOVE_KANBAN', {
                    task: this.prepareSocketTask(task, currentTask),
                    statusCode: nextStatusCode
                })
                return
            }

            this.$set(this.list, index, this.prepareSocketTask(task, currentTask))
        },
        checkReload() {
            if(this.listCount < this.count && this.next) {
                this.reload(true)
            }
        },
        reload(last = false) {
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

                        await this.$http.put(`/tasks/task_kanban/${element.id}/status/`, { 
                            current: element.id,
                            status: this.column.code,
                            previous,
                            next
                        })
                        this.changeListCount()
                        eventBus.$emit(`RELOAD_COLUMN_${element.status.code}`)
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
                let params = this.$route.query
                params['filters'] = {status: this.column.code}
                params['page_name'] = this.queryParams?.page_name ? this.queryParams.page_name : this.pageModel
                params['page'] = this.page
                params['page_size'] = this.pageSize
                params['task_type'] = this.taskType

                if(this.filters) {
                    params['filters'] = {
                        ...params['filters'],
                        ...this.filters
                    }

                    if(this.queryParams?.filters) {
                        params['filters'] = {
                            ...params['filters'],
                            ...this.queryParams.filters
                        }
                    }
                }

                const res =  await this.$http('tasks/task_kanban/list/', {params} )

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
                        let params = this.$route.query
                        params['filters'] = {status: this.column.code}
                        params['page_name'] = this.queryParams?.page_name ? this.queryParams.page_name : this.pageModel
                        params['page'] = this.page
                        params['page_size'] = this.pageSize
                        params['task_type'] = this.taskType

                        if(this.filters) {
                            params['filters'] = {
                                ...params['filters'],
                                ...this.filters
                            }

                            if(this.queryParams?.filters) {
                                params['filters'] = {
                                    ...params['filters'],
                                    ...this.queryParams.filters
                                }
                            }
                        }

                        const res =  await this.$http('tasks/task_kanban/list/', {params} )
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
        eventBus.$on(`RELOAD_COLUMN_${this.column.code}`, () => {
            this.checkReload()
        })

        eventBus.$on('STATUS_TASK_KANBAN', ({task, status}) => {
            this.deleteColumnTask(task)

            if(this.column.code === status.code) {
                this.list.unshift(task)
                this.changeListCount()
            }
        })
        eventBus.$on(`update_filter_tasks.TaskModel`, () => {
            this.reload()
        })
        eventBus.$on('DELETE_TASK_KANBAN', data => {
            this.deleteColumnTask(data)
        })
        eventBus.$on('UPDATE_TASK_KANBAN', data => {
            if(this.list?.length) {
                const index = this.list.findIndex(f => f.id === data.id)
                if(index !== -1) {
                    this.$set(this.list, index, data)
                }
            }
        })
        eventBus.$on('TASK_SOCKET_MOVE_KANBAN', ({ task, statusCode }) => {
            if(statusCode !== this.column.code)
                return

            const index = this.list.findIndex(item => item.id === task.id)
            if(index !== -1) {
                this.$set(this.list, index, this.prepareSocketTask(task, this.list[index]))
                return
            }

            this.list.unshift(this.prepareSocketTask(task))
            this.changeListCount()
        })
        eventBus.$on('ADD_TASK_KANBAN', data => {
            if(this.column.is_open) {
                this.list.unshift(data)
                this.changeListCount()
            }
        })
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_tasks.TaskModel`)
        eventBus.$off(`DELETE_TASK_KANBAN`)
        eventBus.$off(`UPDATE_TASK_KANBAN`)
        eventBus.$off(`TASK_SOCKET_MOVE_KANBAN`)
        eventBus.$off(`ADD_TASK_KANBAN`)
        eventBus.$off('STATUS_TASK_KANBAN')
        eventBus.$off(`RELOAD_COLUMN_${this.column.code}`)
    }
}
</script>

<style lang="scss">
.list-group{
    min-height: 50%;
}
</style>

<style lang="scss" scoped>
.scroll_wrap{
    height: 100%;
    overflow-y: auto;
    overflow-x: hidden;
}
.wrapper-item{
    height: calc(100% - 40px);
}
.item-list{
    height: 100%;
    scroll-snap-align: start;
    flex-grow: 0;
    background-color: #eff2f5;
    border-radius: var(--borderRadius);
    flex-shrink: 0;
    padding-bottom: 5px;
    overflow: hidden;
    .block_btn{
        margin-right: -7px;
    }
}
</style>
