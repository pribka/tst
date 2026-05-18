<template>
    <transition name="slide-fade">
        <div v-if="showStatistics" class="day_statistics">
            <div class="day_progress"> <!--v-if="dayStatistics.by_work_type && dayStatistics.by_work_type.length > 1"-->
                <div
                    v-for="(item, index) in dayStatistics.by_work_type"
                    :key="index"
                    class="day_progress__segment"
                    v-tippy
                    :content="`${item.work_type_name} (${item.quantity_percentage}%): ${secondsFormat(item.duration)}`"
                    :class="{ active: hoverIndex === index }"
                    :style="{
                        width: item.quantity_percentage + '%',
                        backgroundColor: item.work_type_color,
                        boxShadow: 'initial'
                    }"/>
            </div>
            <div class="day_statistics__list flex items-center gap-x-6 gap-y-3 flex-wrap">
                <div 
                    v-for="(item, index) in dayStatistics.by_work_type" 
                    :key="index" 
                    class="day_statistics_item"
                    @mouseenter="hoverIndex = index"
                    @mouseleave="hoverIndex = null">
                    <a-badge :color="item.work_type_color" class="stat_badge mr-2" />
                    <span class="opacity-80">{{ item.work_type_name }} ({{ item.quantity_percentage }}%)</span><span class="ml-2 font-semibold">{{ secondsFormat(item.duration) }}</span>
                </div>
            </div>
        </div>
    </transition>
</template>

<script>
import { secondsFormat } from '@/utils/utils.js'
export default {
    props: {
        storeKey: {
            type: String,
            required: true
        }
    },
    computed: {
        dayStatistics() {
            return this.$store.state.workplan.day_statistics?.[this.storeKey]?.data || null
        },
        showStatistics() {
            return this.dayStatistics?.total_quantity_fact || false
        }
    },
    data() {
        return {
            hoverIndex: null
        }
    },
    methods: {
        secondsFormat
    },
    mounted() {
        this.$store.dispatch('workplan/getDayStatistics', { storeKey: this.storeKey })
    }
}
</script>

<style lang="scss" scoped>
.slide-fade-enter-active {
  transition: all .3s ease;
}
.slide-fade-leave-active {
  transition: all .3s cubic-bezier(1.0, 0.5, 0.8, 1.0);
}
.slide-fade-enter, .slide-fade-leave-to{
  transform: translateY(-10px);
  opacity: 0;
}
.day_progress {
    display: flex;
    height: 12px;
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 10px;
    &__segment {
        height: 100%;
        transition: all .25s ease;
        &.active {
            opacity: 0.6;
        }
    }
}
.day_statistics_item {
    cursor: default;
    font-size: 13px;
}
.day_statistics{
    margin-bottom: 20px;
    .stat_badge{
        &::v-deep{
            .ant-badge-status-text{
                display: none;
            }
        }
    }
}
</style>