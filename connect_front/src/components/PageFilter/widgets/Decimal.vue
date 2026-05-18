<template>
    <div class="input_number_wrap flex" >
        <DecimalField 
            v-model="start"
            @change="inputChange('start')"
            @focus="focus"
            :val="start"
            :minimumValue="min"
            :maximumValue="max"
            placeholder="От"
            :decimalLength="decimalLength"/>
        <DecimalField 
            v-model="end"
            class="ml-2"
            @change="inputChange('start')"
            @focus="focus"
            :val="end"
            :minimumValue="min"
            :maximumValue="max"
            placeholder="До"
            :decimalLength="decimalLength"/>
    </div>
</template>

<script>
import filtersCheckbox from '../mixins/filtersCheckbox'
export default {
    components: {
        DecimalField: () => import('@/components/Field/DecimalField')
    },
    mixins: [filtersCheckbox],
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
    
    data() {
        return {
            value: 0,
            start: "",
            end: ""
        
            
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
            } else {
                if(val.start) this.start = val.start
                if(val.end) this.end = val.end
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
        decimalLength(){
            return this.item.decimalLength
        },
        
       
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
// .input_number_wrap{
    
//     .input_number {
//     width: 100%;
//     text-align: right;
  
//     outline: none !important;
//     // border-radius: 0px !important;
// }


// }


</style>