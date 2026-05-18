<template>
    <div
        class="attach_meeting_card"
        :class="selected && 'attach_meeting_card--selected'"
        :title="item.name"
        @click="$emit('select', item)">
        <div class="attach_meeting_card__head">
            <div class="attach_meeting_card__title_wrap">
                <div class="attach_meeting_card__title">
                    {{ item.name }}
                </div>
                <div v-if="formattedDate" class="attach_meeting_card__date">
                    {{ formattedDate }}
                    <template v-if="formattedDuration">
                        - {{ formattedDuration }}
                    </template>
                </div>
            </div>
            <a-radio :checked="selected" />
        </div>
        <div class="attach_meeting_card__meta">
            <Status :status="item.status" />
        </div>
    </div>
</template>

<script>
import { durationFormat } from '@apps/vue2MeetingComponent/utils/index.js'

export default {
    name: 'AttachMeetingCard',
    components: {
        Status: () => import('@apps/vue2MeetingComponent/components/Status.vue')
    },
    props: {
        item: {
            type: Object,
            required: true
        },
        selected: {
            type: Boolean,
            default: false
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
.attach_meeting_card{
    padding: 12px;
    border-radius: var(--borderRadius);
    background: #f7f9fc;
    cursor: pointer;
    transition: .2s ease;

    &:not(:last-child){
        margin-bottom: 10px;
    }

    &--selected{
        background: #f0f5ff;

        .attach_meeting_card__title{
            color: var(--blue);
        }
    }

    &__head{
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 12px;
    }

    &__title_wrap{
        min-width: 0;
        flex: 1;
    }

    &__title{
        font-size: 14px;
        line-height: 1.4;
        font-weight: 500;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        word-break: break-word;
    }

    &__date{
        margin-top: 8px;
        font-size: 13px;
        color: rgba(0, 0, 0, .65);
    }

    &__meta{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        margin-top: 10px;
    }

    ::v-deep .ant-radio-wrapper,
    ::v-deep .ant-radio{
        pointer-events: none;
    }
}
</style>
