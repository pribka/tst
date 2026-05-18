<template>
    <ActivityDrawer v-model="visible">
        <template v-if="actionsList">
            <ActivityItem
                v-if="actionsList.open" 
                key="open"
                @click="open()">
                <i class="fi fi-rr-search-alt"></i>
                Открыть
            </ActivityItem>
            <ActivityItem
                v-if="actionsList.edit" 
                key="edit"
                @click="edit()">
                <i class="fi fi-rr-edit"></i>
                Редактировать
            </ActivityItem>
            <ActivityItem
                v-if="actionsList.delete" 
                key="delete"
                class="text-red-500"
                @click="deleteHandler()">
                <i class="fi fi-rr-trash"></i>
                Удалить
            </ActivityItem>
        </template>
    </ActivityDrawer>
</template>

<script>
import { ActivityItem, ActivityDrawer } from '@/components/ActivitySelect'
import mixins from './mixins'
export default {
    name: 'ActionsDrawer',
    components: {
        ActivityItem,
        ActivityDrawer
    },
    mixins: [mixins]
}
</script>