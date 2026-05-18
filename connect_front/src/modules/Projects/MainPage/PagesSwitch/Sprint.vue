<template>
    <div :class="!isMobile && 'h-full'">
        <Sprints 
            :filters="filters" 
            :showCreateButton="showCreateButton"
            inject
            :excludeCol="['project']"
            class="h-full flex flex-col"
            :injectFormParams="injectFormParams"
            :excludeFields="excludeFields"
            :pageName="pageName" />
    </div>
</template>

<script>
import { mapGetters } from 'vuex'
export default {
    components: {
        Sprints: () => import('@apps/vue2TaskComponent/components/Sprint/Sprints.vue')
    },
    props: {
        id: {
            type: [String, Number],
            required: true
        },
        actions: {
            type: Object,
            default: () => null
        }
    },
    computed: {
        ...mapGetters({
            requestData : "projects/info"
        }),
        isMobile() { 
            return this.$store.state.isMobile
        },
        pageName() {
            return `list_sprint_groups_and_project_${this.id}`
        }
    },
    data() {
        return {
            filters: {},
            excludeFields: ['status'],
            showCreateButton: false,
            injectFormParams: {}
        }
    },
    created() {
        if(this.actions?.add_sprint?.availability && !this.requestData?.finished)
            this.showCreateButton = true

        this.filters = { 
            projects: this.id
        }
        this.injectFormParams = {
            projects: [this.requestData]
        }
        this.excludeFields.push('project')
    }
}
</script>