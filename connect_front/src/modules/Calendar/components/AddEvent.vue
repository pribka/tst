<template>
    <DrawerTemplate
        class="event_form_drawer"
        :width="drawerWidth"
        :class="isMobile && 'mobile'"
        v-model="visible"
        @afterVisibleChange="afterVisibleChange"
        @close="visible = false">
        <template #title>
            <div class="drawer_title">{{ edit ? $t('calendar.edit_event') : $t('calendar.add_event') }}</div>
        </template>
        <template #rightHeader>
            <HelpButton partCode="calendar" />
        </template>
        <div ref="eventAddBody">
            <a-form-model
                ref="eventForm"
                :model="form"
                :rules="rules">
                <div class="lg:flex lg:items-start">
                    <a-form-model-item ref="name" :label="$t('calendar.event_name')" prop="name" class="w-full mb-2 md:mb-1">
                        <a-input 
                            v-model="form.name" 
                            ref="eventNameInput"
                            size="large" 
                            @pressEnter="onSubmit()" />
                    </a-form-model-item>
                    <a-form-model-item ref="event_type" :label="$t('calendar.event_type')" prop="event_type" class="lg:ml-3 mb-2 md:mb-1">
                        <a-select v-model="form.event_type" size="large" :loading="eventTypeLoader" :getPopupContainer="getPopupContainer" class="event_type_select">
                            <a-select-option v-for="item in eventTypeList" :key="item.id" :value="item.code">
                                {{ item.string_view }}
                            </a-select-option>
                        </a-select>
                    </a-form-model-item>
                </div>
                <a-form-model-item ref="description" :label="$t('calendar.event_description')" prop="description" class="mb-1 md:mb-2">
                    <component
                        :is="ckEditor"
                        :key="edit || visible"
                        v-model="form.description" />
                </a-form-model-item>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-5 gap-y-3 md:gap-y-2 mb-5 md:mb-3">
                    <a-form-model-item ref="start_at" :label="$t('calendar.start_date')" prop="start_at" class="mb-0">
                        <div class="flex items-center">
                            <a-date-picker 
                                v-model="form.start_at" 
                                :allowClear="false" 
                                size="large" 
                                :placeholder="$t('calendar.choose_date')" 
                                format="DD.MM.YYYY"
                                :getCalendarContainer="getPopupContainer"
                                class="w-full"
                                :showToday="false"
                                @change="changeStartAt" />
                            <a-time-picker 
                                v-if="!form.all_day"
                                v-model="form.start_at" 
                                :allowClear="false" 
                                format="HH:mm" 
                                :getPopupContainer="getPopupContainer"
                                :minuteStep="5"
                                size="large" 
                                class="ml-2 time_picker" 
                                :placeholder="$t('calendar.time_placeholder')"
                                @change="changeStartAtTime" />
                        </div>
                    </a-form-model-item>
                    <a-form-model-item ref="end_at" :label="$t('calendar.end_date')" prop="end_at" class="mb-0">
                        <div class="flex items-center">
                            <a-date-picker 
                                v-model="form.end_at" 
                                :allowClear="false" 
                                format="DD.MM.YYYY"
                                size="large" 
                                :getCalendarContainer="getPopupContainer"
                                :placeholder="$t('calendar.choose_date')" 
                                class="w-full"
                                :showToday="false"
                                @change="changeEndAt" />
                            <a-time-picker 
                                v-if="!form.all_day"
                                v-model="form.end_at" 
                                :allowClear="false" 
                                size="large" 
                                :getPopupContainer="getPopupContainer"
                                :minuteStep="5"
                                format="HH:mm" 
                                class="ml-2 time_picker" 
                                :placeholder="$t('calendar.time_placeholder')"
                                @change="changeEndAtTime" />
                        </div>
                    </a-form-model-item>
                    <div class="mt-1 lg:mt-0">
                        <a-checkbox :checked="form.all_day" @change="allDayChange">
                            {{$t('calendar.all_day')}}
                        </a-checkbox>
                    </div>
                </div>
                <div v-if="isMobile && !form.meeting && !form.external_meeting" class="flex items-center mb-3">
                    <a-switch v-model="form.meetingCreate" />
                    <span class="cursor-pointer ml-2" @click="form.meetingCreate = !form.meetingCreate">{{ $t('calendar.create_meeting') }}</span>
                </div>
                <a-form-model-item ref="members" :label="$t('calendar.members')" prop="members" class="mb-2">
                    <UserDrawer
                        id="calendar"
                        :metadata="{ key: 'members', value: form.metadata }"
                        :changeMetadata="changeMetadata"
                        v-model="form.members"
                        multiple
                        inputSize="large"
                        :title="$t('calendar.select_members')" />
                </a-form-model-item>
                <transition name="default-members-slide">
                    <div v-if="showDefaultMembersAction" class="default-members-action">
                        <a-button type="link" icon="fi-rr-user-add" flaticon class="p-0 h-auto" @click="applyDefaultMembers">
                            {{ $t('calendar.fill_default_members') }}
                        </a-button>
                    </div>
                </transition>
                <div class="lg:grid grid-cols-2 gap-5">
                    <a-form-model-item class="w-full mb-2 md:mb-2" ref="address" :label="$t('calendar.address')" prop="address">
                        <a-input v-model="form.address" size="large" />
                    </a-form-model-item>
                    <a-form-model-item class="w-full mb-2 md:mb-2" ref="calendar" :label="$t('calendar.calendar')" prop="calendar">
                        <!--<div v-if="form.related_object" disabled="disabled" class="flex items-center ant-input ant-input-lg cursor-default truncate ant-input-disabled">
                            <a-badge v-if="form.related_object.color" :color="form.related_object.color" /> <span class="truncate">{{ form.related_object.name }}</span>
                        </div>-->
                        <CalendarSelect 
                            selectFirst
                            initLoading
                            v-model="form.calendar" 
                            inputType="defaultInput"
                            storeName="calendar_select"
                            @change="onCalendarChange" />
                    </a-form-model-item>
                </div>
                <div class="lg:grid grid-cols-2 gap-5">
                    <a-form-model-item ref="notify_min" :label="$t('calendar.remind_before')" prop="notify_min" class="mb-2">
                        <div class="flex items-center">
                            <a-select
                                v-model="form.notify_min"
                                size="large" 
                                style="min-width: 200px;"
                                :getPopupContainer="getPopupContainer">
                                <a-select-option
                                    v-for="item in notifyMinOptions"
                                    :key="item.value"
                                    :value="item.value">
                                    {{ item.label }}
                                </a-select-option>
                            </a-select>
                        </div>
                    </a-form-model-item>
                    <a-form-model-item class="w-full mb-2" ref="calprivacyendar" :label="$t('calendar.privacy_settings')" prop="privacy">
                        <a-select v-model="form.privacy" size="large" :getPopupContainer="getPopupContainer" :loading="privacyLoading" class="w-full">
                            <a-select-option v-for="item in privacyList" :key="item.id" :value="item.code">
                                {{ item.string_view }}
                            </a-select-option>
                        </a-select>
                    </a-form-model-item>
                </div>
                <a-form-model-item ref="color" :label="$t('calendar.event_color')" prop="color" class="mb-3">
                    <ColorPicker v-model="form.color" ref="colorPicker" typeList @change="onColorInput" />
                </a-form-model-item>
                <div class="lg:grid grid-cols-2 gap-5">
                    <a-form-model-item class="w-full mb-2" :label="$t('calendar.conference')">
                        <MeetingSelectField
                            v-model="form.meeting"
                            :placeholder="$t('calendar.attach_meeting')" />
                    </a-form-model-item>
                </div>
                <div class="mb-2">
                    <div class="flex items-center">
                        <a-switch v-model="form.external_meeting" />
                        <span class="cursor-pointer ml-2" @click="form.external_meeting = !form.external_meeting">
                            {{ $t('calendar.external_meeting_toggle') }}
                        </span>
                    </div>
                </div>
                <div v-if="form.external_meeting" class="mb-2">
                    <a-form-model-item
                        class="w-full mb-2"
                        :label="$t('calendar.external_meeting_source_label')">
                        <a-radio-group v-model="form.external_meeting_source" size="large" button-style="solid">
                            <a-radio-button value="url">
                                {{ $t('calendar.external_meeting_source_url') }}
                            </a-radio-button>
                            <a-radio-button value="file">
                                {{ $t('calendar.external_meeting_source_file') }}
                            </a-radio-button>
                        </a-radio-group>
                    </a-form-model-item>
                </div>
                <div v-if="form.external_meeting && form.external_meeting_source === 'url'" class="lg:grid grid-cols-2 gap-5">
                    <a-form-model-item
                        class="w-full mb-2"
                        :label="$t('calendar.external_meeting_link_label')">
                        <a-input v-model="form.external_meeting_url" placeholder="https://" size="large" />
                    </a-form-model-item>
                    <a-form-model-item
                        class="w-full mb-2"
                        :label="$t('calendar.external_meeting_storage_label')">
                        <a-select
                            v-model="form.external_meeting_storage_provider"
                            size="large"
                            :getPopupContainer="getPopupContainer">
                            <a-select-option
                                v-for="item in externalStorageOptions"
                                :key="item.value"
                                :value="item.value">
                                {{ item.label }}
                            </a-select-option>
                        </a-select>
                    </a-form-model-item>
                </div>
                <div v-if="form.external_meeting && form.external_meeting_source === 'file'" class="mb-3">
                    <input
                        ref="externalMeetingFileInput"
                        type="file"
                        hidden
                        style="display: none;"
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
                </div>
                <a-form-model-item
                    :label="$t('calendar.files')"
                    class="mb-2"
                    prop="attachments">
                    <FileAttach
                        ref="fileAttach"
                        :attachmentFiles="form.attachments">
                        <template v-slot:openButton>
                            <a-button 
                                flaticon
                                class="mb-2"
                                icon="fi-rr-download">
                                {{$t('calendar.upload_file')}}
                            </a-button>
                        </template>
                    </FileAttach>
                </a-form-model-item>
            </a-form-model>
        </div>
        <template #footer>
            <div class="flex items-center w-full">
                <a-button 
                    type="primary" 
                    :loading="loading"
                    :block="isMobile"
                    class="px-8"
                    size="large"
                    @click="onSubmit()">
                    {{$t('calendar.save')}}
                </a-button>
                <div v-if="!isMobile && !form.meeting && !form.external_meeting" class="flex items-center ml-5">
                    <a-switch v-model="form.meetingCreate" />
                    <span class="cursor-pointer ml-2" @click="form.meetingCreate = !form.meetingCreate">{{ $t('calendar.create_meeting') }}</span>
                </div>
            </div>
        </template>
    </DrawerTemplate>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'
export default {
    components: {
        ColorPicker: () => import('./ColorPicker.vue'),
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue'),
        FileAttach: () => import('@apps/vue2Files/components/FileAttach'),
        UserDrawer: () => import('@apps/DrawerSelect/index.vue'),
        HelpButton: () => import('@apps/Support/components/HelpButton.vue'),
        CalendarSelect: () => import('./CalendarSelect.vue'),
        MeetingSelectField: () => import('./MeetingSelectField.vue'),
        VNodes: {
            functional: true,
            render: (h, ctx) => ctx.props.vnodes
        }
    },
    computed: {
        externalMeetingFileName() {
            const file = this.form.external_meeting_record_file
            if(!file)
                return ''
            return file.original_name || file.name || file.title || file.path || ''
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        drawerWidth() {
            if(this.windowWidth > 800)
                return 800
            else {
                return '100%'
            }
        },
        ckEditor() {
            if(this.visible)
                return () => import('@apps/CKEditor')
            else
                return null
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        notifyMinOptions() {
            return [
                { value: 30, label: this.$t('calendar.reminder_30_minutes') },
                { value: 60, label: this.$t('calendar.reminder_1_hour') },
                { value: 120, label: this.$t('calendar.reminder_2_hours') },
                { value: 180, label: this.$t('calendar.reminder_3_hours') },
                { value: 240, label: this.$t('calendar.reminder_4_hours') },
                { value: 300, label: this.$t('calendar.reminder_5_hours') },
                { value: 1440, label: this.$t('calendar.reminder_1_day') }
            ]
        },
        externalStorageOptions() {
            return [
                { value: 'google_drive', label: 'Google Drive' },
                { value: 'nextcloud', label: 'Nextcloud' }
            ]
        },
    },
    watch: {
        'form.external_meeting'(value) {
            if(value) {
                this.form.meetingCreate = false
            } else {
                this.form.external_meeting_source = 'url'
                this.form.external_meeting_url = ''
                this.form.external_meeting_record_file = null
            }
        },
        'form.external_meeting_source'(value) {
            if(value === 'url') {
                this.form.external_meeting_record_file = null
            }
            if(value === 'file') {
                this.form.external_meeting_url = ''
            }
        }
    },
    data() {
        return {
            visible: false,
            edit: false,
            loading: false,
            externalMeetingFileUploading: false,
            isCustomColor: false,
            page: 1,
            uKey: 'default',
            next: true,
            eventTypeList: [],
            eventTypeLoader: false,
            privacyList: [],
            privacyLoading: false,
            defaultMembers: [],
            showDefaultMembersAction: false,
            pendingProjectId: null,
            selectedDate: false,
            rules: {
                name: [
                    { required: true, message: this.$t('calendar.required_field'), trigger: 'blur' },
                    { max: 255, message: this.$t('calendar.max_255'), trigger: 'blur' }
                ],
                calendar: [
                    { required: true, message: this.$t('calendar.required_field'), trigger: 'blur' }
                ],
                event_type: [
                    { required: true, message: this.$t('calendar.required_field'), trigger: 'blur' }
                ],
                end_at: [
                    { required: true, message: this.$t('calendar.required_field'), trigger: 'blur' }
                ],
                start_at: [
                    { required: true, message: this.$t('calendar.required_field'), trigger: 'blur' }
                ]
            },
            form: {
                metadata: {
                    members: []
                },
                meetingCreate: false,
                address: '',
                attachments: [],
                calendar: null,
                color: '',
                description: '',
                end_at: null,
                event_type: null,
                meeting: null,
                meeting_url: '',
                external_meeting: false,
                external_meeting_source: 'url',
                external_meeting_url: '',
                external_meeting_storage_provider: 'google_drive',
                external_meeting_record_file: null,
                members: [],
                name: '',
                notify_at: null,
                notify_min: 30,
                privacy: null,
                start_at: null,
                all_day: false
            }
        }
    },
    methods: {
        async getDefaultMembers(id) {
            const { data } = await this.$http.get(`/work_groups/workgroups/${id}/get_workgroups_members/`, {
                params: {
                    page: 1,
                    page_size: 10000
                }
            })
            return data?.results?.map(({ member }) => member).filter(Boolean) || []
        },
        async requestDefaultMembers(projectId) {
            try {
                const defaultMembers = await this.getDefaultMembers(projectId)

                if(defaultMembers?.length) {
                    this.defaultMembers = defaultMembers
                    this.showDefaultMembersAction = true
                }
            } catch(error) {
                if(error?.status === 404 || error?.response?.status === 404) {
                    return
                }

                errorHandler({error, show: false})
            }
        },
        applyDefaultMembers() {
            this.form.members = this.defaultMembers
            this.showDefaultMembersAction = false
        },
        onColorInput(value) {
            if(value) {
                this.isCustomColor = true
            } else {
                this.isCustomColor = false
                this.syncColorWithCalendar()
            }
        },
        onCalendarChange() {
            if(this.form.related_object)
                this.$delete(this.form, 'related_object')
            this.syncColorWithCalendar()
            if(this.form.calendar?.color) {
                this.$nextTick(() => {
                    this.$refs.colorPicker.updateColor(this.form.calendar.color)
                })
            }
        },
        syncColorWithCalendar() {
            if(this.isCustomColor)
                return

            let color = null

            if(this.form.related_object && this.form.related_object.id === this.form.calendar?.id && this.form.related_object.color)
                color = this.form.related_object.color
            else {
                if(this.form.calendar?.color)
                    color = this.form.calendar.color
            }
            if(color)
                this.form.color = color
        },
        async fetchMeetingLabel(meetingId) {
            try {
                const { data } = await this.$http.get(`/meetings/${meetingId}/detail/`)
                if (data && this.form.meeting) {
                    this.$set(this.form, 'meeting', { ...data })
                }
            } catch(e) {}
        },
        changeMetadata({key, value}) {
            this.$set(this.form.metadata, key, value)
        },
        getPopupContainer() {
            return this.$refs.eventAddBody
        },
        normalizeNotifyMin(value) {
            const allowedValues = [30, 60, 120, 180, 240, 300, 1440]

            if(allowedValues.includes(Number(value))) {
                return Number(value)
            }

            return 30
        },
        async onExternalMeetingFileChange(event) {
            const [file] = event?.target?.files || []
            if(!file) {
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
                if(uploadedFile?.id) {
                    this.form.external_meeting_record_file = uploadedFile
                } else {
                    this.$message.error(this.$t('loading_error'))
                }
            } catch(error) {
                errorHandler({error})
            } finally {
                this.externalMeetingFileUploading = false
                if(this.$refs.externalMeetingFileInput) {
                    this.$refs.externalMeetingFileInput.value = ''
                }
            }
        },
        onSubmit() {
            this.$refs.eventForm.validate(async valid => {
                if (valid) {
                    try {
                        this.loading = true
                        const formData = JSON.parse(JSON.stringify(this.form))

                        if(formData.members.length) {
                            formData.members = formData.members.map(us => {
                                return us.id
                            })
                        }
                        if(formData.attachments.length) {
                            formData.attachments = formData.attachments.map(fl => {
                                return fl.id
                            })
                        }
                        if(formData.notify_min)
                            formData.notify_at = this.$moment(formData.start_at).add(-formData.notify_min, 'minutes')
                        if(formData.start_at)
                            formData.start_at = this.$moment(formData.start_at).toISOString()
                        if(formData.end_at)
                            formData.end_at = this.$moment(formData.end_at).toISOString()
                        if(formData.calendar)
                            formData.calendar = formData.calendar.id
                        if(formData.related_object?.id) {
                            this.$set(formData, 'calendar', formData.related_object.id)
                            this.$delete(formData, 'related_object')
                        }
                        if(formData.meeting) {
                            if(formData.meeting.id) {
                                formData.meeting = formData.meeting.id
                            } else {
                                delete formData.meeting
                            }
                        }
                        if(formData.external_meeting) {
                            if(formData.external_meeting_source === 'file') {
                                const externalMeetingRecordFileId = formData.external_meeting_record_file?.id || formData.external_meeting_record_file
                                if(!externalMeetingRecordFileId) {
                                    this.$message.warning(this.$t('calendar.required_field'))
                                    this.loading = false
                                    return
                                }
                                formData.external_meeting_record_file = externalMeetingRecordFileId
                                delete formData.external_meeting_url
                                delete formData.external_meeting_storage_provider
                            } else {
                                formData.external_meeting_url = (formData.external_meeting_url || '').trim()
                                if(!formData.external_meeting_url) {
                                    this.$message.warning(this.$t('calendar.required_field'))
                                    this.loading = false
                                    return
                                }
                                if(!formData.external_meeting_storage_provider) {
                                    formData.external_meeting_storage_provider = 'google_drive'
                                }
                                delete formData.external_meeting_record_file
                            }
                            delete formData.external_meeting_source
                        } else {
                            delete formData.external_meeting_url
                            delete formData.external_meeting_storage_provider
                            delete formData.external_meeting_record_file
                            delete formData.external_meeting_source
                            delete formData.external_meeting
                        }

                        if(this.edit) {
                            const { data } = await this.$http.put(`/calendars/events/${formData.id}/`, formData)
                            if(data) {
                                const reqData = {...data}
                                if(this.form.meetingCreate && !formData.external_meeting) {
                                    const mData = await this.$http.post(`/calendars/events/${data.id}/create_meeting/`)
                                    if(mData?.data)
                                        reqData.meeting = mData.data.meeting
                                }
                                this.$message.info(this.$t('calendar.event_updated'))
                                this.visible = false
                                const { id } = formData
                                const query = JSON.parse(JSON.stringify(this.$route.query))
                                if(query.event && Number(query.event) !== id || !query.event) {
                                    query.event = id
                                    this.$router.push({query})
                                }
                                if (this.$store.hasModule('workplan')) {
                                    this.$store.dispatch('workplan/updateItem', {
                                        item: reqData,
                                        list: 'eventList'
                                    })
                                }
                                eventBus.$emit('edit_event', reqData)
                                eventBus.$emit('header_event_update', reqData)
                            }
                        } else {
                            const { data } = await this.$http.post('/calendars/events/', formData)
                            if(data) {
                                const reqData = {...data}
                                if(this.form.meetingCreate && !formData.external_meeting) {
                                    const mData = await this.$http.post(`/calendars/events/${data.id}/create_meeting/`)
                                    if(mData?.data)
                                        reqData.meeting = mData.data.meeting
                                }
                                this.$message.info(this.$t('calendar.event_created'))
                                if (this.$store.hasModule('workplan')) {
                                    this.$store.dispatch('workplan/updateItem', {
                                        item: reqData,
                                        list: 'eventList'
                                    })
                                }
                                eventBus.$emit(`add_event_${this.uKey}`, reqData)
                                eventBus.$emit('header_event_update', reqData)
                                if (this.$store.hasModule('workplan')) {
                                    this.$store.dispatch('workplan/reloadList', {
                                        list: 'eventList'
                                    })
                                }
                                this.visible = false
                            }
                        }
                    } catch(error) {
                        errorHandler({error})
                    } finally {
                        this.loading = false
                    }
                } else {
                    console.log('error submit!!');
                    if(this.isMobile) {
                        this.$message.warning(this.$t('calendar.fill_required_fields'))
                    }
                    return false;
                }
            });
        },
        afterVisibleChange(vis) {
            if(vis) {
                this.getEventTypes()
                this.getEventPrivacy()

                if(!this.edit && !this.selectedDate) {
                    this.form.start_at = this.$moment()
                    this.form.end_at = this.$moment().add(1, 'hours')
                    this.selectedDate = false
                }
                if(!this.edit && this.pendingProjectId) {
                    this.requestDefaultMembers(this.pendingProjectId)
                    this.pendingProjectId = null
                }
            } else {
                eventBus.$emit('add_event_close_drawer')
                if(this.edit) {
                    const { id } = this.form
                    let query = Object.assign({}, this.$route.query)
                    if(query.event && Number(query.event) !== id || !query.event) {
                        query.event = id
                        this.$router.push({query})
                    }
                }

                this.isCustomColor = false
                this.defaultMembers = []
                this.showDefaultMembersAction = false
                this.page = 1
                this.next = true
                this.eventTypeList = []
                this.pendingProjectId = null
                this.selectedDate = false
                this.privacyList = []
                this.edit = false
                this.uKey = 'default'
                this.form = {
                    metadata: {
                        members: []
                    },
                    meetingCreate: false,
                    address: '',
                    attachments: [],
                    calendar: null,
                    color: '',
                    description: '',
                    end_at: null,
                    event_type: null,
                    meeting: null,
                    meeting_url: '',
                    external_meeting: false,
                    external_meeting_source: 'url',
                    external_meeting_url: '',
                    external_meeting_storage_provider: 'google_drive',
                    external_meeting_record_file: null,
                    members: [],
                    name: '',
                    notify_at: null,
                    notify_min: 30,
                    privacy: null,
                    start_at: null,
                    all_day: false
                }
            }
        },
        allDayChange(e) {
            this.form.all_day = e.target.checked
            if(e.target.checked) {
                this.form.start_at = this.$moment(this.form.start_at).set('hour', 0).set('minute', 0).set('second', 0)
                this.form.end_at = this.$moment(this.form.end_at).set('hour', 23).set('minute', 59).set('second', 59)
            } else {
                this.form.start_at = this.$moment(this.form.start_at).set('hour', this.$moment().format('HH')).set('minute', this.$moment().format('mm')).set('second', this.$moment().format('ss'))
                this.form.end_at = this.$moment(this.form.end_at).set('hour', this.$moment().add(1, 'hours').format('HH')).set('minute', this.$moment().format('mm')).set('second', this.$moment().format('ss'))
            }
        },
        changeStartAtTime(e) {
            if(!e || !this.form.end_at) {
                return
            }

            const startAt = this.$moment(e)
            const endAt = this.$moment(this.form.end_at)

            if(startAt.isSameOrAfter(endAt)) {
                this.form.end_at = startAt.clone().add(1, 'hours')
            }
        },
        changeEndAtTime(e) {
            if(!e || !this.form.start_at) {
                return
            }

            const endAt = this.$moment(e)
            const startAt = this.$moment(this.form.start_at)

            if(endAt.isSameOrBefore(startAt)) {
                this.form.start_at = endAt.clone().add(-1, 'hours')
            }
        },
        changeStartAt(e) {
            const eDate = JSON.parse(JSON.stringify(e))
            this.form.end_at = this.$moment(eDate).add(1, 'hours')
        },
        changeEndAt(e) {
            const eDate = JSON.parse(JSON.stringify(e))
            if(this.$moment(eDate).isSameOrBefore(this.form.start_at)) {
                this.form.start_at = this.$moment(eDate).add(-1, 'hours')
            }
        },
        async getEventPrivacy() {
            try {
                this.privacyLoading = true
                const { data } = await this.$http.get('/app_info/select_list/', {
                    params: {
                        model: 'event_calendar.EventCalendarPrivacyModel'
                    }
                })
                if(data) {
                    this.privacyList = data.selectList
                    if(!this.form.privacy) {
                        this.form.privacy = data.selectList[0].code
                    }
                }
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                this.privacyLoading = false
            }
        },
        async getEventTypes() {
            try {
                this.eventTypeLoader = true
                const { data } = await this.$http.get('/app_info/select_list/', {
                    params: {
                        model: 'event_calendar.EventCalendarTypeModel'
                    }
                })
                if(data) {
                    this.eventTypeList = data.selectList
                    if(!this.form.event_type) {
                        this.form.event_type = data.selectList[0].code
                    }
                }
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                this.eventTypeLoader = false
            }
        }
    },
    mounted() {
        eventBus.$on('open_event_form', (startDate = null, endDate = null, event = null, related_object = null, uKey = 'default', nameFocus = false, projectId = null, inject = null) => {
            this.uKey = uKey
            if(event) {
                this.edit = !!event.id
                this.pendingProjectId = null
                const formData = {
                    ...event,
                    end_at: this.$moment(event.end_at),
                    start_at: this.$moment(event.start_at),
                    event_type: event.event_type?.code || null,
                    privacy: event.privacy?.code || null,
                    calendar: event.calendar?.id || null
                }
                const firstExternalRecord = Array.isArray(event.external_meeting_records)
                    ? event.external_meeting_records[0]
                    : null
                formData.external_meeting = !!firstExternalRecord
                formData.external_meeting_source = firstExternalRecord?.own_file ? 'file' : 'url'
                formData.external_meeting_url = firstExternalRecord?.own_file ? '' : (firstExternalRecord?.url || '')
                formData.external_meeting_storage_provider = firstExternalRecord?.storage_provider || 'google_drive'
                formData.external_meeting_record_file = firstExternalRecord?.record_file || null
                if(event.notify_at)
                    formData.notify_min = this.$moment(event.start_at).diff(event.notify_at, 'minutes')
                if(event.privacy)
                    this.privacyList = [{...event.privacy}]
                if(event.event_type)
                    this.eventTypeList = [{...event.event_type}]
                if(event.calendar?.related_object) {
                    formData.related_object = event.calendar
                    formData.calendar = {
                        ...event.calendar,
                        string_view: event.calendar.name
                    }
                } else {
                    if(event.calendar)
                        formData.calendar = {
                            ...event.calendar,
                            string_view: event.calendar.name
                        }
                }
                if(event.meeting?.id && !event.meeting.string_view) {
                    this.fetchMeetingLabel(event.meeting.id)
                }
                if(event.color && event.calendar && event.calendar.color)
                    this.isCustomColor = event.color !== event.calendar.color
                else
                    this.isCustomColor = !!event.color
                if(formData.all_day) {
                    const end = this.$moment(event.end_at)
                    formData.start_at = this.$moment(event.start_at).set('hour', 0).set('minute', 0).set('second', 0).set('second', 0)
                    formData.end_at = this.$moment(end).set('hour', 23).set('minute', 59).set('second', 59).set('millisecond', 59)
                } else {
                    formData.start_at = this.$moment(event.start_at)
                    formData.end_at = this.$moment(event.end_at)
                }

                formData.notify_min = this.normalizeNotifyMin(formData.notify_min)

                this.form = JSON.parse(JSON.stringify(formData))
                if(event.calendar?.color) {
                    this.$nextTick(() => {
                        this.$refs.colorPicker.updateColor(event.calendar.color)
                    })
                }
            } else {
                this.defaultMembers = []
                this.showDefaultMembersAction = false
                if(startDate) {
                    if(this.$moment(startDate, 'YYYY-MM-DD', true).isValid()) {
                        if(this.$moment(endDate).diff(startDate, 'days') > 1) {
                            const end = this.$moment(endDate).add(-1, 'days')
                            this.form.start_at = this.$moment(startDate).set('hour', 0).set('minute', 0).set('second', 0).set('second', 0)
                            this.form.end_at = this.$moment(end).set('hour', 23).set('minute', 59).set('second', 59).set('millisecond', 59)
                        } else {
                            this.form.start_at = this.$moment(startDate).set('hour', 0).set('minute', 0).set('second', 0).set('second', 0)
                            this.form.end_at = this.$moment(startDate).set('hour', 23).set('minute', 59).set('second', 59).set('millisecond', 59)
                        }
                        this.form.all_day = true
                    } else {
                        this.form.start_at = this.$moment(startDate)
                        this.form.end_at = this.$moment(endDate)
                    }
                    this.selectedDate = true
                }
                if(related_object) {
                    const relatedCalendar = {
                        ...related_object,
                        string_view: related_object.string_view || related_object.name
                    }
                    this.form.related_object = related_object
                    this.form.calendar = relatedCalendar
                    if(related_object.color && !this.isCustomColor && !this.form.color) {
                        this.form.color = related_object.color
                    }
                }
                if(Array.isArray(inject?.members) && inject.members.length) {
                    this.form.members = inject.members
                }
                this.pendingProjectId = projectId || null
            }
            this.visible = true
            if(nameFocus) {
                this.$nextTick(() => {
                    setTimeout(() => {
                        if(this.$refs.eventNameInput)
                            this.$refs.eventNameInput.focus()
                    }, 700)
                })
            }
        })
    },
    beforeDestroy() {
        eventBus.$off('open_event_form')
    }
}
</script>

<style lang="scss" scoped>
.default-members-action {
    margin-top: -8px;
    margin-bottom: 12px;
}

.external-meeting-file-picker {
    display: flex;
    align-items: center;
    gap: 12px;
}

.external-meeting-file-picker__name {
    font-size: 13px;
    color: rgba(0, 0, 0, .65);
    word-break: break-word;
}

.default-members-slide-enter-active,
.default-members-slide-leave-active {
    transition: opacity 0.25s ease, transform 0.25s ease, max-height 0.25s ease, margin 0.25s ease;
    overflow: hidden;
}

.default-members-slide-enter,
.default-members-slide-leave-to {
    opacity: 0;
    transform: translateY(-10px);
    max-height: 0;
    margin-top: -12px;
    margin-bottom: 0;
}

.default-members-slide-enter-to,
.default-members-slide-leave {
    opacity: 1;
    transform: translateY(0);
    max-height: 40px;
}

</style>
