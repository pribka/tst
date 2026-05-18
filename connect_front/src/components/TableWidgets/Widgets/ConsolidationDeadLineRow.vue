<template>
    <div v-if="isScheduled">
        <template v-if="record.next_dead_line">
            {{ getDate(record.next_dead_line) }}
        </template>
        <template v-else>
            <div class="text-gray-300">Не указан</div>
        </template>
    </div>
    <div v-else>
        <DeadLine 
            :status="record.status" 
            :date="text" />
    </div>
</template>

<script>
export default {
    props: {
        text: {
            type: String
        },
        record: {
            type: Object,
            required: true
        }
    },
    computed: {
        isScheduled() {
            return this.record.is_scheduled
        }
    },
    components: {
        DeadLine: () => import('@apps/Consolidation/components/DeadLine')
    },
    methods: {
        getDate(date) {
            return this.$moment(date).format('DD.MM.YYYY')
        }
    }
}
</script>