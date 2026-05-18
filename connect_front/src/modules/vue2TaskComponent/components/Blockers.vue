
<template>
    <Tags
        :useAction="canEdit"
        useSelect
        :noDataText="$t('task.no_blockers')"
        :model="model"
        uniqueSelectOptions
        :selectMinWidth="150"
        workplanUpdate
        :selectOptions="options"
        :selectPlaceholder="$t('task.choose')"
        :related_object="task.id"
        :contractor="task.organization.id" />
</template>

<script>
export default {
    components: {
        Tags: () => import('@apps/UIModules/Tags.vue')
    },
    props: {
        task: {
            type: Object,
            require: true
        },
        workplanUpdate: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        canEdit() {
            const actions = this.$store.state.task?.taskActions?.task?.[this.task.id]?.actions
            return actions?.update_tags?.availability
        }
    },
    data() {
        return {
            model: 'tasks.TaskModel',
            options: [
                { 
                    value: "dostup",        
                    label: this.$t('task.blocker_access'),        
                    color: "#FF5C5C" 
                },
                { 
                    value: "oshibka",       
                    label: this.$t('task.blocker_error'),        
                    color: "#FF5C5C" 
                },
                { 
                    value: "zapret",        
                    label: this.$t('task.blocker_prohibition'),        
                    color: "#FF5C5C" 
                },
                { 
                    value: "netdannyh",     
                    label: this.$t('task.blocker_no_data'),     
                    color: "#FF9A01" 
                },
                { 
                    value: "sboi",          
                    label: this.$t('task.blocker_failure'),          
                    color: "#FF5C5C" 
                },
                { 
                    value: "ozhidanie",     
                    label: this.$t('task.blocker_waiting'),      
                    color: "#FFD175" 
                },
                { 
                    value: "vopros",        
                    label: this.$t('task.blocker_question'),        
                    color: "#FFD175" 
                },
                { 
                    value: "risk",          
                    label: this.$t('task.blocker_risk'),          
                    color: "#FFD175" 
                },
                { 
                    value: "proverka",      
                    label: this.$t('task.blocker_check'),      
                    color: "#52943C" 
                },
                { 
                    value: "soglasovanie",  
                    label: this.$t('task.blocker_approval'),  
                    color: "#52943C"
                }
            ],
        }
    },
}
</script>