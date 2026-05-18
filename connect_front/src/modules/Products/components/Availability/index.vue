<template>
    <div
        class="availability"
        :ref="`availability_${item.id}`"
        :class="size">
        <a-popover
            v-if="item.available_count"
            v-model="visible"
            :getPopupContainer="getPopupContainer">
            <a-badge
                class="badge_availability"
                :status="status"
                :text="statusText"/>
            <div slot="content" class="">
                <a-spin
                    v-if="visible && loading"
                    size="small"/>
                <div
                    v-for="el, index in listData"
                    :key="index"
                    class="flex justify-between items-center my-1">
                    <span class="font-semibold">
                        {{el.warehouse.name}}:
                    </span>
                    <span class="ml-2">
                        {{el.quantity}}
                    </span>
                </div>
            </div>
        </a-popover>
        <a-badge
            v-else
            class="badge_availability"
            :status="status"
            :text="statusText"/>
    </div>
</template>

<script>
export default {
    props: {
        item: {
            type: Object,
            required: true
        },
        size: {
            type: String,
            default: 'small'
        }
    },
    data(){
        return {
            visible: false,
            listData: [],
            loading: false,
        }
    },
    computed: {
        status(){
            return this.item.is_available ? 'success' : 'error'
        },
        statusText(){
            var is_available_map = {
                '0':['В наличии','Нет в наличии'],
                '1':['Готов к сборке','Не готов к сборке'],
                '2':['Доступно','Не доступна'],
            };
            var good_type_code = is_available_map[this.item.goods_type.code];
            var true_result = good_type_code[0];
            var false_result = good_type_code[1];
            return this.item.is_available ?  true_result : false_result
        }
    },
    watch: {
        visible(val){
            if(val && this.listData.length === 0){

                this.getAvail()
            }
        }
    },
    methods:{
        getPopupContainer() {
            return this.$refs[`availability_${this.item.id}`]
        },
        async getAvail(){
            try{
                this.loading = true
                const {data} = await this.$http(`catalogs/goods/${this.item.id}/availability/`)
                this.listData = data.results
            }
            catch(e){
                console.error(e)
            }
            finally{
                this.loading = false
            }
        }
    }
}
</script>

<style lang="scss">
.availability{
    &.small{
        .ant-badge-status-text{
            font-size: 12px;
        }
    }
}
.badge_availability{
    .ant-badge-status-text{
        white-space: nowrap;
        -moz-user-select: none;
        -khtml-user-select: none;
        user-select: none;
        font-weight: 300;
    }
    .ant-badge-status-dot{
        margin-top: 2px;
    }
}
</style>

<style lang="scss" scoped>

.badge_availability{
    display: flex;
    align-items: center;
    padding: 0px 10px;
}
.badge_availability:hover{
  background: #eff2f5 !important;
  border-radius: 10px;
  padding: 0px 10px;
  color: #fff !important;
}
</style>