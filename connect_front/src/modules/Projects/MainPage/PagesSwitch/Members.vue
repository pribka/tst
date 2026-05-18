<template>
    <component 
        :is="componentWidget"
        class="h-full flex flex-col min-h-0"
        :actions="actions"
        :requestData="requestData"
        :isFounder="isFounder"
        :id="id" />
</template>

<script>
export default{
    name: 'Participants',
    props: {
        isFounder: {
            type: Boolean,
            required: true
        },
        isStudent: {
            type: Boolean,
            required: true
        },
        id: {
            type: [String, Number],
            default: null
        },
        updatePartisipants: {
            type: Function,
            default: () => {}
        },
        actions: {
            type: Object,
            default: () => null
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        componentWidget() {
            if (this.isMobile) {
                return () => import('../../components/MemberList.vue')
            }
            return () => import('../../components/MemberTable.vue')
        }
    }
}
</script>