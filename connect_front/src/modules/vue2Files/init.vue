<script>
import store from "./store/index"

export default {
    render: () => null,
    created() {
        if (!this.$store.hasModule("files"))
            this.$store.registerModule("files", store);
    }
}
</script>