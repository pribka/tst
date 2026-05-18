<template>
    <div class="flex" :class="isVertical ? 'flex-col gap-2' : 'flex-row gap-2'">
        <DateTimeField
            v-model="start"
            ref="DateTimeField"
            class="w-full"
            :dateFormat="dateFormat"
            :currentDate="currentDate"
            :placeholder="$t('from')"
            :wConfig="wConfig"
            :time="time"
            allowClear
            :focus="focus"
            @change="changeValue('start')" />
        <DateTimeField
            class="w-full"
            :class="isVertical ? 'mt-2':'ml-1'"
            v-model="end"
            ref="DateTimeField"
            :placeholder="$t('to')"
            :dateFormat="dateFormat"
            :currentDate="currentDate"
            :wConfig="wConfig"
            :time="time"
            allowClear
            :focus="focus"
            @change="changeValue('end')" />
    </div>
</template>

<script>
import filtersCheckbox from '../mixins/filtersCheckbox'
import {formatsInMoments} from '@/utils/dateSettings'
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
        },
        vertical: {
            type: Boolean,
            default: false
        }
    },
    mixins: [filtersCheckbox],
    components: {
        DateTimeField: () => import('@/components/Field/DateTimeField')
    },
    data() {
        return {
            start: null,
            end: null,
            value: "",
            dateFormat: "YYYY.MM.DD",
            currentDate: false,
            time: false,
            wConfig: {
                size: 'default',
                disabled: false
            }

        }
    },
    created() {
        const w = this.filter.widget
        this.dateFormat = w.dateFormat
        this.time = w.time   

        if(this.selected){
            if(this.selected.start) this.start  = this.selected.start
            if(this.selected.end) this.end  = this.selected.end
        }
    },
    watch: {
        selected(val){
            if(val === null){
                this.start = this.end = null
            }
        }
    },
    computed: {
        isVertical() {
            return this.vertical || this.windowWidth <= 1436
        },
        selected: {
            get() {
                return this.$store.state.filter.filterSelected[this.name][this.filter.name]
            },
            set(val) {
                this.$store.commit('filter/SET_SELECTED_FILTER', {
                    name: this.name,
                    filterName: this.filter.name,
                    value: val
                })
            }
        },
        windowWidth() {
            return this.$store.state.windowWidth
        }
    },
    methods: {
        changeValue(mode){
            const m = this.$moment(mode === 'start' ? this.start : this.end, this.dateFormat)
            let value = null
            if (m && m.isValid()) {
                value = m.format('YYYY-MM-DD')
            }

            const start = mode === 'start'
                ? value
                : (this.start ? this.$moment(this.start, formatsInMoments).format('YYYY-MM-DD') : null)

            const end = mode === 'end'
                ? value
                : (this.end ? this.$moment(this.end, formatsInMoments).format('YYYY-MM-DD') : null)

            let data = {}
            data['start'] = start
            data['end'] = end

            if (start === null && end === null) data = null

            this.selected = data

            if (this.start || this.end) {
                let tags = Object.values(data)
                this.$store.commit('filter/SET_FILTER_TAG', { value: tags, name: this.name, filterName: this.filter.name })
            } else {
                this.$store.commit('filter/DELETE_FILTER_TAG', { name: this.name, filterName: this.filter.name })
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

<style lang="scss">
.date_filed{
    min-width:100%!important;
}
</style>