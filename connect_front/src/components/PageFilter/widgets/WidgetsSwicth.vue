<template>
    <div class="w-full filter_item">
        <div class="flex">
            <a-checkbox v-model="active" />
            <label @click="active = !active;" class="mb-1 ml-2 block cursor-pointer select-none">{{filter.verbose_name}}</label> 
        </div>
        <component
            v-bind:is="typeSwicth"
            :windowWidth="windowWidth"
            :filter="filter"
            :filterPrefix="filterPrefix"
            :modelLabel="modelLabel"
            :injectSelectParams="injectSelectParams"
            :page_name="page_name"
            :filterBodyRef="filterBodyRef"
            :active="active"
            :vertical="vertical"
            :name="name" />
    </div>
</template>

<script>
export default {
    props: {
        filter: {
            type: Object,
            required: true
        },
        windowWidth: {
            type: Number,
            default: 0
        },
        name: {
            type: String,
            required: true
        },
        vertical: {
            type: Boolean,
            default: false
        },
        page_name: {
            type: [String, Number],
            default: ''
        },
        filterPrefix: {
            type: String,
            default: ''
        },
        modelLabel: {
            type: String,
            default: ''
        },
        injectSelectParams: {
            type: Object,
            default: () => {}
        },
        filterBodyRef: { type: [HTMLElement, Object], default: null }
    },
   
    created(){
        if(this.active === undefined)
            this.changeActive()
    },
    methods: {
        changeActive(){
            this.$store.commit("filter/SET_ACTIVE_FILTERS", 
                {name: this.name, filterName: this.filter.name, value: false})
        },
    },
    computed: {
        typeSwicth() {
            return () => import(`./${ this.filter.widget.type }`)
        },
        active: {
            get() {
                return this.$store.state.filter.filterActive[this.name][this.filter.name]
            },
            set(value) {
                this.$store.commit("filter/SET_ACTIVE_FILTERS", 
                    {name: this.name, filterName: this.filter.name, value})
            }
        }
    }
}
</script>