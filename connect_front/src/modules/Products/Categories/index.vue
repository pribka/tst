<template>
    <component 
        :is="widget"
        :list="list"
        :loading="loading"
        :expandedKeys="expandedKeys"
        :selectedKeys="selectedKeys"
        :activeEl="activeEl"
        :mainCategory="mainCategory"
        :selectEl="selectEl"
        :selectMobileEl="selectMobileEl"
        :onExpand="onExpand"
        :returnAllCategory="returnAllCategory"/>
</template>

<script>
import { mapMutations } from 'vuex'
import eventBus from "@/utils/eventBus"
export default {
    props: {
        value: String,
        model: {
            type: [String, Number],
            required: true
        },
        page_name: {
            type: String,
            default: 'catalogs.goodsmodel_list_page'
        }
    },
    data() {
        return {
            loading: false,
            list: [],
            expandedKeys: [],
            selectedKeys: [],
            mainCategory: true,
        }
    },
    computed:{
        activeEl(){
            return [this.$route.query.category] || []
        },
        selCategory(){
            return this.$route.query.category || null
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        widget() {
            if(this.isMobile)
                return () => import('./Drawer.vue')
            return () => import('./Tree.vue')
        }
    },
    watch: {
        selCategory(val){
            this.setCategoryStore(val)
        },
        '$route.query.category'(){
            this.selectedKeys = this.activeEl
        }
    },
    created() {
        this.categoryInit()
        eventBus.$on('filter_is_set', () => {
            this.cacheData = null
        })
    },
    beforeDestroy() {
        eventBus.$off('filter_is_set')
    },
    methods: {
        ...mapMutations({
            setCategoryStore: 'products/SET_CATEGORY'
        }),
        async categoryInit() {
            this.setCategoryStore(this.selCategory)
            if(this.selCategory && this.selCategory !== 'all')
                if(this.isMobile)
                    await this.getAllCategory()
                else
                    await this.getCategory(this.selCategory)
            else    
                await this.getAllCategory()
            
            this.selectedKeys = this.activeEl

            this.expandedKeys = JSON.parse(localStorage.getItem('expandedKeysCategories')) || []
        },
        async getAllCategory(){
            try{ 
                this.loading = true
                let params = {
                    page_name: this.page_name
                }
                const {data} = await this.$http('catalogs/goods_category/', {params})
                this.list = data
                this.cacheData = data
            } catch(e){
                console.error(e)
            }
            finally{
                this.loading = false
                this.selectedKeys = []
                this.mainCategory = true
            }
        },
        async getCategory(id){
            try{ 
                this.loading = true
                let params = {
                    page_name: this.page_name
                }
                const {data} = await this.$http(`catalogs/goods_category_structure/${id}/`, {params})

                this.list = data
            }
            catch(e){
                console.error(e)
            }
            finally{
                this.mainCategory = false
                this.loading = false
            }
        },
        async returnAllCategory(main) {
            try{ 
                this.loading = true
                if(this.cacheData){ 
                    this.list = this.cacheData
                    if(main){ 
                        this.mainCategory = true
                        let query = Object.assign({}, this.$route.query)
                        if(query['category'] !== 'all'){ 
                            query['category'] ='all'
                            this.$router.replace({query})
                        }
                        this.expandedKeys = []
                        this.selectedKeys = []
                    }  
                    else this.mainCategory = false
                   
                } else await this.getAllCategory()
            } 
            catch(e){
                console.error(e)
            }
            finally{
                this.loading = false
            }
        },
        selectEl(val, e){
            if(val.length > 0){ 
                const top = e.selectedNodes[0]?.data?.props?.top
                this.selectedKeys = val
        
                let query = Object.assign({}, this.$route.query)
                if(query['category'] !== val[0]){ 
                    query['category'] = val[0]
                    this.$router.replace({query})
                }
                this.getCategory(val[0]) 
                this.expandedKeys.push(val[0])
            }
            
        },
        selectMobileEl(val){
            if(val.length > 0){ 
                this.selectedKeys = val
        
                let query = Object.assign({}, this.$route.query)
                if(query['category'] !== val[0]){ 
                    query['category'] = val[0]
                    this.$router.replace({query})
                }
            }
            
        },
        onExpand(expandedKeys) {
            this.expandedKeys = expandedKeys;
            localStorage.setItem('expandedKeysCategories', JSON.stringify(expandedKeys))
        },
        getParentsByKey(list, key) {
            for(const item of list) {
                // console.log(item.title)
                if(item.key === key)
                    return [item.key]
                if(item.children) {
                    const childKeys = this.getParentsByKey(item.children, key)
                    if(childKeys)
                        return childKeys.concat(item.key)
                } 
            }
            return false
        },
    },
    mounted(){
        eventBus.$on("update_products_category", (id) => {
            if(this.isMobile) {
                const itemParents = this.getParentsByKey(this.list, id)
                this.expandedKeys.splice(0)
                this.expandedKeys.push(...itemParents)
            }
            else
                this.getCategory(id)
        })
        eventBus.$on(`update_filter_${this.model}`, () => {
            this.categoryInit()
        })
    },
    beforeDestroy(){
        eventBus.$off("update_products_category")
        eventBus.$off(`update_filter_${this.model}`)
    }
}
</script>

<style lang="scss" scoped>
.main_category{ 
    color: #1d65c0;
    &:hover,
    &.active{
        color: #000;
    }
}
</style>

