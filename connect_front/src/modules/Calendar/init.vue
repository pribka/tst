<template>
    <div>
        <AddEvent />
        <component :is="eventDrawerAsync" v-if="$route.query.event" />
    </div>
</template>

<script>
import store from './store/index'
export default {
    components: {
        AddEvent: () => import('./components/AddEvent.vue')
    },
    data() {
        return {
            eventDrawerAsync: null
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    watch: {
        '$route.query.event': {
            immediate: true,
            handler(v) {
                if (v && !this.eventDrawerAsync)
                    this.eventDrawerAsync = () => import('./components/EventDrawer')
            }
        }
    },
    created() {
        if(!this.$store.hasModule('calendar')) {
            this.$store.registerModule('calendar', store)
        }
    }
}
</script>
