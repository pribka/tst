<template>
    <div
        class="chat_message"
        :class="[alignRight && 'is_support', message.reply && 'is_reply']">

        <!-- Иконка/аватар слева показываем только в режиме сотрудника -->
        <div v-if="showLeftIcon" class="mr-2">
            <template v-if="message.channel.code === 'internal'">
                <a-avatar
                    :src="message.author && message.author.avatar ? message.author.avatar.path : null"
                    icon="user"
                    :size="24" />
            </template>

            <template v-if="message.channel.icon && message.channel.code !== 'internal'">
                <a-avatar
                    v-if="isSVG(message.channel.icon)"
                    :src="require(`@/assets/svg/${message.channel.icon}`)"
                    :size="24" />
                <a-avatar
                    v-else
                    :size="24">
                    <i class="fi" :class="message.channel.icon" />
                </a-avatar>
            </template>
        </div>

        <div>
            <div class="chat_message__bubble" :class="[alignRight && 'chat_message_is_support']">
                <div class="message_header flex items-center">
                    <div class="user_name text-xs flex item-center font-semibold">
                        <span class="mr-2">{{ authorLabel }}</span>
                    </div>

                    <div class="message_date">
                        {{ formattedDate }}
                    </div>
                </div>

                <div v-if="message.reply" class="message_reply">
                    <div class="message_reply__label">{{ $t('helpdesk.reply_to_message') }}:</div>
                    <TextViewer
                        :body="message.reply.text"
                        collapsible
                        toggleButtonColor="#416ce9"
                        overlayColor="#e8ecfa" />
                </div>

                <TextViewer v-if="message.text" class="message_text" :body="message.text" />

                <div v-if="audioFilesList && audioFilesList.length" class="mt-2">
                    <AudioMessage
                        v-for="audio in audioFilesList"
                        :key="audio.id"
                        :audio="audio"
                        :onLoaded="onAudioLoaded"
                        :onPlayStart="onAudioPlay" />
                </div>

                <div v-if="videoFilesList && videoFilesList.length" class="mt-2">
                    <VideoMessage
                        v-for="video in videoFilesList"
                        :key="video.id"
                        :video="video"
                        :onLoaded="onVideoLoaded"
                        :onPlayStart="onVideoPlay" />
                </div>

                <div v-if="filesList && filesList.length" class="mt-2 flex flex-wrap">
                    <MessageFile
                        v-for="file in filesList"
                        :key="file.id"
                        :file="file"
                        :id="message.id" />
                </div>
            </div>

            <div v-if="isActive" class="flex items-center gap-3 mt-2">
                <div v-if="showReplyButton" class="message_btn" @click="setReplace(message)">
                    {{ $t('helpdesk.reply_to_message') }}
                </div>

                <!-- Добавление задачи только для сотрудника -->
                <div v-if="showTaskButton" class="message_btn" @click="addTask()">
                    {{ $t('helpdesk.add_task') }}
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { mapState } from 'vuex'
import { audioFormats, videoFormats } from '../../../../../utils/utils.js'

export default {
    components: {
        MessageFile: () => import('../../../../MessageFile.vue'),
        AudioMessage: () => import('../../../../AudioMessage.vue'),
        VideoMessage: () => import('../../../../VideoMessage.vue'),
        TextViewer: () => import('@apps/CKEditor/TextViewer.vue')
    },

    props: {
        message: { type: Object, required: true },
        ticket: { type: Object, required: true },
        setReplace: { type: Function, default: () => {} },
        isActive: { type: Boolean, default: false },
        actions: { type: Object, default: () => null },
        onAudioLoaded: { type: Function, default: () => {} },
        onAudioPlay: { type: Function, default: () => {} },
        onVideoLoaded: { type: Function, default: () => {} },
        onVideoPlay: { type: Function, default: () => {} },
    },

    computed: {
        ...mapState({
            user: state => state.user.user,
        }),

        // ticketView = сотрудник, requestView = клиент
        isClientView() {
            const q = this.$route?.query || {}
            if (q.ticketView) return false
            if (q.requestView) return true
            return false
        },

        isActions() {
            return this.actions?.create_message
        },

        isSupport() {
            return this.message.is_help_desk
        },

        // ВАЖНО: класс is_support (justify-content:flex-end) используем по-разному:
        // - сотрудник: вправо уходят сообщения саппорта (is_help_desk=true)
        // - клиент: вправо уходят "мои" сообщения (is_help_desk=false)
        alignRight() {
            return this.isClientView ? !this.isSupport : this.isSupport
        },

        showLeftIcon() {
            // в клиентском режиме не показываем иконки/аватар слева
            return !this.isClientView && !this.isSupport && this.message.channel && this.message.channel.icon
        },

        authorLabel() {
            // клиент: для своих сообщений пишем "Ваше сообщение"
            if (this.isClientView && !this.isSupport) {
                return this.$t('helpdesk.your_message')
            }

            // сотрудник (и саппорт-сообщения на клиенте): показываем автора/контактное лицо
            if (this.message.author) return this.message.author.full_name

            if (this.ticket?.contact_person?.name) return this.ticket.contact_person.name

            return this.ticket?.channel ? this.ticket.channel.name : this.$t('helpdesk.contact_person')
        },

        showReplyButton() {
            return this.isActive && this.isActions
        },

        showTaskButton() {
            // задачи только для сотрудника
            return this.isActive && !this.isClientView
        },

        formattedDate() {
            const msgDate = this.$moment(this.message.created_at)
            const now = this.$moment()

            if (msgDate.isSame(now, 'day')) {
                return `${this.$t('helpdesk.today_at')} ${msgDate.format('HH:mm')}`
            } else if (msgDate.isSame(now.clone().subtract(1, 'day'), 'day')) {
                return `${this.$t('helpdesk.yesterday')} ${msgDate.format('HH:mm')}`
            } else {
                return msgDate.format('DD.MM.YYYY')
            }
        },

        audioFilesList() {
            if (this.message.attachments?.length) {
                return this.message.attachments.filter(f =>
                    audioFormats.some(ext => f.extension.includes(ext))
                )
            }
            return []
        },

        videoFilesList() {
            if (this.message.attachments?.length) {
                return this.message.attachments.filter(f =>
                    videoFormats.some(ext => f.extension.includes(ext))
                )
            }
            return []
        },

        filesList() {
            if (this.message.attachments?.length) {
                return this.message.attachments.filter(f =>
                    ![...audioFormats, ...videoFormats].some(ext => f.extension.includes(ext))
                )
            }
            return []
        }
    },

    methods: {
        isSVG(icon) {
            return icon.endsWith('.svg')
        },

        addTask() {
            // защита: если вдруг вызвали в клиентском режиме
            if (this.isClientView) return

            const form = {
                name: this.ticket.name,
                description: this.message.text,
                reason: this.ticket.id,
            }

            if (this.ticket.priority) form.priority = Number(this.ticket.priority.code)
            if (this.ticket.specialist) form.operator = this.ticket.specialist
            if (this.ticket.visors?.length) form.visors = this.ticket.visors
            else form.visors = []

            if (this.message.attachments?.length) form.attachments = this.message.attachments

            if (this.ticket.dead_line) {
                form.dead_line = this.$moment(this.ticket.dead_line)
                    .hour(18)
                    .minute(0)
                    .second(0)
                    .millisecond(0)
            } else {
                form.dead_line = null
            }

            const pageName = `tasks.TaskModel.Tickets_${this.ticket.id}`
            form.create_handler = pageName

            this.$store.commit('task/SET_TASK_TYPE', 'task')
            this.$store.commit('task/SET_PAGE_NAME', { pageName })
            eventBus.$emit('add_task_modal_watch', { type: 'add_task', data: form })
        },
    }
}
</script>

<style lang="scss" scoped>
.message_reply{
    background: #e8ecfa;
    padding: 10px;
    border-radius: 8px;
    margin-bottom: 10px;
    &__label{
        font-size: 10px;
        line-height: 10px;
        margin-bottom: 5px;
        color: #888888;
    }
    .message_text{
        font-size: 14px;
        word-break: break-word;
        line-height: 22px;
    }
}
.chat_message{
    padding: 20px;
    display: flex;
    &::v-deep{
        .ant-avatar{
            background: #fff;
        }
    }
    .message_btn{
        color: #888888;
        cursor: pointer;
        font-size: 12px;
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
        line-height: 16px;
        &:hover{
            color: var(--blue);
        }
    }
    &.is_support{
        justify-content: flex-end;
    }
    &__bubble{
        background: #fff;
        border-radius: 8px;
        padding: 15px;
        max-width: 800px;
        min-width: 220px;
        .message_date{
            color: #888888;
        }
        .message_header{
            font-size: 12px;
            margin-bottom: 8px;
        }
        .message_text{
            font-size: 14px;
            word-break: break-word;
            line-height: 22px;
        }
    }
}
.chat_message_is_support{
    background-color: var(--blue);
    .message_text{
        color: white;
    }
    .user_name{
        color: white;
    }
    .message_date{
        color: white;
    }
}
</style>
