<template>
    <div ref="wrap">
        <a-date-picker
            v-model="valueProxy"
            inputType="ghost"
            class="w-full"
            :allowClear="true"
            :getCalendarContainer="() => $refs.wrap"
            format="DD-MM-YYYY"
            :placeholder="$t('Date')" />
    </div>
</template>

<script>
export default {
    props: {
        item: {
            type: Object,
            required: true,
        },
        changeItemValue: {
            type: Function,
            required: true,
        },
    },
    computed: {
        valueProxy: {
            get() {
                return this.item.value ? this.$moment(this.item.value) : null
            },
            set(value) {
                if (value) {
                    this.changeItemValue(value.format('YYYY-MM-DD'))
                } else {
                    this.changeItemValue(null)
                }
            }
        }
    },
    methods: {
    }
}
</script>
