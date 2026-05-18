<template>
    <div v-if="record.channel" class="flex items-center">
        <template v-if="record.channel?.icon">
            <img 
                v-if="isSVG" 
                :src="require(`@/assets/svg/${record.channel.icon}`)"
                class="mr-2 channel_icon" />
            <i 
                v-else 
                class="mr-2 fi" 
                :class="record.channel.icon"></i>
        </template>
        {{ record.channel.name }}
    </div>
</template>

<script>
export default {
    props: {
        main: { // Если вставляем этот компонент куда то помимо страницы задач, тут надо ставить false
            type: Boolean,
            default: false
        },
        record: {
            type: Object,
            required: true
        },
        text: {
            type: [Object, Number, String],
        },
        expandedRowKeys: {
            type: Array,
        },
        expanded: {
            type: Number,
        },
        extendDrawer: {
            type: Boolean,
            default: false
        },
        showChildren: { // Показывать или возможность раскрыть задачу с подзадачами
            type : Boolean,
            default: true
        },
        indent: {
            type: Object,
        },
        column: {
            type: Object,
            default: () => null
        },
        openTask: {
            type: Function,
            default: () => {}
        },
        reloadTask: {
            type: Function,
            default: () => {}
        },
        pageName: {
            type: String,
            default: ''
        }
    },
    computed: {
        isSVG() {
            return this.record.channel?.icon?.endsWith('.svg')
        },
    }
}
</script>

<style lang="scss" scoped>
.channel_icon{
    max-width: 16px;
}
</style>