<template>
    <a-tag 
        block
        size="large"
        :color="statusColor">{{ $t(`sprint.${record.status}`) }}</a-tag>
</template>
<script>
export default {
    props: {
        record: {
            type: Object,
            required: true
        },
    },
    computed: {
        statusColor() {
            switch (this.record.status) {
            case "new":
                return "blue";
                break;
            case "in_process":
                return "purple";
                break;
            case "completed":
                return "green";
                break;
            default:
                return "blue";
            }
        },
    }
}
</script>