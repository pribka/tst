<template>
    <div class="point_popup">
        <div 
            v-for="order in waypoint.orders" 
            :key="order.id" 
            class="order_item">
            <div 
                v-if="order.contractor_member && order.contractor_member.name" 
                class="mb-1">
                Клиент: {{ order.contractor_member.name }}
            </div>
            <div 
                v-if="order.goods_content && order.goods_content.length" 
                class="mb-1">
                Заказ: {{ order.goods_content }}
            </div>
            <div v-if="order.quantity">
                Общее кол-во: {{ order.quantity }}
            </div>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        waypoint: {
            type: Object,
            required: true
        }
    }
}
</script>

<style lang="scss" scoped>
.point_popup{
    .order_item{
        &:not(:last-child){
            padding-bottom: 10px;
            margin-bottom: 10px;
            border-bottom: 1px solid var(--border2);
        }
    }
}
</style>