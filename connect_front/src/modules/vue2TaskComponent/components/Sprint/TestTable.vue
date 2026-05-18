<template>
    <div class="flex-grow flex min-h-0">
        <UniversalTable 
            :model="model"
            :pageName="pageName"
            :tableType="tableType"
            :openHandler="openSprint"
            :endpoint="endpoint"
            :startEdit="startEdit"
            :deleteSprint="deleteSprint"
            :updateStatus="updateStatus" />
    </div>
</template>

<script>
import UniversalTable from '@/components/TableWidgets/UniversalTable'
export default {
    props: {
        tableType: {
            type: String,
            default: 'sprints'
        },
        openSprint: {
            type: Function,
            default: () => {}
        },
        startEdit: {
            type: Function,
            default: () => {}
        },
        deleteSprint: {
            type: Function,
            default: () => {}
        },
        updateStatus: {
            type: Function,
            default: () => {}
        },
        pageName: {
            type: String,
            default: "sprint_list"
        },
        model: {
            type: String,
            default: ''
        },
    },
    components: {
        UniversalTable
    },
    computed: {
        endpoint() {
            return `/tasks/sprint/list/`
        }
    }
}
</script>

<style lang="scss" scoped>
</style>