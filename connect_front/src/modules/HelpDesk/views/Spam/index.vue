<template>
    <div class="flex flex-col h-full">
        <List
            ref="listComponent"
            :initPageName="initPageName" 
            :initPageModel="initPageModel" />
    </div>
</template>

<script>
export default {
    components: {
        List: () => import('./List.vue')
    },
    props: {
        initPageName: {
            type: String,
            required: true
        },
        initPageModel: {
            type: String,
            required: true
        },
        changeMainViewType: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
        }
    },
    computed: {
        isKanban() {
            return this.viewType === 'kanban' ? true : false
        }
    }
}
</script>

<style lang="scss" scoped>
.header_pd{
    padding: 15px 15px 0 15px;
}
</style>