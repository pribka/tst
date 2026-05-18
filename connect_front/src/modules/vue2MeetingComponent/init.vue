<template>
    <div>
        <CreateDrawer />
        <CreateModal />
        <component :is="meetingDrawerAsync" v-if="$route.query.meeting" />
        <component :is="CallComponentAsync" v-if="CallComponentAsync" />
    </div>
</template>

<script>
import axios from '@/config/axios'
import store from './store/index'
import { restoreMeetingCalls } from './utils/call'
export default {
    name: 'MeetingInit',
    components: {
        CreateDrawer: () => import('./components/CreateDrawer'),
        CreateModal: () => import('./components/CreateModal')
    },
    data() {
        return {
            meetingDrawerAsync: null,
            CallComponentAsync: null,
            activeCallsLoaded: false
        }
    },
    watch: {
        '$route.query.meeting': {
            immediate: true,
            handler(v) {
                if (v && !this.meetingDrawerAsync)
                    this.meetingDrawerAsync = () => import('./components/MeetingShowDrawer/index.vue')
            }
        }
    },
    created() {
        if (!this.$store.hasModule('meeting'))
            this.$store.registerModule('meeting', store)

        this.CallComponentAsync = () => import('./Call/index.vue')
        this.loadActiveCalls()
    },
    methods: {
        async loadActiveCalls() {
            if (this.activeCallsLoaded)
                return

            this.activeCallsLoaded = true

            try {
                const { data } = await axios.get('/meetings/calls/active_calls/')
                restoreMeetingCalls(Array.isArray(data?.results) ? data.results : [])
            } catch (e) {
                this.activeCallsLoaded = false
            }
        }
    }
}
</script>
