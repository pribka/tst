<script>
import monitor from "./store/index.js"
export default {
    render: () => null,
    created() {
        if (!this.$store.hasModule("monitor"))
            this.$store.registerModule("monitor", monitor)
    }
}
</script>