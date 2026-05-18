<template>
    <div 
        class="page_title flex items-center" 
        :class="wrapClass">
        <a-button 
            v-if="back"
            icon="arrow-left"
            class="mr-1 text_current"
            type="link"
            @click="backRoute()" />
        <div 
            v-if="loading"
            class="title_loader">
            <a-skeleton
                active
                :paragraph="{ rows: 1 }" />
        </div>
        <h1 v-else>
            {{ title }}
        </h1>
    </div>
</template>

<script>
export default {
    props: {
        title: {
            type: String,
            required: true
        },
        wrapClass: {
            type: String,
            default: 'pb-4'
        },
        back: {
            type: Boolean,
            default: false
        },
        loading: {
            type: Boolean,
            default: false
        }
    },
    methods: {
        backRoute() {
            this.$router.push({ name: 'business_processes_main' })
        }
    }
}
</script>

<style lang="scss">
.page_title{
    .ant-skeleton-paragraph{
        display: none;
    }
    .ant-skeleton-title{
        margin: 0px;
    }
    .ant-skeleton-title{
        height: 22px;
    }
}
</style>

<style lang="scss" scoped>
.page_title{
    h1{
        font-weight: 300;
        font-size: 24px;
    }
    .title_loader{
        min-height: 36px;
        width: 100%;
        display: flex;
        align-items: center;
    }
}
</style>