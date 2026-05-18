<template>
    <div>
        <KanbanItem
            v-for="task in sprintList"
            :key="task.id"
            :item="task"

            showStatus
            hideDeadline
            :showSprintButton="showSprintButton"
            :active="isActiveTasks"
            :myTaskEnabled="false"
            :sprint-id="sprintId"
            @statusChanged="getTaskCount"
            :removeFromSprint="removeFromSprint"/>

        <infinite-loading
            :distance="10"
            @infinite="upScrollHandler('sprint', $event)">
            <div 
                slot="spinner" 
                class="pt-1">
                <a-spin v-if="sprintList && sprintList.length" />
            </div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
        <a-empty 
            v-if="!taskLoading && !sprintList.length"
            class="mt-4">
            <template #description>
                {{ $t('task.no_active_tasks') }}
            </template>
        </a-empty>
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
export default {
    components: { 
        KanbanItem: () => import('../Kanban/Item.vue'), 
        InfiniteLoading: () => import('vue-infinite-loading')
    },
    props: {
        sprintId: {
            type: String,
            required: true
        },
        getTaskCount: {
            type: Function,
            required: true
        },
        isActiveTasks: {
            type: Boolean,
            default: true
        },
        activeAllData: {
            type: Array,
            required: true
        },
        upScrollHandler: {
            type: Function,
            required: true        
        },
        showSprintButton: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            taskNext: true,
            taskLoading: false,

            page: 1,
            pageSize: 70,
            pageName: 'sprint_kanban_tasks.TaskMode',
        }
    },
    computed: {
        sprintList() {
            const index = this.activeAllData.findIndex(el=> el.name === "sprint")
            return this.activeAllData[index].list
        }
    },
    methods: {
        async getTaskList($state){
            try {
                if(!this.taskLoading && this.taskNext) {
                    this.taskLoading = true              
    
                    let params = {
                        page: this.page,
                        page_size: this.pageSize,
                        page_name: this.pageName,
                        sprint: this.sprintId
                    }
    
                    const response = await this.$http(`tasks/sprint/task/list/`, { params } )
                    
                    this.sprintList.push(...response.data.results)
    
                    if(response.data.next) {
                        this.page += 1
                        this.tasksNext = true
                        $state.loaded()
                    } 
                    else {
                        this.next = false
                        $state.complete()
                    }
    
                    this.taskLoading = false
                }

            }
            catch(error){
                errorHandler({error})
            }

        },
        async removeFromSprint(task) {
            try{
                const status = null
                await  this.$http.put(`/tasks/task/${task.id}/set_sprint/`,
                    { sprint: status })

                if(this.sprintList.includes(task))
                    this.sprintList.splice(this.sprintList.indexOf(task), 1)

                await this.getTaskCount()
            }
            catch(error){
                errorHandler({error})
            }
        }
    },
    created() {
        this.sprintList.splice(0)
    }
}
</script>