<template>
    <div>
        <component :is="contractDrawerDriverAsync" v-if="$route.query.contract" />
        <AddDrawer />
    </div>
</template>

<script>
export default {
    name: 'DealsInit',
    components: {
        AddDrawer: () => import('./AddDrawer/index.vue'),
    },
    data() {
        return {
            contractDrawerDriverAsync: null,
        }
    },
    watch: {
        '$route.query.contract': {
            immediate: true,
            handler(value) {
                if (value && !this.contractDrawerDriverAsync) {
                    this.contractDrawerDriverAsync = () => import('./components/ContractDrawerDriver.vue')
                }
            },
        },
    },
}
</script>
