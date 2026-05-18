<template>
    <div class="flex-grow flex">
        <UniversalTable 
            :model="pageModel"
            :pageName="page_name"
            :tableType="tableType"
            :openHandler="openHandler"
            :endpoint="endpoint"        
            :showChildren="true"/>
    </div>
</template>

<script>
export default {
    name: 'GroupTable',
    components: {
        UniversalTable: () => import('@/components/TableWidgets/UniversalTable')
    },
    props: {
        tableType: {
            type: String,
            default: 'groups'
        },
        listProject: {
            type: Boolean,
            default: true
        },
        pageModel: {
            type: String,
            default: 'workgroups.WorkgroupModel'
        },
        page_name: {
            type: String,
            default: 'page_list_project_workgroups.WorkgroupModel'
        },
    },
    computed: {
        endpoint() {
            return `/work_groups/workgroups/?is_project=${this.listProject ? 1 : 0}`
        },
    },
    methods: {
        openHandler(id) {
            const query = Object.assign({}, this.$route.query)
            if(query.viewProject !== id) {
                query.viewProject = id
                this.$router.push({ query })
            } else {
                delete query.viewProject
                this.$router.replace({ query })
                    .then(() => {
                        query.viewProject = id
                        this.$router.replace({ query })
                    })
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.group_desc,
.group_name{
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    transition: color 0.3s;
    word-break: break-word;
}
</style>