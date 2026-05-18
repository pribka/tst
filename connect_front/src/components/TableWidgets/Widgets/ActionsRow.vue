<template>
    <component
        :is="actionWidget"
        :record="record"
        :openOrder="openHandler"
        :item="record"
        :id="record?.id"
        :pageName="pageName"
        :role="record"
        :organization="params?.organization"
        @edit="startEdit"
        @delete="deleteSprint(record.id)"
        @updateStatus="updateStatus"

        :openModalStat="openModalStat"
        :openDescModal="openDescModal" />
</template>

<script>
export default {
    props: {
        model: {
            type: String
        },
        openHandler: {
            type: Function,
            default: () => {}
        },
        record: {
            type: Object,
            required: true
        },
        id: {
            type: [String, Number],
            default: null
        },
        startEdit: {
            type: Function,
            default: () => {}
        },
        deleteSprint: {
            type: Function,
            default: () => {}
        },
        tableType: {
            type: String
        },
        updateStatus: {
            type: Function,
            default: () => {}
        },
        openDescModal: {
            type: Function,
            default: () => {}
        },
        openModalStat: {
            type: Function,
            default: () => {}
        },
        pageName: {
            type: String,
            default: ''
        },
        params: {
            type: Object,
            default: () => {}
        }
    },
    computed: {
        isMyBases() {
            return false //this.tableType === 'tickets'
        },
        isTask() {
            return ['tasks', 'sprint_tasks', 'project-tasks'].includes(this.tableType)
        },
        isChatTask() {
            return this.tableType === 'chat_tasks'
        },
        isSprint() {
            return this.model === 'tasks.TaskSprintModel'
        },
        isOrder() {
            return this.model === 'crm.GoodsOrderModel'
        },
        isMeeting() {
            return this.model === 'meetings.PlannedMeetingModel'
        },
        isAnalytics() {
            return this.tableType === 'analytics'
        },
        isContractors() {
            return this.tableType === 'contractors'
        },
        isLeads() {
            return this.tableType === 'leads'
        },
        isConsolidation() {
            return this.tableType === 'consolidation' || this.tableType === 'consolidation_templates'
        },
        isRoles() {
            return this.tableType === 'roles'
        },
        isModeration() {
            return this.tableType === 'moderation'
        },
        isAccountingReports() {
            return false //this.tableType === 'accounting_reports'
        },
        actionWidget() {
            /*if(this.isMyBases)
                return () => import('@apps/MyBases/components/ViewListActions.vue')*/
            if(this.isTask || this.isChatTask) {
                if(!this.record.is_sign_task)
                    return () => import('@apps/vue2TaskComponent/components/TaskActions/List.vue')
            } if(this.isSprint)
                return () => import('@apps/vue2TaskComponent/components/Sprint/components/Actions.vue')
            if(this.isOrder)
                return () => import('@apps/Orders/components/OrdersList/Actions.vue')
            if(this.isMeeting)
                return () => import('@apps/vue2MeetingComponent/components/CardActions.vue')
            if(this.isAnalytics)
                return () => import('@apps/vue2TaskComponent/components/Analytics/Actions.vue')
            if(this.isContractors)
                return () => import('@apps/Contractors/components/Actions.vue')
            if(this.isLeads)
                return () => import('@apps/Contractors/components/Actions.vue')
            if(this.isModeration)
                return () => import('@apps/Moderation/components/Actions.vue')
            if(this.isRoles)
                return () => import('@apps/Directories/Team/components/Permissions/RoleActionsDropdown.vue') 
            if(this.isConsolidation)
                return () => import('@apps/Consolidation/components/Actions/Consolidation/index.vue')
            /*if(this.isAccountingReports)
                return () => import('@apps/AccountingReports/components/Actions/Actions.vue')*/
            return null
        }
    }
}
</script>