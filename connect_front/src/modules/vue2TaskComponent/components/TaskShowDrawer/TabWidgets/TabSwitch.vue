<template>
    <component 
        :is="tabWidget" 
        :task="task"
        :myTask="myTask"
        :reloadTask="reloadTask"
        :dropActions="dropActions"
        :checkRole="checkRole"
        :getCommentsCount="getCommentsCount"
        :edit="edit"
        :tab="tab"
        :code="code"
        :hideDeliveryMap="hideDeliveryMap"
        :openTask="openTask"
        :isMobile="isMobile"
        :isOperator="isOperator"
        :closeDrawer="closeDrawer"
        :bodyWrap="bodyWrap"
        :isAuthor="isAuthor" />
</template>

<script>
export default {
    props: {
        tab: {
            type: Object,
            default: () => null
        },
        task: {
            type: Object,
            required: true
        },
        myTask: {
            type: Boolean,
            default: false
        },
        reloadTask: {
            type: Function,
            default: () => {}
        },
        getCommentsCount: {
            type: Function,
            default: () => {}
        },
        edit: {
            type: Function,
            default: () => {}
        },
        openTask: {
            type: Function,
            default: () => {}
        },
        dropActions: {
            type: Object,
            default: () => null
        },
        checkRole: {
            type: Function,
            default: () => {}
        },
        code: {
            type: [String, Number],
            required: true
        },
        isMobile: {
            type: Boolean,
            default: false
        },
        isOperator: {
            type: Boolean,
            default: false
        },
        hideDeliveryMap: {
            type: Boolean,
            default: true
        },
        isAuthor: {
            type: Boolean,
            required: true
        },
        closeDrawer: {
            type: Function,
            default: () => {}
        },
        bodyWrap: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        tabWidget() {
            return () => import(`./${this.tab.component}`)
                .then(module => {
                    return module
                })
                .catch(e => {
                    console.log('error')
                    return import(`./NotWidget.vue`)
                })
        }
    }
}
</script>