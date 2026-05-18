<template>
    <div class="cursor-pointer" @click="openHandler()">
        <div>{{ record.request_type.name }}</div>
        <div v-if="record.description" class="truncate" style="opacity: 0.6;">
            {{ record.description }}
        </div>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    props: {
        record: {
            type: Object,
            required: true
        },
    },
    methods: {
        openHandler() {
            const query = JSON.parse(JSON.stringify(this.$route.query))
            if(!query.approvals) {
                query.approvals = this.record.id
                this.$router.push({query})
            } else {
                eventBus.$emit('approvals_drawer_close')
                setTimeout(() => {
                    query.approvals = this.record.id
                    this.$router.push({query})
                }, 500)
            }
        },
    }
}
</script>