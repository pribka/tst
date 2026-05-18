<script>
import store from "./store/index"
export default {
    render: () => null,
    created() {
        if(!this.$store.hasModule('dashboard'))
            this.$store.registerModule("dashboard", store)
    }
}
</script>