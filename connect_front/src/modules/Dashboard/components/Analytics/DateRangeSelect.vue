<template>
    <div class="flex">
        <a-date-picker
            class="mr-2"
            v-model="filters.dateRange.start"
            :valueFormat="filters.dateRange.format"
            :placeholder="$t('dashboard.start')"
            @change="$emit('updateFilters')" />
        <a-date-picker
            :valueFormat="filters.dateRange.format"
            v-model="filters.dateRange.end"
            :placeholder="$t('dashboard.end')"
            @change="$emit('updateFilters')" />
    </div>
</template>

<script>
export default {
    props: {
        filters: {
            type: Object,
            required: true
        }
    },
    created() {
        const dateRange = this.filters.dateRange
        const isDataRangeEmpty = !dateRange.start || !dateRange.end
        if (isDataRangeEmpty) {
            this.initDateRange()
        }
    },
    methods: {
        initDateRange() {
            this.filters.dateRange.start = this.$moment(new Date()).subtract(1, 'week')
            this.filters.dateRange.end = this.$moment(new Date())
        },
    }
}
</script>

<style>

</style>