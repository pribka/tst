<template>
    <div ref="wrapRef" class="h-full flex flex-col">
        <UniversalTable
            :model="pageModel"
            ref="tableWidget"
            class="flex-grow"
            :params="{
                display: 'root'
            }"
            :colParams="{
                getPopupContainer: getPopupContainer
            }"
            :pageName="page_name"
            showChildren
            tableType="team_structure"
            endpoint="/users/my_organizations/" />
    </div>
</template>

<script>
export default {
    props: {
        page_name: {
            type: String,
            required: true
        },
        pageModel: {
            type: String,
            required: true
        }
    },
    components: {
        UniversalTable: () => import('@/components/TableWidgets/UniversalTable'),
    },
    methods: {
        getPopupContainer() {
            return this.$refs.wrapRef
        }
    }
}
</script>
