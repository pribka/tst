<template>
    <a-input
        v-model="selected"
        @change="changeInput"
        @focus="focus"
        allowClear
        :placeholder="$t('f_input_p')"
        size="default" />
</template>

<script>
// import eventBus from '../utils/eventBus'
import filtersCheckbox from '../mixins/filtersCheckbox'
export default {
    props: {
        filter: {
            type: Object,
            required: true
        },
        name: {
            type: String,
            required: true
        },
        windowWidth: {
            type: Number,
            default: 0
        }
    },
    mixins: [filtersCheckbox],
    computed: {
        selected: {
            get() {
                return this.$store.state.filter.filterSelected[this.name][this.filter.name]
            },
            set(val) {
                this.$store.commit('filter/SET_SELECTED_FILTER', {
                    name: this.name,
                    filterName: this.filter.name,
                    value: val === "" ? null: val
                })
            }
        }
    },
    methods: {
        changeInput() {
            this.$store.commit('filter/SET_FILTER_TAG', {value: this.selected, name: this.name, filterName: this.filter.name})
        },
        
    },
    
}
</script>