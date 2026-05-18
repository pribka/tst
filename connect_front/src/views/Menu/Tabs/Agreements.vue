<template>
    <div>
        <a-table 
            :columns="columns"
            :loading="loading"
            :pagination="false"
            :row-key="record => record.id"
            :locale="{
                emptyText: 'Нет данных'
            }"
            :data-source="list">
            <template 
                slot="currency" 
                slot-scope="text">
                <template v-if="text">
                    {{ text.name }}
                </template>
            </template>
        </a-table>
    </div>
</template>

<script>
export default {
    data() {
        return {
            loading: false,
            page: 1,
            list: [],
            columns: [
                {
                    title: 'Название',
                    dataIndex: 'name',
                    key: 'name'
                },
                {
                    title: 'Валюта',
                    dataIndex: 'currency',
                    key: 'currency',
                    scopedSlots: { customRender: 'currency' }
                }
            ]
        }
    },
    created() {
        this.getList()
    },
    methods: {
        async getList() {
            try {
                this.loading = true
                const { data } = await await this.$http.get('/catalogs/contracts/', {
                    params: {
                        page: this.page
                    }
                })
                if(data) {
                    this.list = data.results
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        }
    }
}
</script>