<template>
    <div class="input_number_wrap flex" >
        <a-input-number
            @change="inputChange('start')"
            @focus="focus"
            class="input_number"
            placeholder="От"
            allowClear
            v-model="start"
            :min="min"
            :max="max"
            v-mask="'#################################'"
            size="default"    />
        <a-input-number
            @change="inputChange('end')"
            @focus="focus"
            class="input_number ml-1"
            placeholder="До"
            allowClear
            v-model="end"
            :min="min"
            :max="max"
            v-mask="'#################################'"
            size="default"    />
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
    
    data() {
        return {
            value: 0,
            start: null,
            end: null
        
            
        }
    },
    created() {
        if(this.selected){
            if(this.selected.start) this.start  = this.selected.start
            if(this.selected.end) this.end  = this.selected.end
        }
    },
    watch: {
        selected(val){
            if(val === null){
                this.start =  this.end = null
               
            }
        }
    },
    computed:{
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
        item(){
            return this.filter.widget
        },
        min(){
            return  parseInt(this.item.minValue)
        },
        max(){
            return  parseInt(this.item.maxValue)
        },
        
        defaultValue(){
            return this.item.defaultValue
        }
    },
    methods: {
        inputChange(mode) {

            let data = {} 
          
            if(this.start) data['start'] = this.start
            if(this.end) data['end'] = this.end

            this.selected = data

            if(this.start || this.end) { 
                let tags = Object.values(data)
        
                this.$store.commit('filter/SET_FILTER_TAG', {value: tags, name: this.name, filterName: this.filter.name})
            }
            else
                this.$store.commit('filter/DELETE_FILTER_TAG', {name: this.name, filterName: this.filter.name})


        
        },
        
    },
   

}
</script>

<style lang="scss" >
.input_number_wrap{
    
    .input_number {
    width: 100%;
    text-align: right;
  
    outline: none !important;
    // border-radius: 0px !important;
}


}


</style>