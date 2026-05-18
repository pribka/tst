<template>
    <a-radio-group 
        v-model="active"
        size="large"
        class="ml-1 grid_type">
        <span v-if="loading">
            <a-spin size="small" />
        </span>
        <template v-else>
            <a-radio-button 
                v-for="item in gridType" 
                :key="item.type" 
                :value="item.type">
                <i class="fi" :class="item.icon"></i>
            </a-radio-button>
        </template>
    </a-radio-group>
</template>

<script>
export default {
    computed: {
        active: {
            get() {
                return this.$store.state.products.activeGridType
            },
            set(val) {
                this.$store.commit('products/CHANGE_ACTIVE_TYPE', val)
            }
        },
        gridType() {
            return this.$store.state.products.gridType
        }
    },
    data() {
        return {
            loading: false
        }
    },
    async created() {
        if(!this.gridType?.length)
            await this.getType()
        this.$store.commit('products/SET_DEFAULT_GRID_TYPE')
    },
    methods: {
        async getType() {
            try {
                this.loading = true
                await this.$store.dispatch('products/getGridType')
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.grid_type{
    display: flex;
    .ant-radio-button-wrapper{
        border: 0px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        padding: 0 10px;
        &::before{
            display: none;
        }
    }
}
</style>

<style lang="scss">
.grid_type{
    .ant-radio-button{
        display: none;
    }
    span{
        display: flex;
        align-items: center;
        justify-content: center;
    }
}
</style>