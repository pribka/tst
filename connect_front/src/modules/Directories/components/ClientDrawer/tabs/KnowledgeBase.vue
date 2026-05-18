<template>
    <a-row :gutter="{xs: 15, md: 20, lg: 30, xxl: 30}" class="h-full">
        <a-col 
            :sm="24" 
            :xl="6"
            :xxl="6"
            class="h-full">
            <div class="drawer_aside">
                
            </div>
        </a-col>
        <a-col
            :sm="24"
            :xl="18"
            :xxl="18"
            class="h-full">
            
        </a-col>
    </a-row>
</template>

<script>
export default {
    props: {
        client: {
            type: Object,
            required: true
        },
        actions: {
            type: Object,
            default: () => null
        }
    },
    data() {
        return {
            
        }
    },
    methods: {
        
    }
}
</script>

<style lang="scss" scoped>
.drawer_aside{
    padding: 20px;
    background: #F8F9FC;
    border: 1px solid #E5E7EF;
    border-radius: 6px;
    color: #000;
}
</style>