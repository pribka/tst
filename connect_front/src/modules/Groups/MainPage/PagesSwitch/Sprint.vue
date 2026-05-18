<template>
    <div class="wrg_sprint flex-grow flex flex-col">
        <ListSprint 
            :filters="formParams" 
            :showCreateButton="showCreateButton"
            :pageName="pageName" />
        
    </div>
</template>

<script>
import { mapGetters } from 'vuex'
export default {
    components: {
        ListSprint: () => import('@apps/vue2TaskComponent/components/Sprint/List.vue')
    },
    props: {
        id: {
            type: [String, Number],
            required: true
        },
        is_project: {
            type: Boolean,
            default: false
        },
        actions: {
            type: Object,
            default: () => null
        }
    },
    computed: {
        ...mapGetters({
            requestData : "workgroups/info"
        }),
        pageName() {
            return `list_sprint_groups_and_project_${this.id}`
        }
    },
    data() {
        return {
            formParams: {},
            excludeFields: ['status'],
            filters: "",
            showCreateButton: false
        }
    },
    created() {
        if(this.actions?.add_sprint) {
            this.showCreateButton = true
        }

        if(this.requestData.is_project) {
            this.formParams = { 
                project: this.id
             
                // dead_line: this.requestData.dead_line
            }
            this.excludeFields.push('project')
        } else {
            this.formParams = {  workgroup: this.id}
            this.excludeFields.push('workgroup')
        }
    }
}
</script>

<style lang="scss">
.wrg_sprint{
    .sprint_wrapper{
        padding: 0;
    }
    height: 100%;
    position: relative;
}
</style>