<template>
    <div>
        <component :is="baseDrawerAsync" v-if="$route.query.help" />
        <component :is="newsDrawerAsync" v-if="$route.query.newList" />
        <component :is="newsItemDrawerAsync" v-if="$route.query.newsItem" />
    </div>
</template>

<script>
export default {
    name: 'HelpInit',
    data() {
        return {
            baseDrawerAsync: () => import('./components/BaseDrawer/index.vue'),
            newsDrawerAsync: () => import('./components/NewsDrawer/index.vue'),
            newsItemDrawerAsync: () => import('./components/NewsItemDrawer/index.vue')
        }
    }
}
</script>
