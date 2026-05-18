<template>
    <div>
        <CreateDrawer />
        <ViewDrawer />
    </div>
</template>

<script>
import store from "./store/index"
import CreateDrawer from './components/CreateDrawer'
import ViewDrawer from './components/ViewDrawer'
export default {
    components: {
        CreateDrawer,
        ViewDrawer
    },
    created() {
        if(!this.$store.hasModule('bprocess'))
            this.$store.registerModule("bprocess", store)
    }
}
</script>