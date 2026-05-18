<template>
    <div>
        <TicketDrawerCreate />
        <TicketDrawerView />
    </div>
</template>

<script>
import mybases from "./store/index.js"
export default {
    components: {
        TicketDrawerCreate: () => import("./components/TicketDrawerCreate.vue"),
        TicketDrawerView: () => import("./components/TicketDrawerView.vue")
    },
    created() {
        if (!this.$store.hasModule("mybases"))
            this.$store.registerModule("mybases", mybases)
    }
}
</script>