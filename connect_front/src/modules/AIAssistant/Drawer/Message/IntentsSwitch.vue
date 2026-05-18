<template>
    <div class="intents_card">
        <component 
            :is="IntentsWidget" 
            :intents="intents" 
            :injectUpdate="injectUpdate"
            :injectDelete="injectDelete"
            :useInject="useInject"
            :injectCreated="injectCreated"
            :injectChangeField="injectChangeField"
            :intentIndex="intentIndex"
            :messageIndex="messageIndex"
            :message="message" />
    </div>
</template>

<script>
export default {
    props: {
        intents: {
            type: Object,
            required: true
        },
        message: {
            type: Object,
            required: true
        },
        messageIndex: {
            type: Number,
            default: 0
        },
        intentIndex: {
            type: Number,
            default: 0
        },
        useInject: {
            type: Boolean,
            default: false
        },
        injectUpdate: {
            type: Function,
            default: () => {}
        },
        injectDelete: {
            type: Function,
            default: () => {}
        },
        injectChangeField: {
            type: Function,
            default: () => {}
        },
        injectCreated: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        IntentsWidget() {
            if(!this.intents.is_active)
                return () => import(`./IntentsWidgets/IntentsEmpty.vue`)
            else
                return () => import(`./IntentsWidgets/IntentWidget.vue`)
        }
    }
}
</script>

<style lang="scss" scoped>
.intents_card{
    width: 100%;
    background: #fff;
    border-radius: 8px;
    padding: 12px;
    &:not(:last-child){
        margin-bottom: 10px;
    }
}
</style>