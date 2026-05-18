import eventBus from '@/utils/eventBus'
export default {
    methods: {
        async getIDs(listItems) {
            const ids = listItems.map(item => {
                return item.id
            })
            return ids
        },
        async setActions(listItems) {
            let ids = await this.getIDs(listItems)
            if(listItems.length > 0) {
                try {
                    this.loading = true
                    const { data } = await this.$http.post('/risk_assessment/action_info/', ids)
                    if(data) {
                        listItems.forEach(item => {
                            Object.assign(item, data[item.id])
                        })
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.loading = false
                }
                return listItems
            } else {
                return []
            }
        },
        
        getInquiries() {
            this.getList()
        },
        async updateAssessmentInList(data) {
            const index = this.list.findIndex(f => f.id === data.id)
            if(index !== -1) {
                const new_data = await this.setActions([data])
                this.$set(this.list, index, new_data[0])
                eventBus.$emit('update_assessment_details', new_data[0].id)
            }
        },
    }
}