<template>
    <div class="ticket">
        <div
            class="list_view__item"
            :class="[ isMobile && 'is_mobile', bottomBorder && 'item_bt_border',]">

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
            default: true
        }
    },
    computed: {
        useTitle() {
            return this.title || this.$scopedSlots.title
        },
        isMobile() {
            return this.$store.state.isMobile
        },
    }
}
</script>

<style lang="scss" scoped>
.item_label {
    color: #888888;
}
.item_bt_border {
    &.is_mobile{
        border-bottom: 1px solid #e5e7ef !important;
        padding-bottom: 15px !important;
    }

}
.list_view__item {
    /* Mobile: vertical layout */
    &.is_mobile {
        display: flex;
        flex-direction: column;
        align-items: flex-start !important;
    }

    &.is_mobile .item_label {
        margin-bottom: 0.25rem !important;
        opacity: 0.6 !important;
    }

    &.is_mobile .item_value {
        width: 100%;
    }
}
</style>

<style lang="scss">
.ticket {
    .list_view__item {
        margin-bottom: 5px !important;
    }
}
</style>
