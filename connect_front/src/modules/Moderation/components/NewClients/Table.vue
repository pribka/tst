<template>
    <UniversalTable
        :model="pageModel"
        :pageName="pageName"
        :tableType="tableType"
        :endpoint="endpoint"/>
</template>

<script>
export default {
    components: {
        UniversalTable: () => import('@/components/TableWidgets/UniversalTable')
    },
    data() {
        return {
            pageModel: 'users.NewUserInfoModel',
            pageName: 'users.NewUserInfoModel',
            tableType: 'new-clients',
            endpoint: '/users/new_user_info/'
        }
    },
}
</script>