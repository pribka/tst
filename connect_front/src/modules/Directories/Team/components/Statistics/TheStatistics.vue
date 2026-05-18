<template>
    <div>
        <ChartList
            :taskStatistics="taskStatistics"
            :visibleСharts="['all', 'completed']"
            adaptiveChart />
        <div class="font-semibold mb-2 mt-4">{{ $t('team.my_tasks') }}</div>
        <TaskTable 
            :organization="organization"/>
    </div>
</template>

<script>
export default {
    components: {
        ChartList: () => import('./ChartList.vue'),
        TaskTable: () => import('./TaskTable.vue')
    },
    props: {
        organization: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            taskStatistics: {},
        }
    },
    created() {
        this.getStatisticsByOrganization()
    },
    methods: {
        async getStatisticsByOrganization() {
            const params = {}            
            const url = `/users/my_organizations/${this.organization.id}/task_count/`
            try {
                const { data } = await this.$http.get(url, params)
                this.taskStatistics = data
            } catch(error) {
                console.error(error)
            }
        }
    }
}
</script>

<style lang="scss" scoped>

</style>
