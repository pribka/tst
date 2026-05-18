<template>
    <span 
        v-if="[0, 3, 4].includes(record.priority)"
        class="inline-block w-4 h-4">
        <a-tooltip 
            destroyTooltipOnHide
            :title="title">
            <img v-if="record.priority === 0" src="../assets/images/down-arrow.svg" />
            <img v-else-if="record.priority === 3" src="../assets/images/fire.svg" />
            <img v-else-if="record.priority === 4" src="../assets/images/rocket.svg" />
        </a-tooltip>
    </span>
</template>

<script>
export default {
    props: {
        record: {
            type: Object,
            requred: true
        }
    },
    data() {
        return {
            priorityList: {
                0: {
                    title: this.$t('task.very_low_priority'),
                },
                3: {
                    title: this.$t('task.large_priority'),
                },
                4: {
                    title: this.$t('task.very_large_priority'),
                },
            }
        }
    },
    computed: {
        title() {
            return this.priorityList[this.record.priority].title
        },
        image() {
            return require(this.priorityList[this.record.priority].image)
        }
    }
}
</script>