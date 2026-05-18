<template>
    <InviteContactPerson :contactPerson="record" />
</template>

<script>
export default {
    components: {
        InviteContactPerson: () => import('@apps/HelpDesk/components/InviteContactPerson.vue')
    },
    props: {
        record: {
            type: Object,
            required: true
        },
    },
}
</script>