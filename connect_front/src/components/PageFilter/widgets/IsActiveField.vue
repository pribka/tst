<template>
    <div class="flex items-center is_active_field">
        <a-radio-group
            v-model="selected"
            @change="onChange"
            size="default">
            <a-radio-button @click="changeBtn(true)" :value="true">
                {{ $t('yes') }}
            </a-radio-button>
            <a-radio-button @click="changeBtn(false)" :value="false">
                {{ $t('no') }}
            </a-radio-button>
        </a-radio-group>
    </div>
</template>

<script>
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
                    value: val
                })
            }
        }
    },
    methods: {
        onChange(e) {
            const value =   e.target.value ? this.$t('yes') : this.$t('no')
            this.$store.commit('filter/SET_FILTER_TAG', {value, name: this.name, filterName: this.filter.name})
        },
        changeBtn(value){
            this.focus()
            if(value){
                if(this.selected){ 
                    this.selected = null
                    this.$store.commit('filter/DELETE_FILTER_TAG', { name: this.name, filterName: this.filter.name})
                }
            } else if(!this.selected)
            {
                this.selected = null
                this.$store.commit('filter/DELETE_FILTER_TAG', { name: this.name, filterName: this.filter.name})
            }
            
            
        }   
    }
}
</script>
<style lang="scss">
.is_active_field   .ant-radio-button-wrapper{
    padding: 0 30px;
}
</style>