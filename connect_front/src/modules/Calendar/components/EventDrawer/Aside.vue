<template>
    <div ref="cl_aside" :class="isMobile && 'mb-5'">
        <div v-if="event.is_finished" class="aside_item">
            <a-tag color="purple">
                {{ $t('calendar.event_finished') }}
            </a-tag>
        </div>
        <div v-if="event.author" class="aside_item">
            <Profiler
                :user="event.author"
                initStatus
                :getPopupContainer="getPopupContainer"
                :subtitle="{ text: $t('calendar.organizer'), class: 'text-xs opacity-60' }" />
        </div>
        <div v-if="eventMembers && eventMembers.length" class="aside_item">
            <div
                v-for="us in eventMembers"
                :key="us.id"
                class="aside_item__user">
                <Profiler
                    :user="us"
                    initStatus
                    :getPopupContainer="getPopupContainer"
                    :subtitle="{ text: $t('calendar.participant'), class: 'text-xs opacity-60' }" />
            </div>
        </div>
        <div v-if="actions && actions.edit" class="aside_item">
            <UserDrawer
                id="calendar_event_members"
                multiple
                buttonMode
                buttonBlock
                buttonType="ui"
                buttonIcon="fi-rr-user-add"
                :buttonText="$t('calendar.invite_employee')"
                :buttonLoading="membersLoading"
                :value="editableMembers"
                @input="onMembersChange" />
        </div>
        <div class="aside_item">
            <div class="label mb-1 flex items-center justify-between gap-3">
                <span class="label_text">{{ $t('calendar.conference') }}</span>
                <span
                    v-if="actions && actions.edit && hasConferenceData"
                    class="meeting_edit_action"
                    @click="openMeetingTypeModal">
                    {{ $t('calendar.change') }}
                </span>
            </div>
            <template v-if="hasConnectMeeting">
                <EventMeetingCard
                    :item="event.meeting"
                    :joinLoading="meetingLoading"
                    :joinButtonText="event.meeting.status === 'ended' ? $t('calendar.start_new_session') : $t('calendar.start_meeting')"
                    :showJoinButton="!!meetingJoinUrl && !event.meeting.is_external"
                    :showCopyButton="!!meetingInviteUrl && !event.meeting.is_external"
                    :borderMode="isMobile"
                    @join="openMeetingInviteModal"
                    @copy="copyMeeting"
                    @open="openMeeting" />
            </template>
            <template v-else-if="externalMeetingRecord">
                <div
                    class="external_meeting_card"
                    @click="openExternalRecord">
                    <div class="external_meeting_card__head">
                        <div class="external_meeting_card__title">
                            {{ $t('calendar.external_meeting_record') }}
                        </div>
                        <a-tag v-if="getStorageProviderLabel(externalMeetingRecord)" color="blue">
                            {{ getStorageProviderLabel(externalMeetingRecord) }}
                        </a-tag>
                    </div>
                    <div class="external_meeting_card__meta">
                        {{ formatExternalRecordDate(externalMeetingRecord.created_at) }}
                    </div>
                    <div class="external_meeting_card__link">
                        {{ externalMeetingRecord.url }}
                    </div>
                </div>
            </template>
            <div v-else class="mt-1">
                <div
                    class="mb-2 cursor-pointer blue_color flex items-center"
                    :content="$t('calendar.attach_meeting_desc')"
                    v-tippy
                    @click="openMeetingTypeModal">
                    <i class="fi fi-rr-share-square mr-1" />
                    {{ $t('calendar.attach_meeting') }}
                </div>
                <a-button 
                    v-if="actions && actions.edit"
                    block 
                    icon="fi-rr-video-camera-alt"
                    flaticon
                    :loading="loading"
                    type="flat_primary"
                    @click="createMeetingHandler()">
                    {{ $t('calendar.create_meeting') }}
                </a-button>
            </div>
        </div>
        <MeetingInviteModal
            :visible="inviteModalVisible"
            :users="inviteUsers"
            :loading="meetingLoading"
            @cancel="inviteModalVisible = false"
            @invite="inviteAndStartMeeting" />
        <AttachMeetingDrawer
            ref="attachMeetingDrawer"
            :eventId="event.id"
            :currentMeetingId="event.meeting?.id || ''"
            @attached="refreshEventDetails" />
        <a-modal
            :visible="meetingTypeModalVisible"
            :title="$t('calendar.meeting_type_modal_title')"
            :footer="null"
            :width="400"
            @cancel="closeMeetingTypeModal">
            <div class="meeting_type_options">
                <a-button
                    block
                    type="primary"
                    icon="fi-rr-share-square"
                    flaticon
                    @click="selectMeetingType('connect')">
                    {{ $t('calendar.meeting_type_connect') }}
                </a-button>
                <a-button
                    block
                    icon="fi-rr-video-camera-alt"
                    flaticon
                    @click="selectMeetingType('external')">
                    {{ $t('calendar.meeting_type_external') }}
                </a-button>
            </div>
        </a-modal>
        <a-modal
            :visible="externalMeetingModalVisible"
            :title="externalMeetingRecord ? $t('calendar.change') : $t('calendar.external_meeting_add')"
            @cancel="closeExternalMeetingModal">
            <a-form-model layout="vertical">
                <a-form-model-item :label="$t('calendar.external_meeting_source_label')">
                    <a-radio-group v-model="externalMeetingForm.source" button-style="solid">
                        <a-radio-button value="url">
                            {{ $t('calendar.external_meeting_source_url') }}
                        </a-radio-button>
                        <a-radio-button value="file">
                            {{ $t('calendar.external_meeting_source_file') }}
                        </a-radio-button>
                    </a-radio-group>
                </a-form-model-item>
                <a-form-model-item
                    v-if="externalMeetingForm.source === 'url'"
                    :label="$t('calendar.external_meeting_link_label')">
                    <a-input v-model="externalMeetingForm.url" placeholder="https://" />
                </a-form-model-item>
                <a-form-model-item
                    v-if="externalMeetingForm.source === 'url'"
                    :label="$t('calendar.external_meeting_storage_label')">
                    <a-select
                        v-model="externalMeetingForm.storage_provider"
                        :getPopupContainer="getModalPopupContainer">
                        <a-select-option
                            v-for="option in externalStorageOptions"
                            :key="option.value"
                            :value="option.value">
                            {{ option.label }}
                        </a-select-option>
                    </a-select>
                </a-form-model-item>
                <a-form-model-item
                    v-if="externalMeetingForm.source === 'file'"
                    :label="$t('calendar.external_meeting_pick_file')">
                    <input
                        ref="externalMeetingFileInput"
                        type="file"
                        class="external-meeting-file-input"
                        @change="onExternalMeetingFileChange" />
                    <div class="external-meeting-file-picker">
                        <a-button
                            icon="fi-rr-upload"
                            flaticon
                            :loading="externalMeetingFileUploading"
                            @click="$refs.externalMeetingFileInput && $refs.externalMeetingFileInput.click()">
                            {{ $t('calendar.external_meeting_pick_file') }}
                        </a-button>
                        <span v-if="externalMeetingFileName" class="external-meeting-file-picker__name">
                            {{ externalMeetingFileName }}
                        </span>
                    </div>
                </a-form-model-item>
            </a-form-model>
            <template slot="footer">
                <div
                    class="external-meeting-modal-footer"
                    :class="{ 'external-meeting-modal-footer--mobile': isMobile }">
                    <a-button
                        class="external-meeting-modal-footer__cancel"
                        type="ui_ghost"
                        :block="isMobile"
                        @click="closeExternalMeetingModal">
                        {{ $t('calendar.confirm_cancel') }}
                    </a-button>
                    <a-button
                        class="external-meeting-modal-footer__submit"
                        type="primary"
                        :block="isMobile"
                        :loading="externalMeetingSaving"
                        @click="submitExternalMeeting">
                        {{ $t('calendar.save') }}
                    </a-button>
                </div>
            </template>
        </a-modal>
        <div v-if="event.calendar" class="aside_item">
            <div class="label">
                {{ $t('calendar.calendar_label') }}
            </div>
            <div class="value flex items-center">
                <a-badge :color="event.calendar.color" /> {{ event.calendar.name }}
            </div>
        </div>
        <div v-if="event.address" class="aside_item">
            <div class="label">
                {{ $t('calendar.place') }}
            </div>
            <div class="value">
                {{ event.address }}
            </div>
        </div>
        <div v-if="event.event_type" class="aside_item">
            <div class="label">
                {{ $t('calendar.type') }}
            </div>
            <div class="value">
                {{ event.event_type.name }}
            </div>
        </div>
        <div v-if="event.privacy" class="aside_item">
            <div class="label">
                {{ $t('calendar.privacy') }}
            </div>
            <div class="value">
                {{ event.privacy.name }}
            </div>
        </div>
        <div v-if="event.calendar && event.calendar.related_object" class="aside_item">
            <div class="label">
                {{ $t('calendar.related_object') }}
            </div>
            <div class="value">
                <a :href="event.calendar.related_object.frontend_route" target="_blank">
                    {{ event.calendar.related_object.name || event.calendar.related_object.title }}
                </a>
            </div>
        </div>
        <div v-if="event.notify_at" class="aside_item">
            <div class="label">
                {{ $t('calendar.reminder') }}
            </div>
            <div class="value">
                {{ notifyMin }}
            </div>
        </div>
    </div>
</template>

<script>
import { declOfNum } from '@/utils/utils.js'
import { errorHandler } from '@/utils/index.js'
import eventBus from '@/utils/eventBus'
export default {
    props: {
        event: {
            type: Object,
            required: true
        },
        actions: {
            type: Object,
            default: () => null
        },
        createMeeting: {
            type: Function,
            default: () => {}
        },
        toggleMeetingStatus: {
            type: Function,
            default: () => {}
        },
        refreshEventDetails: {
            type: Function,
            default: async () => null
        }
    },
    computed: {
        notifyMin() {
            const notify = this.$moment(this.event.start_at).diff(this.event.notify_at, 'minutes')
            const minuteWord = declOfNum(notify, [this.$t('calendar.minutes'), this.$t('calendar.minutes'), this.$t('calendar.minutes')])
            return this.$t('calendar.notify_template', { min: notify, minute_word: minuteWord })
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        currentUser() {
            return this.$store.state.user.user
        },
        eventMembers() {
            if(!this.event.members?.length)
                return []
            return this.event.members.filter(f => f.id !== this.event.author?.id)
        },
        inviteUsers() {
            const list = []
            const pushUser = user => {
                if (user && user.id) list.push(user)
            }

            pushUser(this.event?.author)

            if (Array.isArray(this.event?.members)) {
                this.event.members.forEach(pushUser)
            }

            const uniq = new Map()
            list.forEach(u => {
                const key = String(u.id)
                if (!uniq.has(key)) uniq.set(key, u)
            })

            const currentUserId = this.currentUser?.id

            return Array
                .from(uniq.values())
                .filter(u => String(u.id) !== String(currentUserId))
        },
        hasMeeting() {
            return !!(this.event?.meeting && Object.keys(this.event.meeting).length)
        },
        hasConnectMeeting() {
            return this.hasMeeting && !this.event?.meeting?.is_external
        },
        hasConferenceData() {
            return this.hasConnectMeeting || !!this.externalMeetingRecord || !!this.event?.meeting?.is_external
        },
        meetingJoinUrl() {
            return this.event?.meeting?.target || this.event?.meeting?.url || ''
        },
        meetingInviteUrl() {
            return this.event?.meeting?.invite_link || this.event?.meeting?.url_external || ''
        },
        externalMeetingRecords() {
            if (!Array.isArray(this.event?.external_meeting_records)) {
                return []
            }
            return this.event.external_meeting_records
        },
        externalMeetingRecord() {
            return this.externalMeetingRecords[0] || null
        },
        externalMeetingFileName() {
            const file = this.externalMeetingForm.record_file
            if (!file) return ''
            return file.original_name || file.name || file.title || file.path || ''
        }
    },
    components: {
        UserDrawer: () => import('@apps/DrawerSelect/index.vue'),
        EventMeetingCard: () => import('./EventMeetingCard.vue'),
        MeetingInviteModal: () => import('./MeetingInviteModal.vue'),
        AttachMeetingDrawer: () => import('./AttachMeetingDrawer.vue')
    },
    data() {
        return {
            loading: false,
            meetingLoading: false,
            inviteModalVisible: false,
            membersLoading: false,
            editableMembers: [],
            pendingMembers: null,
            meetingTypeModalVisible: false,
            externalMeetingModalVisible: false,
            externalMeetingSaving: false,
            externalMeetingFileUploading: false,
            externalMeetingForm: {
                source: 'url',
                url: '',
                storage_provider: 'google_drive',
                record_file: null
            },
            externalStorageOptions: [
                { value: 'google_drive', label: 'Google Drive' },
                { value: 'nextcloud', label: 'Nextcloud' }
            ]
        }
    },
    watch: {
        event: {
            immediate: true,
            deep: true,
            handler() {
                this.syncEditableMembers()
            }
        }
    },
    methods: {
        syncEditableMembers() {
            this.editableMembers = Array.isArray(this.event?.members)
                ? [...this.event.members]
                : []
        },
        onMembersChange(users = []) {
            this.editableMembers = [...users]
            this.pendingMembers = [...users]
            this.updateMembersQueue()
        },
        async updateMembersQueue() {
            if (this.membersLoading || !this.pendingMembers) return

            this.membersLoading = true
            try {
                while (this.pendingMembers) {
                    const members = [...this.pendingMembers]
                    this.pendingMembers = null

                    const payload = {
                        members: members.map(user => user.id)
                    }
                    const { data } = await this.$http.patch(`/calendars/events/${this.event.id}/`, payload)

                    if (data) {
                        await this.refreshEventDetails()
                    }
                }
            } catch(error) {
                this.syncEditableMembers()
                errorHandler({error})
            } finally {
                this.membersLoading = false
            }
        },
        async createMeetingHandler() {
            try {
                this.loading = true
                await this.createMeeting()
            } catch(error) {
                errorHandler({error})
            } finally {
                this.loading = false
            }
        },
        getPopupContainer() {
            return this.$refs[`cl_aside`]
        },
        getModalPopupContainer(triggerNode) {
            return triggerNode?.parentNode || document.body
        },
        startMeeting() {
            this.toggleMeetingStatus('online')
            if (this.meetingJoinUrl) {
                window.open(this.meetingJoinUrl, '_blank')
            }
        },
        openMeetingInviteModal() {
            if (this.event?.meeting?.status === 'online') {
                this.startMeeting()
                return
            }
            // If there is no one to notify except current user, start immediately.
            if (!this.inviteUsers.length) {
                this.startMeeting()
                return
            }
            this.inviteModalVisible = true
        },
        async inviteAndStartMeeting(notifyUserIds = []) {
            try {
                this.meetingLoading = true
                this.inviteModalVisible = false
                const payload = {
                    notify_user_ids: notifyUserIds
                }

                const { data } = await this.$http.post(`meetings/start-related/?related_object=${this.event.id}`, payload)
                if (data?.url || data?.target) {
                    this.event.meeting = data
                    this.toggleMeetingStatus('online')
                    eventBus.$emit('edit_event', this.event)
                    window.open(data.target || data.url, '_blank')
                }
            } catch(error) {
                errorHandler({error})
            } finally {
                this.meetingLoading = false
            }
        },
        copyMeeting() {
            navigator.clipboard.writeText(this.meetingInviteUrl)
                .then(() => {
                    this.$message.success(this.$t('link_succes_copy'))
                })
                .catch(error => {
                    console.error(error)
                    this.$message.error(this.$t('copy_link_error'))
                })
        },
        openMeeting() {
            if (!this.event?.meeting?.id) {
                return
            }
            const query = JSON.parse(JSON.stringify(this.$route.query))
            if(query?.meeting !== this.event.meeting.id) {
                query.meeting = this.event.meeting.id
                this.$router.push({query})
            }
        },
        openMeetingTypeModal() {
            this.meetingTypeModalVisible = true
        },
        closeMeetingTypeModal() {
            this.meetingTypeModalVisible = false
        },
        selectMeetingType(type) {
            this.closeMeetingTypeModal()
            if (type === 'external') {
                this.openExternalMeetingModal()
                return
            }
            this.openAttachMeetingDrawer()
        },
        getStorageProviderLabel(record) {
            if (!record) return ''
            if (record.storage_provider_display) return record.storage_provider_display
            const option = this.externalStorageOptions.find(item => item.value === record.storage_provider)
            return option ? option.label : ''
        },
        formatExternalRecordDate(value) {
            if (!value) return ''
            return this.$moment(value).format('DD.MM.YYYY HH:mm')
        },
        openExternalRecord() {
            this.openMeeting()
        },
        openExternalMeetingModal() {
            const record = this.externalMeetingRecord
            this.externalMeetingForm = {
                source: record?.own_file ? 'file' : 'url',
                url: record?.own_file ? '' : (record?.url || ''),
                storage_provider: record?.storage_provider || 'google_drive',
                record_file: record?.record_file || null
            }
            this.externalMeetingModalVisible = true
        },
        closeExternalMeetingModal() {
            this.externalMeetingModalVisible = false
        },
        async onExternalMeetingFileChange(event) {
            const [file] = event?.target?.files || []
            if (!file) {
                return
            }

            try {
                this.externalMeetingFileUploading = true
                const data = await this.$uploadFile({
                    file,
                    url: '/common/upload/',
                    fieldName: 'upload'
                })
                const uploadedFile = Array.isArray(data) ? data[0] : data
                if (uploadedFile?.id) {
                    this.externalMeetingForm.record_file = uploadedFile
                } else {
                    this.$message.error(this.$t('loading_error'))
                }
            } catch(error) {
                errorHandler({error})
            } finally {
                this.externalMeetingFileUploading = false
                if (this.$refs.externalMeetingFileInput) {
                    this.$refs.externalMeetingFileInput.value = ''
                }
            }
        },
        async submitExternalMeeting() {
            const source = this.externalMeetingForm.source || 'url'
            const url = (this.externalMeetingForm.url || '').trim()
            const storageProvider = this.externalMeetingForm.storage_provider
            const recordFileId = this.externalMeetingForm.record_file?.id || this.externalMeetingForm.record_file

            try {
                this.externalMeetingSaving = true
                const payload = {
                    external_meeting: true
                }

                if (source === 'file') {
                    if (!recordFileId) {
                        this.$message.error(this.$t('calendar.required_field'))
                        return
                    }
                    payload.external_meeting_record_file = recordFileId
                } else {
                    if (!url) {
                        this.$message.error(this.$t('calendar.required_field'))
                        return
                    }
                    if (!storageProvider) {
                        this.$message.error(this.$t('calendar.required_field'))
                        return
                    }
                    payload.external_meeting_url = url
                    payload.external_meeting_storage_provider = storageProvider
                }

                await this.$http.patch(`/calendars/events/${this.event.id}/`, payload)
                await this.refreshEventDetails()
                this.externalMeetingModalVisible = false
                this.$message.success(this.$t('calendar.item_created'))
            } catch(error) {
                errorHandler({error})
            } finally {
                this.externalMeetingSaving = false
            }
        },
        openAttachMeetingDrawer() {
            this.$refs.attachMeetingDrawer.open()
        }
    }
}
</script>

<style lang="scss" scoped>
.aside_item{
    color: #000;
    &:not(:last-child){
        padding-bottom: 15px;
    }
    .label{
        .label_text{
            opacity: 0.6;
        }
    }
    &__user{
        &:not(:last-child){
            margin-bottom: 8px;
        }
    }
}

.meeting_edit_action{
    color: var(--blue);
    cursor: pointer;
    font-size: 14px;
    line-height: 1.4;
}

.meeting_type_options{
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.external_meeting_list{
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.external_meeting_card{
    border: 1px solid #e6e9f2;
    border-radius: var(--borderRadius);
    padding: 10px 12px;
    cursor: pointer;
    transition: .2s ease;

    &:hover{
        border-color: #cfd7e6;
    }

    &__head{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        margin-bottom: 6px;
    }

    &__title{
        font-size: 14px;
        font-weight: 500;
        color: #1f2937;
    }

    &__meta{
        font-size: 12px;
        color: rgba(0, 0, 0, .55);
        margin-bottom: 4px;
    }

    &__link{
        color: var(--blue);
        font-size: 13px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
}

.external-meeting-file-picker {
    display: flex;
    align-items: center;
    gap: 12px;
}

.external-meeting-modal-footer {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 8px;
    width: 100%;
}

.external-meeting-modal-footer--mobile {
    flex-direction: column;
}

.external-meeting-modal-footer--mobile .external-meeting-modal-footer__submit {
    order: 1;
}

.external-meeting-modal-footer--mobile .external-meeting-modal-footer__cancel {
    order: 2;
}

.external-meeting-file-input {
    position: absolute !important;
    width: 1px !important;
    height: 1px !important;
    padding: 0 !important;
    margin: -1px !important;
    overflow: hidden !important;
    clip: rect(0, 0, 0, 0) !important;
    white-space: nowrap !important;
    border: 0 !important;
    opacity: 0 !important;
    pointer-events: none !important;
    appearance: none !important;
    -webkit-appearance: none !important;
}

.external-meeting-file-picker__name {
    font-size: 13px;
    color: rgba(0, 0, 0, .65);
    word-break: break-word;
}
</style>
