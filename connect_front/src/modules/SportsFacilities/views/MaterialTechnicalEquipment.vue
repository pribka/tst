<template>
    <div>
        <a-table 
            :columns="columns" 
            :data-source="data" 
            bordered
            :pagination="false">

        </a-table>
        <a-button type="primary" size="large" block class="add_btn">
            Добавить оборудование
        </a-button>
    </div>
</template>

<script>
export default {
    data() {
        return {
            data: [
                {
                    per: 'Турник',
                    price: 1000,
                    count: 38,
                    price2: 50,
                    date: '20.08.2024',
                    gar: '3 года',
                    sost: 'Отличное'
                },
                {
                    per: 'Турник',
                    price: 1000,
                    count: 38,
                    price2: 50,
                    date: '20.08.2024',
                    gar: '3 года',
                    sost: 'Отличное'
                },
                {
                    per: 'Турник',
                    price: 1000,
                    count: 38,
                    price2: 50,
                    date: '20.08.2024',
                    gar: '3 года',
                    sost: 'Отличное'
                },
                {
                    per: 'Турник',
                    price: 1000,
                    count: 38,
                    price2: 50,
                    date: '20.08.2024',
                    gar: '3 года',
                    sost: 'Отличное'
                }
            ],
            columns: [
                {
                    title: this.$t('sports.equipmentList'),
                    dataIndex: 'per',
                    key: 'per',
                },
                {
                    title: this.$t('sports.cost'),
                    dataIndex: 'price',
                    key: 'price',
                },
                {
                    title: this.$t('sports.quantity'),
                    dataIndex: 'count',
                    key: 'count',
                },
                {
                    title: this.$t('sports.unitPrice'),
                    dataIndex: 'price2',
                    key: 'price2',
                },
                {
                    title: this.$t('sports.purchaseDate'),
                    dataIndex: 'date',
                    key: 'date',
                },
                {
                    title: this.$t('sports.serviceLife'),
                    dataIndex: 'gar',
                    key: 'gar',
                },
                {
                    title: this.$t('sports.condition'),
                    dataIndex: 'sost',
                    key: 'sost',
                },
            ]
        }
    }
}
</script>

<style lang="scss" scoped>
.add_btn{
    border-top-left-radius: 0px;
    border-top-right-radius: 0px;
}
</style>