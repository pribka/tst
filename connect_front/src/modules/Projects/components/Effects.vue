<template>
    <div style="max-width:80%;">
        <a-progress
            class="row_progress"
            :stroke-color="{
                '0%': '#4179fb',
                '100%': '#4179fb',
            }"
            :percent="percent"/>
    </div>
</template>

<script>
export default {
    props: {
        item: {
            type: Object,
            required: true
        }
    },
    computed: {
        percent() {
            const { tasks, complete_tasks } = this.item
            return parseInt(((complete_tasks / tasks) * 100).toFixed(2))
        }
    }
}
</script>

<style lang="scss" scoped>
.row_progress{
    &::v-deep{
        .ant-progress-inner{
            background: #e8ecfa;
        }
        .ant-progress-text{
            color: #888888;
        }
    }
}
</style>