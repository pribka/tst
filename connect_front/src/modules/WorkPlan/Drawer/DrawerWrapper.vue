<template>
    <DrawerTemplate
        :value="value"
        :width="computedWidth"
        class="my_plan_drawer"
        destroyOnClose
        :titleTruncate="titleTruncate"
        @input="$emit('input', $event)"
        @afterVisibleChange="afterVisibleChange"
        @close="close">
        <template #title>
            <slot name="title" />
        </template>
        <slot name="body" />
        <template v-if="$slots.footer" #footer>
            <slot name="footer" />
        </template>
    </DrawerTemplate>
</template>

<script>
import { mapState } from 'vuex'
export default {
    props: {
        value: {
            type: Boolean,
            default: false
        },
        titleTruncate: {
            type: Boolean,
            default: false
        },
        width: {
            type: [Number, String],
            default: 1350
        }
    },
    components: {
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue')
    },
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth
        }),
        computedWidth() {
            if(typeof this.width === 'string')
                return this.width

            return this.windowWidth > this.width ? this.width : '100%'
        }
    },
    methods: {
        close() {
            this.$emit('input', false)
            this.$emit('close')
        },
        afterVisibleChange(vis) {
            this.$emit('afterVisibleChange', vis)
        }
    }
}
</script>

<style lang="scss">
.my_plan_drawer{
    .ant-drawer-content{
        background: #f7f9fc;
    }
}
</style>
