<template>
    <span 
        v-if="hasPriorityIcon">
        <a-tooltip 
            destroyTooltipOnHide
            :title="title">
            <img
                :height="iconPixelSize"
                :width="iconPixelSize"
                :src="imgPath" />
        </a-tooltip>
    </span>
</template>

<script>
export default {
    props: {
        item: {
            type: Object,
            required: true
        },
        iconPixelSize: {
            type: Number,
            default: 14
        }
    },
    computed: {
        hasPriorityIcon() {
            const displayedPriorityList = [0, 3, 4]
            return displayedPriorityList.includes(this.item.priority)
        },
        title() {
            if(this.item.priority === 0)
                return this.$t('task.very_low_priority')
            if(this.item.priority === 3)
                return this.$t('task.large_priority')
            if(this.item.priority === 4)
                return this.$t('task.very_large_priority')
            return ''
        },
        imgPath() {
            if(this.item.priority === 0)
                return require('../../../assets/images/down-arrow.svg')
            if(this.item.priority === 3)
                return require('../../../assets/images/fire.svg')
            if(this.item.priority === 4) 
                return require('../../../assets/images/rocket.svg')
            return ''
        }
    }
}
</script>