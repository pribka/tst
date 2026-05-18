<template>
    <a-popover transitionName="" destroyTooltipOnHide :getPopupContainer="getPopupContainer">
        <template slot="content">
            <div style="max-width: 400px;" v-html="record.description" />
        </template>
        <div class="truncate">
            {{ record.description }}
        </div>
    </a-popover>
</template>

<script>

export default {
    props: {
        record: {
            type: Object,
            required: true
        },
        colParams: {
            type: Object,
            default: () => null
        }
    },
    methods: {
        getPopupContainer() {
            return this.colParams.getPopupContainer()
        }
    }
}
</script>