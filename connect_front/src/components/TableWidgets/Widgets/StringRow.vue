<template>
    <div
        :class="{
            'cursor-pointer': isCursorPointer,
            'is_hover': isBlueLink,
            'text-center': isTextCenter,
        }" 
        @click="clickHandler(clickHandlerParam)">
        {{ cellText }}
    </div>
</template>

<script>
export default {
    props: {
        text: {
            type: [String, Number, Boolean, Object, Array]
        },
        record: {
            type: Object
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
        isCursorPointer() {
            return this.isCounterField || 
                this.isMeetingName || 
                this.isConfig1CField ||
                this.isSprintName ||
                this.isConsolidation
        },
        isBlueLink() {
            return this.isMeetingName || this.isConfig1CField || this.isSprintName || this.isConsolidation
        },
        isTextCenter() {
            return this.column.textAlign === 'center'
        },
        isSprint() {
            return this.tableType === 'sprints'
        },
        isConsolidation() {
            return (this.tableType === 'consolidation') || (this.tableType === 'consolidation_templates')
        },
        isSprintName() {
            return this.isSprint && this.column.key === 'name'
        },        
        isConfig1CField() {
            return this.column.key === 'config_1c'
        },
        isMyBases() {
            return this.tableType === 'tickets'
        },
        isModeration() {
            return this.tableType === 'moderation'
        },
        isWorkgroupAndProject() {
            return this.model === 'workgroups.WorkgroupModel'
        },
        isTask() {
            return this.model === 'tasks.TaskModel' || this.tableType === 'tasks'
        },   
        isMeeting() {
            return this.tableType === 'meetings'
        },
        isMeetingName() {
            return this.isMeeting && this.isNameField
        },             
        isOrder() {
            return this.model === 'crm.GoodsOrderModel'
        },
        isPublicOrPrivateField() {
            return this.column.key === 'public_or_private'
        },
        isCounterField() {
            return this.column.key === 'counter'
        },
        isNameField() {
            return this.column.key === 'name'
        },
        isRoles() {
            return this.tableType === 'roles'
        },
        isAccountingReports() {
            return this.tableType === 'accounting_reports'
        },
        cellText() {
            if(this.column.key === 'excluded') {
                return this.text ? this.$t('task.returned') : ''
            }
            if(this.column.key === 'is_scrum_master') {
                return this.text ? this.$t('sprint.scrum_master') : this.$t('sprint.sprint_member')
            }
            if(this.isMyBases && this.isConfig1CField)
                return this.text?.name || 'Не выбрана'
            if(this.isTask) 
                if(this.column.key === 'counter')
                    return this.text
                else if(this.column.key === 'contractor')
                    return this.text?.name || '---'
                else if(this.column.key === 'contractor_name')
                    return this.text?.name || '---'

            if(this.isConsolidation) {
                if(this.record?.is_scheduled)
                    return `[ШАБЛОН] ${this.text?.name ? this.text.name : this.record.name}`
                else
                    return this.text?.name ? this.text.name : this.record.name
            }

            if(this.isWorkgroupAndProject)
                if(this.isPublicOrPrivateField)
                    return this.text ? 'Закрытый' : 'Открытый'
            
            if(this.isOrder) 
                if(this.column.key === 'orders_table_info')
                    return this.text || '-'
                else if(this.column.key === 'warehouse')
                    return this.record?.warehouse?.name
                else if(this.column.key === 'contractor')
                    return this.record?.customer_contract?.customer_card?.name || this.text?.name || ''
                else if(this.column.key === 'contractor_member')
                    return this.record?.customer_contract ? '' : this.text?.name || ''
                else if(this.column.key === 'contract')
                    return this.record?.customer_contract
                        ? this.record.customer_contract.number || this.record.customer_contract.string_view || ''
                        : this.text?.name || ''
                else if([
                    'warehouse', 
                    'pay_type',
                    'operation_type'
                ].includes(this.column.key))
                    return this.text?.name || ''
            
            if(this.isAccountingReports)
                return this.text.name

            return this.text || ''
        },
        clickHandler() {
            if((this.isTask && this.isCounterField) ||
                (this.isMeeting && this.isNameField) ||
                (this.isMyBases && this.isConfig1CField) ||
                (this.isSprintName) ||
                (this.isConsolidation)
            )
                return this.openHandler        
            return () => {}
        },
        clickHandlerParam() {
            if((this.isTask && this.isCounterField) ||
                (this.isMeeting && this.isNameField) ||
                (this.isMyBases && this.isConfig1CField) ||
                (this.isRoles && this.isNameField)
            )
                return this.record
            else if (this.isModeration) {
                return this.record
            }
            else if(this.isSprintName ||
                this.isConsolidation)
                return this.record.id
            return null
        }
    }
}
</script>

<style lang="scss" scoped>
.is_hover{
    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    &:hover{
        color: var(--blue);
    }
}
</style>
