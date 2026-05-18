<template>
    <a-range-picker
        class="w-full"
        :ranges="ranges"
        v-model="period"
        @focus="focus"
        :placeholder="[$t('period_start'), $t('period_end')]"
        :valueFormat="dateFormat"
        format="DD.MM.YYYY"
        :mask="{ mask: '00.00.0000', lazy: true, autofix: true }"
        @change="onChange" />
</template>

<script>
import filtersCheckbox from '../mixins/filtersCheckbox'
export default {
    name: 'DateWidget',
    props: {
        filter: {
            type: Object,
            required: true
        },
        name: {
            type: String,
            required: true
        }
    },
    mixins: [filtersCheckbox],
    data() {
        const availablePeriods = {
            year: {
                label: 'Год',
                period: [
                    this.$moment().startOf('year'),
                    this.$moment().endOf('year')
                ]
            },
            half_year_1: {
                label: 'Первое полугодие',
                period: [
                    this.$moment().startOf('year'),
                    this.$moment().month(5).endOf('month')
                ]
            },
            half_year_2: {
                label: 'Второе полугодие',
                period: [
                    this.$moment().month(6).startOf('month'),
                    this.$moment().endOf('year')
                ]
            },
            quarter_1: {
                label: '1 квартал',
                period: [
                    this.$moment().startOf('year'),
                    this.$moment().month(2).endOf('month')
                ]
            },
            quarter_2: {
                label: '2 квартал',
                period: [
                    this.$moment().month(3).startOf('month'),
                    this.$moment().month(5).endOf('month')
                ]
            },
            quarter_3: {
                label: '3 квартал',
                period: [
                    this.$moment().month(6).startOf('month'),
                    this.$moment().month(8).endOf('month')
                ]
            },
            quarter_4: {
                label: '4 квартал',
                period: [
                    this.$moment().month(9).startOf('month'),
                    this.$moment().endOf('year')
                ]
            },
            year_prev_1: {
                label: 'Прошлый год',
                period: [
                    this.$moment().subtract(1, 'year').startOf('year'),
                    this.$moment().subtract(1, 'year').endOf('year')
                ]
            },
            year_prev_2: {
                label: 'Позапрошлый год',
                period: [
                    this.$moment().subtract(2, 'year').startOf('year'),
                    this.$moment().subtract(2, 'year').endOf('year')
                ]
            }
        }
        return {
            availablePeriods,
            dateFormat: "YYYY.MM.DD",
            period: []
        }
    },
    created() {
        const w = this.filter.widget
        this.dateFormat = w.dateFormat

        if(this.selected){
            this.period = [this.selected.start, this.selected.end]
        }
    },
    watch: {
        selected(val){
            if (val === null || (Array.isArray(val) && !val.length)) {
                this.period = []
            }
        }
    },
    computed: {
        ranges() {
            const ranges = {}
            const widgetRanges = this.filter.widget.ranges || []
            widgetRanges.forEach(each => {
                if (this.availablePeriods[each])
                    ranges[this.availablePeriods[each].label] = this.availablePeriods[each].period
            }) 
            return ranges
        },
        selected: {
            get() {
                return this.$store.state.filter.filterSelected[this.name][this.filter.name]
            },
            set(val) {
                this.$store.commit(
                    'filter/SET_SELECTED_FILTER',
                    {
                        name: this.name,
                        filterName: this.filter.name,
                        value: val
                    }
                )
            }
        }
    },
    methods: {
        onChange(period) {
            let data = null
            if (period.length) {
                data = {
                    start: period[0],
                    end: period[1]
                }
            }
            this.selected = data
            if(period.length) { 
                let tags = Object.values(data)
                this.$store.commit(
                    'filter/SET_FILTER_TAG',
                    {
                        value: tags,
                        name: this.name,
                        filterName: this.filter.name
                    }
                )
            } else {
                this.$store.commit(
                    'filter/DELETE_FILTER_TAG',
                    {
                        name: this.name,
                        filterName: this.filter.name
                    }
                )
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.date_select{
    border-bottom: 1px dashed;
    -moz-user-select: none;
    -khtml-user-select: none;
    user-select: none;
    &:hover{
        color: var(--primaryColor);
    }
}
</style>