<template>
    <div v-if="record" class="flex items-center truncate">
        <template v-if="isScheduled">
            <span class="truncate">{{ getDate(record.next_start) }} - {{ getDate(record.next_end) }}</span>
        </template>
        <template v-else>
            <span class="truncate">{{ getDate(record.start) }} - {{ getDate(record.end) }}</span>
        </template>
    </div>
    <div v-else class='text-gray-300'>
        Не указан
    </div>
</template>

<script>
export default {
    props: {
        record: {
            type: Object,
            default: () => null
        },
    },
    computed: {
        isScheduled() {
            return this.record.is_scheduled
        }
    },
    methods: {
        getDate(dateStamp) {
            return this.$moment(dateStamp).format('DD.MM.YYYY')
        }
    }
}
</script>