export default {
    data() {
        return {
            takeLoader: false
        }
    },
    methods: {
        mobileTakeTask(task) {
            this.$confirm({
                title: this.$t('task.handler.confirmTakeTask'),
                closable: true,
                maskClosable: true,
                cancelText: this.$t('task.handler.cancel'),
                okText: this.$t('task.handler.ok'),
                zIndex: 99999,
                onOk: async () => {
                    try {
                        this.takeLoader = true
                        await this.$store.dispatch('task/takeAuctionTask', { task })
                        this.$message.success(this.$t('task.handler.success'))
                    } catch(error) {
                        this.$message.error(this.$t('task.handler.error'))
                        console.error(error)
                    } finally {
                        this.takeLoader = false
                    }
                }
            })
        },
        async takeTask(task) {
            try {
                this.takeLoader = true
                await this.$store.dispatch('task/takeAuctionTask', { task })
                this.$message.success(this.$t('task.handler.success'))
            } catch(error) {
                this.$message.error(this.$t('task.handler.error'))
                console.error(error)
            } finally {
                this.takeLoader = false
            }
        }
    }
}