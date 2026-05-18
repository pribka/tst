<template>
    <div
        :style="`border-color: ${event.color}`" 
        class="border-l-4 relative font-light text-xs overflow-hidden py-1 px-2 rounded">        
        <div class="event_bg" :style="`background: ${event.color}`"></div>
        <div class="relative">
            <span>
                {{ startTime }} - {{ event.name }}
            </span>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        event: {
            type: Object,
            required: true
        }
    },
    computed: {
        startTime() {
            return this.$moment(this.event.start).calendar()
        },
    }
}
</script>

<style lang="scss" scoped>
.event_bg{
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    opacity: 0.3;
}
</style>