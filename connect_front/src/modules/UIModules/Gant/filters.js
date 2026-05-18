import eventBus from "@/utils/eventBus"
import locale from 'ant-design-vue/es/date-picker/locale/ru_RU'
export default {
    data() {
        return {
            filterStart: null,
            filterEnd: null,
            dateRange: [],
            locale: {
                lang: {
                    ...locale.lang,
                    rangePlaceholder: [
                        this.$t('gantt.fStartDate'), 
                        this.$t('gantt.fEndDate')
                    ]
                },
                timePickerLocale: locale.timePickerLocale
            }
        }
    },
    methods: {
        updateGanttVisibleRange() {
            if (this.filterStart && this.filterEnd) {
                this.gantt.config.start_date = this.filterStart
                this.gantt.config.end_date = this.filterEnd
                this.gantt.render()
            } 
        },
        onDateChange(value) {
            if(value?.length) {
                this.filterStart = this.dateRange[0].set({hour: '00', minute: '00', second: '00', millisecond: '00'}).format()
                this.filterEnd = this.dateRange[1].set({hour: '23', minute: '59', second: '59', millisecond: '59'}).format()
                this.setFilter()
            } else {
                this.clearFilter()
            }
            //this.updateGanttVisibleRange()
        },
        clearFilter() {
            try {
                let filters = {}
                if(this.useProjects) {
                    filters = {
                        fields: {
                            dead_line: {
                                active: true,
                                values: {
                                    end: null,
                                    start: null
                                }
                            }
                        },
                        others: {}
                    }
                }
                this.sendFilters(filters)
            } catch(e) {
                console.log(e)
            }
        },
        setFilter() {
            try {
                let filters = {}
                if(this.useProjects) {
                    filters = {
                        fields: {
                            dead_line: {
                                active: true,
                                values: {
                                    end: this.filterEnd,
                                    start: this.filterStart
                                }
                            }
                        },
                        others: {
                            date_start_plan: this.filterStart,
                            dead_line: this.filterEnd
                        }
                    }
                }
                this.sendFilters(filters)
            } catch(e) {
                console.log(e)
            }
        },
        sendFilters(filters) {
            eventBus.$emit(`send_include_fields_${this.page_name}`, filters)
        }
    },
    mounted() {
        eventBus.$on(`filter_others_${this.page_name}`, data => {
            if(data.date_start_plan)
                this.filterStart = data.date_start_plan
            if(data.dead_line)
                this.filterEnd = data.dead_line
            if(data.date_start_plan && data.dead_line) {
                this.dateRange = [this.$moment(data.date_start_plan), this.$moment(data.dead_line)]
            }
        })
    },
    beforeDestroy() {
        eventBus.$off(`filter_others_${this.page_name}`)
    }
}