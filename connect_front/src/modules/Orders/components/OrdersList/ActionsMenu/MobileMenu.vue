<template>
    <div>    
        <ActivityDrawer v-model="visible">
            <ActivityItem
                v-if="!actionsList && listLoading"
                key="menu_loader">
                <div class="flex justify-center w-full">
                    <a-spin size="small" />
                </div>
            </ActivityItem>
            <template v-if="actionsList">
                <template v-if="actionsList.change_status">
                    <ActivityItem 
                        v-if="record.status === 'new'" 
                        key="start" 
                        @click="$emit('start')"
                        icon="fi-rr-comment" >
                        Начать
                    </ActivityItem>
                    <ActivityItem 
                        v-if="record.status=== 'in_process'" 
                        key="end" 
                        @click="$emit('end')"
                        icon="fi-rr-checkbox"> 
                        Завершить
                    </ActivityItem>
                </template>
                <ActivityItem  
                    key="open" 
                    @click="openOrder()"
                    icon="fi-rr-eye">
                    Просмотр
                </ActivityItem>
                <ActivityItem 
                    v-if="actionsList.edit" 
                    key="edit" 
                    @click="orderEdit()"
                    icon="fi-rr-edit">
                    Редактировать
                </ActivityItem>
                <ActivityItem 
                    v-if="actionsList.share" 
                    key="share" 
                    @click="$emit('share')"
                    icon="fi-rr-thumbtack">
                    Поделиться
                </ActivityItem>
                <ActivityItem 
                    v-if="actionsList.add_task && canAddTask"
                    key="addTask"
                    icon="fi-rr-list-check"
                    @click="$emit('addTask')">
                    Добавить задачу
                </ActivityItem>
            </template>
        </ActivityDrawer>
    </div>
</template>

<script>
import { ActivityItem, ActivityDrawer } from '@/components/ActivitySelect'
import mixins from './mixins.js'
export default {
    mixins: [mixins],
    components: {
        ActivityItem,
        ActivityDrawer
    },
    data() {
        return {
            visible: false,
            menuLoading: false
        }
    },
    watch: {
        visible(val) {
            if(!val) {
                this.visibleChange(false)
            }
        }
    },
    methods: {
        openDrawer() {
            this.visible = true
            this.visibleChange(this.visible)
        }
    }
}
</script>