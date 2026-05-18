<template>
    <div v-if="!isTask" class="flex items-center">
        <a-dropdown 
            :destroyPopupOnHide="true">
            <a-button 
                :loading="loading" 
                icon="menu" 
                type="link" />
            <a-menu slot="overlay">
                <template>
                    <a-menu-item 
                        key="add"
                        class="flex items-center"
                        @click="addTask">
                        <i class="fi fi-rr-folder-tree mr-2"></i>
                        {{$t('task.add_task')}}
                    </a-menu-item>
                    <a-menu-item 
                        key="add_milestone"
                        class="flex items-center"
                        @click="addMilestone">
                        <i class="fi fi-rr-folder-tree mr-2"></i>
                        {{$t('task.add_milestone')}}
                    </a-menu-item>
                </template>
            </a-menu>
        </a-dropdown>
        <span class="">
            {{ record.order }}
        </span>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    props: {
        record: {
            type: Object,
            required: true
        },
        pageName: {
            type: String,
            default: ''
        }
    },
    computed: {
        isTask() {
            return this.record.hasOwnProperty('task_type')
        }
    },
    data() {
        return{
            loading: false,
            actionLoading: false
        }
    },
    methods: {
        addTask() { 
            this.addHandler() 
        },
        addMilestone() { 
            this.addHandler('milestone') 
        },
        addHandler(taskType='task') {
            const template = { 
                name: '', 
                description: '',
                task_type: taskType, 
                id: new Date(),
                new: true,
                project_stage: this.record.id,
            }
            eventBus.$emit(`table_row_${this.pageName}`, {
                action: 'expand',
                parentId: this.record.id,
                row: [template]
            })
        }    
    },
    
}
</script>