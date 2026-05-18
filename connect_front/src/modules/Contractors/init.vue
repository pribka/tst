<script>
import contractors from './store/index.js'
export default {
    render: () => null,
    created() {
        if (!this.$store.hasModule("contractors"))
            this.$store.registerModule("contractors", contractors)
    }
}
</script>