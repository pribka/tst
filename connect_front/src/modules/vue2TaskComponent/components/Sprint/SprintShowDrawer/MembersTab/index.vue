<template>
    <div>
        <component
            :is="membersListWidget"
            ref="membersTableRef"
            :sprint="sprint"
            :getDataHook="getDataHook"
            model="12" 
            pageName="12"    
            :onRowClicked="onRowClicked" />

        <p class="mb-2 mt-6 text-base">
            {{ $t('sprint.labor_costs_breakdown') }}
        </p>
        <UserFilter 
            v-if="userData.results.length" 
            :userData="userData"
            v-model="selectedUser"
            @change="reloadLaborCostsTable"
            class="mb-3" />

        <component 
            ref="userTasksTableRef"
            :is="taskListWidget"
            :sprint="sprint"
            :model="model"
            :queryParams="queryParams"
            :pageName="'45234234'" />
    </div>
</template>

<script>
export default {
    components: {
        UserFilter: () => import('./UserFilter.vue'),
        Table: () => import('./Table.vue')
    },
    props: {
        sprint: {
            type: Object,
            required: true
        },
        pageName: {
            type: String,
            default: ''
        },
        model: {
            type: String,
            default: ''
        }
    },
    computed: {
        membersListWidget() {
            if(this.isMobile)
                return () => import('./MembersCardList.vue')
            return () => import('./Table.vue')
        },
        taskListWidget() {
            if(this.isMobile)
                return () => import('./LaborCostsCardList.vue')
            return () => import('./TaskTable.vue')
        },
        queryParams() {
            const params = {
                display: 'only_time_tracking',
            }
            if (this.selectedUser && this.selectedUser !== 'all') {
                params.user = this.selectedUser
            }
            return params
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    data() {
        return {
            selectedUser: '',
            userData: { 
                results: [], 
                count: 0 
            },
        }
    },
    methods: {

        getDataHook(data) {
            if (data) {
                this.userData.results.splice(0) 
                this.userData.results.push(...data.results)
                this.userData.count = data.count
            }
        },
        onRowClicked(data) {
            const userId = data?.data?.user?.id
            this.selectedUser = userId || null
            if (userId) {
                this.reloadLaborCostsTable()
            }
        },
        reloadLaborCostsTable() {
            this.$refs.userTasksTableRef.reload()
        },
    }
}
</script>
