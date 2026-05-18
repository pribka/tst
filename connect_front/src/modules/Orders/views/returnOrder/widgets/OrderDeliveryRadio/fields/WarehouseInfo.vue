<template>
    <div class="warehouse_del">
        <h4 v-if="field.name">
            {{ field.name }}
        </h4>
        <div class="warehouse_list">
            <div 
                v-if="loading" 
                class="loader">
                <a-spin size="small" />
            </div>
            <template v-else>
                <div 
                    v-for="item in list" 
                    :key="item.id" 
                    class="item">
                    <div class="name">
                        {{ item.name }}
                    </div>
                    <div class="address">
                        {{ item.address }}
                    </div>
                    <div 
                        v-if="item.manager" 
                        class="manager info_item">
                        <div class="label">
                            Менеджер:
                        </div>
                        <div class="val">
                            {{ item.manager.full_name }}
                        </div>
                    </div>
                    <div 
                        v-if="item.phone" 
                        class="phone info_item">
                        <div class="label">
                            Телефон:
                        </div>
                        <div class="val">
                            <a :href="`tel:${item.phone}`">
                                {{ item.phone }}
                            </a>
                        </div>
                    </div>
                </div>
            </template>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        field: {
            type: Object,
            required: true
        },
        form: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            loading: false,
            list: []
        }
    },
    created() {
        this.warehouseList()
    },
    methods: {
        async warehouseList() {
            try {
                this.loading = true
                const { data } = await this.$http.get(this.field.apiPath)
                if(data?.length) {
                    this.list = data
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

<style lang="scss" scoped>
.warehouse_del{
    background: #eff2f5;
    border-radius: var(--borderRadius);
    padding: 20px;
    h4{
        font-weight: 600;
        font-size: 18px;
        margin-bottom: 15px;
        margin-top: 0px;
        line-height: 24px;
    }
    .warehouse_list{
        .info_item{
            &:not(:last-child){
                margin-bottom: 10px;
            }
            .label{
                font-weight: 300;
            }
        }
        .item{
            &:not(:last-child){
                margin-bottom: 10px;
                padding-bottom: 10px;
                border-bottom: 1px solid #e3e3e3;
            }
            .name{
                font-weight: 600;
            }
            .address{
                font-weight: 300;
                &:not(:last-child){
                    margin-bottom: 10px;
                }
            }
        }
    }
}
</style>