<template>
    <div class="page_block">
        <div class="mb-4">
            <a-form-model-item label="Характеристика объекта">
                <a-select v-model="filter" size="large" style="max-width: 500px;" class="w-full">
                    <a-select-option value="1">
                        Общая пропускная способность
                    </a-select-option>
                    <a-select-option value="2">
                        Общая площадь крытых помещений
                    </a-select-option>
                </a-select>
            </a-form-model-item>
        </div>
        <a-table 
            :columns="columns" 
            :data-source="data" 
            bordered
            class="data_table"
            :pagination="false">

        </a-table>
        <a-button type="primary" size="large" block class="add_btn">
            {{ $t('Add') }}
        </a-button>
        <div class="footer_actions">
            <a-button type="primary" ghost size="large" class="px-8">
                {{ $t('Save') }}
            </a-button>
        </div>
    </div>
</template>

<script>
export default {
    data() {
        return {
            filter: '1',
            data: [
                {
                    key: '1',
                    col1: 'Спортивный зал',
                    col2: '500 м²',
                    col3: 'Тренировки',
                    col4: '6 м',
                    col5: 'Паркет',
                    col6: '500 люкс',
                    col7: 'Хорошее',
                },
                {
                    key: '2',
                    col1: 'Тренажерный зал',
                    col2: '200 м²',
                    col3: 'Фитнес',
                    col4: '4 м',
                    col5: 'Ламинат',
                    col6: '300 люкс',
                    col7: 'Отличное',
                },
                {
                    key: '3',
                    col1: 'Бассейн',
                    col2: '1000 м²',
                    col3: 'Плавание',
                    col4: '5 м',
                    col5: 'Плитка',
                    col6: '400 люкс',
                    col7: 'Удовлетворительное',
                },
            ],
            columns: [
                {
                    title: 'Наименование помещения',
                    dataIndex: 'col1',
                    key: 'col1',
                },
                {
                    title: 'Площадь',
                    dataIndex: 'col2',
                    key: 'col2',
                },
                {
                    title: 'Назначение',
                    dataIndex: 'col3',
                    key: 'col3',
                },
                {
                    title: 'Высота',
                    dataIndex: 'col4',
                    key: 'col4',
                },
                {
                    title: 'Тип покрытия пола',
                    dataIndex: 'col5',
                    key: 'col5',
                },
                {
                    title: 'Освещенность (в люксах)',
                    dataIndex: 'col6',
                    key: 'col6',
                },
                {
                    title: 'Тех. состояние',
                    dataIndex: 'col7',
                    key: 'col7',
                },
            ]
        }
    }
}
</script>

<style lang="scss" scoped>
.add_btn{
    border-radius: 0px 0px 8px 8px;
}
.footer_actions{
    margin-top: 30px;
    padding-top: 30px;
    border-top: 1px solid #EBEBEB;
}
</style>