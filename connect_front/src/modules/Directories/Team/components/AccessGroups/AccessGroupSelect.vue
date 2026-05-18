<template>
    <DSelect
        v-model="accessGroups"
        size="large"
        apiUrl="/contractor_permissions/access_groups/"
        class="w-full"
        multiple
        :maxTagCount="1"
        infinity
        :listObject="false"
        labelKey="name"
        @change="changeHandler"
        :default-active-first-option="false"
        :filter-option="false"
        :not-found-content="null" />
</template>


<script>
export default {
    components: {
        DSelect: () => import('@apps/DrawerSelect/Select.vue')
    },
    props: {
        user: {
            type: Object,
            required: true
        },
        organization: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            accessGroups: []
        }
    },
    created() {
        this.accessGroups = JSON.parse(JSON.stringify(this.user.access_groups.map(accessGroups => accessGroups.id)))
    },
    methods: {
        changeHandler(value) {
            const url = 'contractor_permissions/access_groups/set_user/'
            const payload = {
                user: this.user.id,
                contractor: this.organization.id,
                access_groups: value,
            }
            this.$http.post(url, payload)
                .catch(error => {
                    console.error(error)
                    this.$message.error(this.$t('team.failed_to_set_access_rights'))
                })
        },
    }
}
</script>