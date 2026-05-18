import eventBus from '@/utils/eventBus'
export default {
    methods: {
        async changeStatus(sprint) {
            try {
                if (this.allData?.[1]?.list?.length === 0) throw new Error()
                this.loadingBtn = true
                const status = sprint.status === "new" ? 'in_process' : 'completed'
                let { data } = await this.$http.put(`tasks/sprint/${sprint.id}/update_status/`,
                    { status }
                )
                if (this.sprint) this.sprint.status = status
                if (this.sprint) this.sprint.dead_line = data.dead_line
                if (this.activeItems) this.activeItems = status !== 'completed' ? true : false

                eventBus.$emit("sprint_update_table", this.sprint)
                this.$emit('change')
            }
            catch (error) {
                console.log(error)
                this.$message.error(`${this.$t('task.sprint_error')}: ${error}`)
            }
            finally {
                this.loadingBtn = false
            }
        },
        getTimeInterval(timeInterval) {
            /*eslint-disable */
            switch (timeInterval) {
                case 'week': return this.$t('task.sprint_week');
                case 'two_week': return this.$t('task.sprint_two_weeks');
                case 'month': return this.$t('task.sprint_month');
            }
            /*eslint-enable */
        },
        getStatus(status) {
            /*eslint-disable */
            switch (status) {
                case 'new': return { name: this.$t('task.sprint_new'), color: "blue" }
                case 'in_process': return { name: this.$t('task.sprint_in_process'), color: "purple" };
                case 'completed': return { name: this.$t('task.sprint_completed'), color: "green" };
            }
            /*eslint-enable */
        }
    },

}