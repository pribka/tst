<template>
    <div class="org_employees font-semibold" @click="openOrganizationDrawer">
        {{ record.members_count }}
    </div>
</template>

<script>
export default {
    props: {
        record: {
            type: [Object, String],
            required: true
        }

    },
    methods: {
        openOrganizationDrawer() {
            const query = {
                organization_drawer: 'detail',
                organization_id: this.record.id
            }

            if (this.record?.parent_expand) {
                query.parent_id = this.record.parent_expand
            }

            this.$router.push({ query })
        }
    }
}
</script>

<style lang="scss" scoped>
.org_employees {
    cursor: pointer;
    transition: color 0.2s ease;
    &:hover {
        color: var(--blue);
    }
}
</style>
