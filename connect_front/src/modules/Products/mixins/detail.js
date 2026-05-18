export default {
    methods: {
        saveHistory() {
            this.$store.commit('products/SAVE_HISTORY')
        },
        removeHistory(id) {
            this.$store.commit('products/REMOVE_HISTORY', id)
        }
    }
}