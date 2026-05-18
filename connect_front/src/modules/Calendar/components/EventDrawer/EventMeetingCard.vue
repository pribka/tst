<template>
    <div
        class="event_meeting_card"
        :class="[
            isMobile && 'is_mobile',
            borderMode && 'event_meeting_card--border',
            singleLineTitle && 'event_meeting_card--single-line-title'
        ]"
        @click="$emit('open')">
        <div class="event_meeting_card__head">
            <div class="event_meeting_card__title" :title="item.name">
                {{ item.name }}
            </div>
            <div class="event_meeting_card__status">
                <Status :status="item.status" />
            </div>
        </div>
        <div v-if="formattedDate" class="event_meeting_card__date">
            {{ formattedDate }}
            <template v-if="formattedDuration">
                - {{ formattedDuration }}
            </template>
        </div>
        <div v-if="showJoinButton || showCopyButton" class="event_meeting_card__actions">
            <a-button
                v-if="showJoinButton"
                block
                icon="fi-rr-video-camera-alt"
                flaticon
                :loading="joinLoading"
                type="flat_primary"
                @click.stop="$emit('join')">
                {{ joinButtonText }}
            </a-button>
            <a-button
                v-if="showCopyButton"
                icon="fi-rr-link-alt"
                flaticon
                v-tippy
                :content="$t('copy_link')"
                type="flat_primary"
                @click.stop="$emit('copy')" />
        </div>
    </div>
</template>

<script>
import { mapState } from 'vuex'
import { durationFormat } from '@apps/vue2MeetingComponent/utils/index.js'

export default {
    name: 'EventMeetingCard',
    components: {
        Status: () => import('@apps/vue2MeetingComponent/components/Status.vue')
    },
    props: {
        item: {
            type: Object,
            required: true
        },
        joinLoading: {
            type: Boolean,
            default: false
        },
        joinButtonText: {
            type: String,
            default: ''
        },
        showJoinButton: {
            type: Boolean,
            default: false
        },
        showCopyButton: {
            type: Boolean,
            default: false
        },
        borderMode: {
            type: Boolean,
            default: false
        },
        singleLineTitle: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        ...mapState({
            isMobile: state => state.isMobile
        }),
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
.event_meeting_card{
    padding: 12px;
    background: #fff;
    border-radius: var(--borderRadius);
    cursor: pointer;
    transition: .2s ease;
    user-select: none;

    &:hover{
        .event_meeting_card__title{
            color: var(--blue);
        }
    }

    &.is_mobile{
        background: #fff;
    }

    &--border{
        border: 1px solid #e6e9f2;
    }

    &--single-line-title{
        .event_meeting_card__head{
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            align-items: center;
            column-gap: 12px;
            margin-bottom: 8px;
        }

        .event_meeting_card__title{
            display: block;
            min-width: 0;
            white-space: nowrap;
            text-overflow: ellipsis;
            max-height: none;
        }

        .event_meeting_card__date{
            margin-top: 0;
        }
    }

    &__head{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
    }

    &__title{
        font-weight: 500;
        font-size: 14px;
        line-height: 1.4;
        display: block;
        max-height: 2.8em;
        overflow: hidden;
        word-break: break-word;
    }

    &__date{
        margin-top: 8px;
        font-size: 13px;
        color: rgba(0, 0, 0, .65);
    }

    &__status{
        display: flex;
        align-items: center;
        flex-shrink: 0;
        width: fit-content;
        max-width: fit-content;
    }

    &__actions{
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 12px;
    }
}
</style>
