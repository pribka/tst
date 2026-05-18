<template>
    <ActivityDrawer v-model="visible">
        <template v-if="actionsList">
            <ActivityItem
                v-if="actionsList.open" 
                key="open"
                @click="openConsolidation()">
                <i class="fi fi-rr-search-alt"></i>
                {{$t('Open')}}
            </ActivityItem>
            <ActivityItem
                v-if="actionsList.edit" 
                key="edit"
                @click="edit()">
                <i class="fi fi-rr-edit"></i>
                {{$t('Edit')}}
            </ActivityItem>
            <ActivityItem
                v-if="actionsList.delete" 
                key="delete"
                class="text-red-500"
                @click="deleteHanlder()">
                <i class="fi fi-rr-trash"></i>
                {{$t('Delete')}}
            </ActivityItem>
        </template>
    </ActivityDrawer>
</template>

<script>
import { ActivityItem, ActivityDrawer } from '@/components/ActivitySelect'
import mixins from './mixins'
export default {
    components: {
        ActivityItem,
        ActivityDrawer
    },
    mixins: [mixins]
}
</script>