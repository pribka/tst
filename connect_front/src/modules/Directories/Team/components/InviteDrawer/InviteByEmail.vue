<template>
    <div>
        <GroupInvite
            ref="emailInvite"
            class="mb-4"
            :form="form"
            :orgId="organizationId" />
        <MassiveInvite
            ref="massiveInvite"
            :form="form"
            :orgId="organizationId" />
    </div>
</template>

<script>
export default {
    components: {
        MassiveInvite: () => import('./MassiveInvite.vue'),
        GroupInvite: () => import('./GroupInvite.vue')
    },
    props: {
        organizationId: {
            type: String,
            defalut: null
        },
        form: {
            type: Object,
            required: true
        }
    }
}
</script>