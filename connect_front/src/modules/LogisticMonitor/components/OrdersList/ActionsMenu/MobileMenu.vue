<template>
    <div>
        <a-button 
            :loading="loading" 
            icon="menu" 
            type="link"
            @click="visible = true"/>       
        <ActivityDrawer v-model="visible">
            <ActivityItem
                v-if="!actionsList && listLoading"
                key="menu_loader">
                <a-spin size="small" />
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
                    {{$t('task.share_to_chat')}}
                </ActivityItem>
                <ActivityItem 
                    v-if="actionsList.add_task && canAddTask"
                    key="addTask"
                    @click="$emit('addTask')">
                    {{$t('task.add_task')}}
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
    }
}
</script>