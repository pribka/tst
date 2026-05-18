<template>
    <div class="order_block">
        <h2 v-if="showTitle">Файлы в заказе</h2>
        <div class="files_list">
            <div 
                v-for="item in order.attachments" 
                :key="item.id" 
                class="file">
                <a 
                    :href="item.path" 
                    target="_blank">
                    {{ item.name }}
                </a>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        order: {
            type: Object,
            required: true
        },
        showTitle: {
            type: Boolean,
            default: true
        }
    }
}
</script>

<style lang="scss" scoped>
.files_list{
    .file{
        a{
            display: block;
            padding: 15px 0;
        }
        &:not(:last-child){
            border-bottom: 1px solid var(--border2);
        }
    }
}
</style>