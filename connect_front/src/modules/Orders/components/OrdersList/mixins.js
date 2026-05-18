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
        updateProduct(data) {
            const value = JSON.parse(JSON.stringify(this.productList))
            const index = value.findIndex(f => f.id === data.id)
            if(index !== -1) {
                // this.$set(value, index, data)
                // this.$store.commit('task/TASK_CHANGE_FIELD', {
                //     key: 'delivery_table',
                //     value,
                //     task: this.task
                // })
                this.updateProductList(index, data)
            }
        },
        async fullShipment(record) {
            try {
                this.$set(this.fullLoading, record.id, true)
                const {data} = await this.$http.post(`/crm/orders/goods/${record.id}/delivery/`, {
                    quantity_success: record.quantity,
                    delivery_comment: ''
                })
                this.updateProduct(data)
                this.$message.success('Товар успешно отгружен')
            } catch(e) {
                console.log(e)
                this.$message.error('Ошибка')
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