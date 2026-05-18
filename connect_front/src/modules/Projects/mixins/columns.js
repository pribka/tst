export default {
    created() {
        this.getTableColumns()
    },
    methods: {
        async getTableColumns() {
            try {
                await this.$store.dispatch('projects/getTableColumns', {
                    listProject: this.listProject
                })
            } catch(e) {
                console.log(e)
            }
        }
    }
}