<template>
    <div
        class="add_event_meeting_card"
        :title="item.name"
        @click="$emit('open')">
        <div class="add_event_meeting_card__head">
            <div class="add_event_meeting_card__title">
                {{ item.name }}
            </div>
            <div class="add_event_meeting_card__status">
                <Status :status="item.status" />
            </div>
        </div>
        <div v-if="formattedDate" class="add_event_meeting_card__date">
            {{ formattedDate }}
            <template v-if="formattedDuration">
                - {{ formattedDuration }}
            </template>
        </div>
    </div>
</template>

<script>
import { durationFormat } from '@apps/vue2MeetingComponent/utils/index.js'

export default {
    name: 'AddEventMeetingCard',
    components: {
        Status: () => import('@apps/vue2MeetingComponent/components/Status.vue')
    },
    props: {
        item: {
            type: Object,
            required: true
        }
    },
    computed: {
        formattedDate() {
            if (!this.item?.date_begin) return ''

            return this.$t('meeting.formated_start_date', {
                date: this.$moment(this.item.date_begin).format('DD.MM.YYYY'),
                time: this.$moment(this.item.date_begin).format('HH:mm')
            })
        },
        formattedDuration() {
            if (this.item?.duration === null || this.item?.duration === undefined) return ''

            try {
                return durationFormat(this.item.duration)
            } catch(error) {
                return ''
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.add_event_meeting_card{
    padding: 12px;
    background: #fff;
    border: 1px solid #e6e9f2;
    border-radius: var(--borderRadius);
    cursor: pointer;
    display: flex;
    flex-direction: column;
    gap: 8px;
    line-height: 1;

    &:hover{
        .add_event_meeting_card__title{
            color: var(--blue);
        }
    }

    &__head{
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        align-items: center;
        column-gap: 12px;
        margin: 0;
    }

    &__title{
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        font-weight: 500;
        font-size: 14px;
        line-height: 1.4;
        margin: 0;
    }

    &__status{
        display: flex;
        align-items: center;
        justify-content: flex-end;
        width: fit-content;
        margin: 0;
    }

    &__date{
        font-size: 13px;
        line-height: 1.4;
        color: rgba(0, 0, 0, .65);
        margin: 0;
    }
}
</style>
