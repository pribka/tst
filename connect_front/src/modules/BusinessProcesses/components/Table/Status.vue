<template>
    <a-tag :color="statusColor">
        {{ statusText }}
    </a-tag>
</template>

<script>
import { statusTextSwitch, statusColorSwitch } from '../../utils'
export default {
    props: {
        record: {
            type: Object,
            required: true
        }
    },
    computed: {
        statusText() {
            return statusTextSwitch(this.record.status)
        },
        statusColor() {
            return statusColorSwitch(this.record.status)
        }
    }
}
</script>