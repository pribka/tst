<template>
    <a-button
        type="ui"
        :size="size"
        @click="openTableSettings"
        flaticon
        v-tippy
        :content="$t('table.settings')"
        class="flex items-center justify-center"
        :shape="shape"
        ghost
        icon="fi-rr-settings" />
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    props: {
        size: {
            type: String,
            default: 'large'
        },
        pageName: {
            type: String,
            required: true
        },
        zIndex: {
            type: Number,
            default: 1000
        },
        shape: {
            type: [String, Object],
            default: () => null
        }
    },
    methods: {
        openTableSettings() {
            eventBus.$emit(`open_table_settings_${this.pageName}`, this.zIndex)
        }
    }
}
</script>