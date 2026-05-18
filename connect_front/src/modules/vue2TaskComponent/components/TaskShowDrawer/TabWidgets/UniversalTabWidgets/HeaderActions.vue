<template>
    <div 
        v-if="checkAccess || checkHeaderWidgets" 
        class="header_actions mb-4 flex items-center">
        <a-button
            v-if="checkAccess" 
            :icon="tab.headerButtons.createButton.icon" 
            :size="tab.headerButtons.createButton.size"
            :type="tab.headerButtons.createButton.type"
            class="item"
            @click="buttonHandler()">
            {{ tab.headerButtons.createButton.title }}
        </a-button>
        <template v-if="checkHeaderWidgets">
            <WidgetSwitch 
                v-for="item in tab.headerButtons.headerWidgets" 
                :key="item"
                class="item"
                :item="item"
                :task="task" />
        </template>
    </div>
</template>

<script>
import accessMixins from './accessMixins.js'
import WidgetSwitch from './ListHeader/WidgetSwitch.vue'
export default {
    components: {
        WidgetSwitch
    },
    mixins: [
        accessMixins
    ],
    props: {
        value: {
            type: Boolean
        },
        tab: {
            type: Object,
            default: () => null
        },
        task: {
            type: Object,
            default: () => null
        },
        code: {
            type: [String, Number],
            required: true
        }
    },
    computed: {
        checkHeaderWidgets() {
            return this.tab?.headerButtons?.headerWidgets?.length ? true : false
        }
    },
    methods: {
        buttonHandler() {
            this.$emit('input', true)
        }
    }
}
</script>

<style lang="scss" scoped>
.header_actions{
    .item{
        &:not(:last-child){
            margin-right: 15px;
        }
    }
}
</style>