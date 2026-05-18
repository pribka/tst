<template>
    <div>
        <div 
            v-if="text === 'online'" 
            class="online pl-2  flex items-center">
            <div class="blob mr-2"></div>
            {{ $t('meeting.online') }} 
        </div>
        <a-tag 
            v-else 
            block
            size="large"
            :color="statusColor">{{ statusText }}</a-tag>
    </div>
</template>

<script>
export default {
    props: {
        text: {
            type: [Object, Boolean, String, Array]
        },
        record: {
            type: Object,
            required: true
        },
        model: {
            type: String
        },
        tableType: {
            type: String
        },
        column: {
            type: Object
        },
        openHandler: {
            type: Function,
            default: () => {}
        }    
    },
    computed: {
        isContractors() {
            return this.tableType === 'contractors'
        },
        isConsolidation() {
            return this.tableType === 'consolidation'
        },
        isLeads() {
            return this.tableType === 'leads'
        },
        isMyBases() {
            return this.tableType === 'tickets'
        },
        isTask() {
            return this.model === 'tasks.TaskModel' || this.tableType === 'tasks'
        },
        isMeeting() {
            return this.model === 'meetings.PlannedMeetingModel'
        },
        isSprint() {
            return this.model === 'tasks.TaskSprintModel'
        },
        isWorkgroupAndProject() {
            return this.model === 'workgroups.WorkgroupModel'
        },
        isProjectStatusField() {
            return this.column.key === 'finished'
        },
        isStatusField() {
            return this.column.key === 'status'
        },
        isAccountingReports() {
            return this.tableType === 'accounting_reports'
        },
        statusText() {
            if(this.isMyBases && this.column.key === 'status')
                return this.record.status.name
            if(this.isWorkgroupAndProject && this.isProjectStatusField)
                return this.record.finished ? this.$t('table.ended') : this.$t('table.activity') 
            if(this.isTask && this.isStatusField)
                return this.text.name
            if(this.isSprint && this.isStatusField)
                return this.getSprintStatus.name
            if(this.isMeeting)
                return this.getMeetingStatus.name
            if(this.isContractors)
                return this.text.value
            if(this.isLeads)
                return this.text.value
            if(this.isConsolidation)
                return this.text.name
            if(this.isAccountingReports)
                return this.text.name

            return this.text?.name
        },
        statusColor() {
            if(this.isMyBases)
                return this.record.status.color
            if(this.isWorkgroupAndProject && this.isProjectStatusField)
                return this.record.finished ? 'green' : 'blue'
            if(this.isTask && this.isStatusField)
                return this.text.color === 'default' ? '' : this.text.color
            if(this.isSprint && this.isStatusField)
                return this.getSprintStatus.color
            if(this.isMeeting)
                return this.getMeetingStatus.color
            if(this.isContractors)
                return this.text.color
            if(this.isLeads)
                return this.text.color
            if(this.isConsolidation)
                return this.text.color
            if(this.isAccountingReports)
                return this.text.color

            return this.text?.color
        },
        getSprintStatus() {
            /*eslint-disable */
            switch (this.record.status) {
                case 'new': return { name: this.$t('table.in_new'), color: "blue" }
                case 'in_process': return { name: this.$t('table.in_process'), color: "purple" };
                case 'completed': return { name: this.$t('table.ended'), color: "green" };
            }
            return { name: "Без статуса", color: "default" }
            /*eslint-enable */
        },
        getMeetingStatus() {
            /*eslint-disable */
            switch (this.text) {
                case 'new': return { name: this.$t("meeting.new"), color: "blue" }
                case 'Новая': return { name: this.$t("meeting.new"), color: "default" };
                case 'ended': return { name: this.$t("meeting.ended"), color: "green" };
            }
            return { name: "Без статуса", color: "default" }
            /*eslint-enable */
        }
    }
}
</script>

<style lang="scss" scoped>
@keyframes pulse-red {
  0% {
    transform: scale(0.95);
    box-shadow: 0 0 0 0 rgba(255, 82, 82, 0.7);
  }
  
  70% {
    transform: scale(1);
    box-shadow: 0 0 0 10px rgba(255, 82, 82, 0);
  }
  
  100% {
    transform: scale(0.95);
    box-shadow: 0 0 0 0 rgba(255, 82, 82, 0);
  }
}
.online{
    color: rgba(255, 82, 82, 1);
    .blob{
        border-radius: 50%;
        height: 8px;
        width: 8px;
        transform: scale(1);
        background: rgba(255, 82, 82, 1);
        box-shadow: 0 0 0 0 rgba(255, 82, 82, 1);
        animation: pulse-red 2s infinite;
    }
}
</style>