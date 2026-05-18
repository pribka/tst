<template>
    <div v-if="record?.repeat_to">
        <span class="truncate">{{ getDate(record.repeat_to) }}</span>
    </div>
    <div v-else class='text-gray-300'>
        Постоянно
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
    methods: {
        getDate(dataStamp) {
            return this.$moment(dataStamp).format('DD.MM.YYYY')
        }
    }
}
</script>