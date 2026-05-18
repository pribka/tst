import { errorHandler } from '@/utils/index.js'
export default {
    methods: {
        deleteObjective(objectiveID) {
            return new Promise((resolve, reject) => {
                this.$confirm({
                    title: this.$t('okr.deleteObjectiveConfirm'),
                    okText: this.$t('okr.delete'),
                    okType: 'danger',
                    cancelText: this.$t('okr.cancel'),
                    onOk: async () => {
                        try {
                            await this.$http.post('/table_actions/update_is_active/', {
                                id: objectiveID,
                                is_active: false
                            });
                            this.$message.success(this.$t('okr.objectiveDeleted'))
                            resolve();
                        } catch (error) {
                            errorHandler({error})
                            reject(e)
                        }
                    }
                })
            })
        }
    }
}