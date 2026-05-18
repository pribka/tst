<template>
    <div class="event_card">
        <div class="event_card__name mb-2 truncate" :title="item.name">
            <span
                class="event_color"
                :style="{ background: item.color || '#96a3b0' }" />
            {{ item.name }}
        </div>
        <div class="mb-2 text_row">
            <i class="fi fi-rr-calendar mr-2" />
            {{ eventDate }}
        </div>
        <div class="flex items-center">
            <a-button
                type="primary"
                ghost
                size="small"
                @click="selectFunction(item)">
                {{ $t('dashboard.select') }}
            </a-button>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        item: {
            type: Object,
            required: true
        },
        selectFunction: {
            type: Function,
            required: true
        }
    },
    computed: {
        eventDate() {
            if(!this.item)
                return ''
            if(this.item.all_day)
                return `${this.$moment(this.item.start_at).format('DD.MM.YYYY')} (${this.$t('calendar.all_day')})`

            const sameDay = this.$moment(this.item.start_at).format('DD.MM.YYYY') === this.$moment(this.item.end_at).format('DD.MM.YYYY')
            if(sameDay)
                return `${this.$moment(this.item.start_at).format('DD.MM.YYYY HH:mm')} - ${this.$moment(this.item.end_at).format('HH:mm')}`

            return `${this.$moment(this.item.start_at).format('DD.MM.YYYY HH:mm')} - ${this.$moment(this.item.end_at).format('DD.MM.YYYY HH:mm')}`
        }
    }
}
</script>

<style lang="scss" scoped>
.event_card{
    padding: 12px;
    font-size: 14px;
    font-variant: tabular-nums;
    line-height: 1.5;
    font-feature-settings: 'tnum';
    background: #fff;
    border-radius: var(--borderRadius);
    margin-bottom: 10px;
    border: 1px solid var(--borderColor);
}
.event_card__name{
    display: flex;
    align-items: center;
    gap: 8px;
    color: #4777ff;
    font-weight: 500;
}
.event_color{
    width: 10px;
    height: 10px;
    border-radius: 50%;
    display: inline-block;
    flex-shrink: 0;
}
.text_row{
    font-size: 13px;
    line-height: 15px;
    color: #656565;
}
</style>
