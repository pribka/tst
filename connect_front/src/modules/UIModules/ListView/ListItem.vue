<template>
    <div class="list_view__item" :class="bottomBorder && 'item_bt_border'">
        <div v-if="useTitle" class="item_label">
            <template v-if="title">
                {{ title }}
            </template>
            <template v-else-if="$scopedSlots.title">
                <slot name="title" />
            </template>
        </div>
        <div class="item_value" :class="!useTitle && 'w-full'">
            <slot />
        </div>
    </div>
</template>

<script>
export default {
    props: {
        title: {
            type: String,
            default: ""
        },
        bottomBorder: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        useTitle() {
            return this.title || this.$scopedSlots.title
        }
    }
}
</script>

<style lang="scss" scoped>
.item_label{
    color: #888888;
}
.list_view__item{
    &.item_bt_border{
        padding-bottom: 15px;
        border-bottom: 1px solid #dadada;
    }
}
</style>
