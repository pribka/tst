<template>
    <a-table 
        :columns="columns"
        :loading="loading"
        :pagination="false"
        :row-key="record => record.id"
        :locale="{
            emptyText: $t('no_data')
        }"
        :data-source="list">
        <template 
            slot="currency" 
            slot-scope="text">
            <template v-if="text">
                {{ text.name }}
            </template>
        </template>
        <template 
            slot="actions" 
            slot-scope="text">
            <a-button 
                type="dashed"
                @click="getAct(text)">
                {{$t('reconciliation_act')}}
            </a-button>
        </template>
    </a-table>
</template>

<script>
export default {
    data() {
        return {
            loading: false,
            actLoading: {},
            page: 1,
            list: [],
            columns: [
                {
                    title: this.$t('name'),
                    dataIndex: 'name',
                    key: 'name'
                },
                {
                    title: this.$t('currency'),
                    dataIndex: 'currency',
                    key: 'currency',
                    scopedSlots: { customRender: 'currency' }
                },
                {
                    title: '',
                    dataIndex: 'id',
                    key: 'id',
                    scopedSlots: { customRender: 'actions' }
                }
            ]
        }
    },
    created() {
        this.getList()
    },
    methods: {
        async getAct(id) {
            try {
                this.loading = true
                const { data } = await this.$http.get(`/crm/contract/${id}/get_file/`, {
                    responseType: 'blob'
                })
                if(data) {
                    const url = window.URL.createObjectURL(new Blob([data]))
                    const link = document.createElement('a')
                    link.href = url
                    link.setAttribute('download', `${this.$t('reconciliation_act_from')} ${this.$moment().format('DD-MM-YYYY')}.zip`)
                    document.body.appendChild(link)
                    link.click()
                    link.remove()
                }
            } catch(e) {
                console.log(e)
                this.$message.error(this.$t('error_occurred'))
            } finally {
                this.loading = false
            }
        },
        async getList() {
            try {
                this.loading = true
                const { data } = await this.$http.get('/catalogs/contracts/', {
                    params: {
                        page: this.page
                    }
                })
                if(data)
                    this.list = data.results
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        }
    }
}
</script>
