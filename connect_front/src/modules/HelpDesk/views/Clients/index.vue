<template>
    <component 
        :is="viewComponent" 
        :initPageName="initPageName" 
        :initPageModel="initPageModel" />
</template>

<script>
export default {
    components: {
        Segmented: () => import('@apps/UIModules/Segmented')
    },
    props: {
        initPageName: {
            type: String,
            default: ""
        },
        initPageModel: {
            type: String,
            default: ""
        },
        changeMainViewType: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        viewComponent() {
            return () => import('./Table.vue')
        }
    }
}
</script>