<template>
    <transition name="slide-fade">
        <div v-if="message.edit" class="flex items-center edit_message_wrapper px-2 lg:px-4 py-1 justify-between">
            <div class="flex items-center">
                <div class="mr-3 blue_color text-lg">
                    <i class="fi fi-rr-edit" />
                </div>

                <div>
                    <div class="flex items-center">
                        {{ $t('chat.message_edit') }}
                    </div>

                    <div v-if="message.share" class="flex items-center mt-1 gap-2">
                        <a-button
                            type="flat_primary"
                            icon="fi-rr-trash"
                            flaticon
                            size="small"
                            @click="clearShare()">
                            {{ clearShareLabel }}
                        </a-button>
                    </div>

                    <EditAttachments
                        v-if="message.attachments && message.attachments.length"
                        class="mt-2"
                        :message="message"
                        :activeChat="activeChat" />
                </div>
            </div>

            <div>
                <a-button
                    @click="closeEdit()"
                    type="ui"
                    ghost
                    style="max-width: 36px;padding: 0px;"
                    shape="circle"
                    flaticon
                    size="large"
                    icon="fi-rr-circle-xmark" />
            </div>
        </div>
    </transition>
</template>

<script>
export default {
    components: {
        EditAttachments: () => import('./EditAttachments.vue')
    },
    props: {
        message: {
            type: Object,
            required: true
        },
        closeEdit: {
            type: Function,
            default: () => {}
        },
        activeChat: {
            type: Object,
            required: true
        }
    },
    computed: {
        clearShareLabel() {
            const share = this.message?.share
            if (!share) return this.$t('chat.clear_object')

            const widget = share.shareWidget
            const type = share.type

            if (widget === 'link') return this.$t('chat.clear_related_link')

            const map = {
                'meetings.PlannedMeetingModel': 'chat.clear_related_meeting',
                'workgroups.WorkGroupModel': 'chat.clear_related_team',
                'workgroups.WorkgroupModel': 'chat.clear_related_team',
                'tasks.TaskModel': 'chat.clear_related_task',
                'files': 'chat.clear_related_file',
                'common.File': 'chat.clear_related_file',
                'comments.CommentModel': 'chat.clear_related_comment',
                'comments': 'chat.clear_related_comment',
                'tasks.TaskSprintModel': 'chat.clear_related_sprint',
                'crm.GoodsOrderModel': 'chat.clear_related_order',
                'bpms_common.NewsModel': 'chat.clear_related_news',
                'event_calendar.EventCalendarModel': 'chat.clear_related_event',
                'tickets.TicketModel': 'chat.clear_related_ticket',
                'help_desk.HelpDeskTicketModel': 'chat.clear_related_ticket'
            }

            return this.$t(map[type] || 'chat.clear_related_object')
        }
    },
    methods: {
        clearShare() {
            this.$store.commit('chat/CHANGE_CHAT_MESSAGE_BY_KEY', {
                id: this.activeChat.chat_uid,
                value: null,
                key: 'share'
            })
        }
    }
}
</script>

<style lang="scss" scoped>
.edit_message_wrapper{
    min-height: 50px;
    width: 100%;
    border-bottom: 1px solid var(--border2);
}
.slide-fade-enter-active {
  transition: all .3s ease;
}
.slide-fade-leave-active {
  transition: all .3s cubic-bezier(1.0, 0.5, 0.8, 1.0);
}
.slide-fade-enter, .slide-fade-leave-to{
  transform: translateY(10px);
  opacity: 0;
}
</style>