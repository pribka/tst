export default {
    computed: {
        activeFilter() {
            return this.$store.state.filter.filterActive[this.name][this.filter.name]
        }
    },
    methods: {
        focus() {
            if (!this.activeFilter)
                this.$store.commit("filter/SET_ACTIVE_FILTERS",
                    { name: this.name, filterName: this.filter.name, value: true })
        }
    }
}