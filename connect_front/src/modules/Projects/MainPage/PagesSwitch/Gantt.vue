<template>
    <Gant 
        :related_object="id" 
        inject
        onlyTask
        :forceStartDate="requestData.date_start_plan"
        :forceEndDate="requestData.dead_line"
        :formParams="formParams"
        :useEdit="addEventCheck"
        pageModel="tasks.TaskModel"
        :page_name="page_name" />
</template>

<script>
import { mapGetters } from 'vuex'
export default {
    components: {
        Gant: () => import('@apps/UIModules/Gant/index.vue')
    },
    props: {
        id: {
            type: [String, Number],
            required: true
        },
        isStudent: {
            type: Boolean,
            required: true
        },
        isFounder: {
            type: Boolean,
            required: true
        }
    },
    computed: {
        ...mapGetters({
            requestData : "projects/info"
        }),
        page_name() {
            return `gantt.groups_and_project_${this.id}`
        },
        addEventCheck() {
            return this.isStudent || this.isFounder ? true : false
        }
    },
    created() {
        this.formParams = { 
            project: {
                name: this.requestData.name, 
                id: this.id,
                workgroup_logo: this.requestData.workgroup_logo?.is_image ? this.requestData.workgroup_logo : null,
                date_start_plan: this.requestData.date_start_plan,
                dead_line: this.requestData.dead_line
            }
        }
    }
}
</script>