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
import UniversalTable from '@/components/TableWidgets/UniversalTable'
export default {
    name: 'GroupTable',
    components: {
        UniversalTable
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
            if(query.viewGroup && Number(query.viewGroup) !== id || !query.viewGroup) {
                query.viewGroup = id
                this.$router.push({query})
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