<template>
    <component
        :is="viewComponent"
        v-bind="componentBinds"
        v-on="$listeners" />
</template>

<script>
export default {
    inheritAttrs: false,
    props: {
        value: { type: [Object, String], default: null },
        selectItem: { type: Function, default: () => {} }
    },
    computed: {
        componentBinds() {
            return {
                ...this.$attrs,
                ...this.$props,
                endpoint: '/wiki/chapters/',
                title: this.$t('support.selectSubsection'),
                placeholder: this.$t('support.selectSubsection')
            }
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        viewComponent() {
            if (this.isMobile) {
                return () => import('./WikiSelectWidget/Mobile.vue')
            }
            return () => import('./WikiSelectWidget/Desktop.vue')
        }
    }
}
</script>
