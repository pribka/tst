<template>
    <div style="max-width:80%;">
        <a-progress
            :stroke-color="{
                '0%': '#108ee9',
                '100%': '#87d068',
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