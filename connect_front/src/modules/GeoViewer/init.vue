<script>
import geoviewer from "./store/index.js"
export default {
    render: () => null,
    created() {
        if (!this.$store.hasModule("geoviewer"))
            this.$store.registerModule("geoviewer", geoviewer)
    }
}
</script>