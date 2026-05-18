<template>
    <component
        :is="viewComponent"
        :initPageName="initPageName"
        :initPageModel="initPageModel"
        :openUserModal="openUserModal"
        :dateRange="dateRange" />
</template>

<script>
export default {
    props: {
        initPageName: {
            type: String,
            default: ""
        },
        initPageModel: {
            type: String,
            default: ""
        },
        openUserModal: {
            type: Function,
            default: () => {}
        },
        dateRange: {
            type: Array,
            default: () => []
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        viewComponent() {
            if (this.isMobile)
                return () => import('./indexMobile.vue')
            return () => import('./List.vue')
        }
    }
}
</script>
