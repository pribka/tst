<template>
    <Fragment>
        <component :is="ticketDrawerAsync" v-if="$route.query.ticketView" />
        <!--<component :is="clientDrawerAsync" v-if="$route.query.client" />-->
        <component :is="requestDrawerAsync" v-if="$route.query.requestView" />

        <!--<ClientForm />-->
        <TicketModal />
        <RequestForm />
    </Fragment>
</template>

<script>
import Fragment from '@apps/UIModules/Fragment.js'
import store from "./store/index"
export default {
    components: {
        //ClientForm: () => import('./components/ClientForm.vue'),
        TicketModal: () => import('./components/Tickets/ModalForm.vue'),
        Fragment,
        RequestForm: () => import('./components/Request/RequestForm.vue')
    },
    data() {
        return {
            ticketDrawerAsync: null,
            //clientDrawerAsync: null,
            requestDrawerAsync: null
        }
    },
    watch: {
        '$route.query.ticketView': {
            immediate: true,
            handler(v) {
                if (v && !this.ticketDrawerAsync)
                    this.ticketDrawerAsync = () => import(/* webpackPrefetch: true, webpackChunkName: "ticket-show-drawer" */ './components/Tickets/TicketDrawer/index.vue')
            }
        },
        /*'$route.query.client': {
            immediate: true,
            handler(v) {
                if (v && !this.clientDrawerAsync)
                    this.clientDrawerAsync = () => import('./components/ClientDrawer')
            }
        },*/
        '$route.query.requestView': {
            immediate: true,
            handler(v) {
                if (v && !this.requestDrawerAsync)
                    this.requestDrawerAsync = () => import('./components/Tickets/TicketDrawer/index.vue')
            }
        }
    },
    /*mounted() {
        const prefetch = () => import( './components/Tickets/TicketDrawer/index.vue')
        if ('requestIdleCallback' in window) window.requestIdleCallback(prefetch)
        else setTimeout(prefetch, 200)
    },*/

    created() {
        if(!this.$store.hasModule('tickets')) {
            this.$store.registerModule("tickets", store)
        }
    }
}
</script>