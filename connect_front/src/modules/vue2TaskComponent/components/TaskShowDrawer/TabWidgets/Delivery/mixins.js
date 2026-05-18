import { priceFormatter } from '@/utils'
export default {
    data() {
        return {
            fullLoading: {},
            visible: false,
            visibleInfo: false,
            infoData: null,
            incomplete: null,
            searchText: '',
            searchInput: null
        }
    },
    methods: {
        closeInfoModal() {
            this.visibleInfo = false
        },
        closeFormModal() {
            this.visible = false
        },
        openInfo(record) {
            this.infoData = record
            this.visibleInfo = true
        },
        handleSearch(selectedKeys, confirm, dataIndex) {
            confirm()
            this.searchText = selectedKeys[0]
            this.searchedColumn = dataIndex
        },
        handleReset(clearFilters) {
            clearFilters()
            this.searchText = ''
        },
        afterCloseInfo() {
            this.infoData = null
        },
        afterClose() {
            this.form = {
                quantity_success: null,
                comment: '',
                attachments: []
            }
            this.incomplete = null
        },
        price(price) {
            return priceFormatter(price)
        },
        updateProductList(data) {
            const value = JSON.parse(JSON.stringify(this.productList))
            const index = value.findIndex(f => f.id === data.id)
            if(index !== -1) {
                this.$set(value, index, data)
                this.$store.commit('task/TASK_CHANGE_FIELD', {
                    key: 'delivery_table',
                    value,
                    task: this.task
                })
            }
        },
        async fullShipment(record) {
            try {
                this.$set(this.fullLoading, record.id, true)
                const {data} = await this.$http.patch(`/tasks/delivery/${record.id}/`, {
                    quantity_success: record.quantity,
                    comment: ''
                })
                this.updateProductList(data)
                this.$message.success(this.$t('task.delivery.product_succes_delivery'))
            } catch(e) {
                console.log(e)
                this.$message.error(this.$t('task.error'))
            } finally {
                this.$delete(this.fullLoading, record.id)
            }
        },
        incompleteModal(record) {
            this.incomplete = {
                ...record,
                quantity_valid: Number(record.quantity)
            }
            this.visible = true
        }
    }
}