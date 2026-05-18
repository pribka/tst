<template>
    <DrawerTemplate
        :title="drawerTitle"
        v-model="visible"
        class="meeting_edit_drawer"
        :class="isMobile && 'mobile'"
        @close="visible = false"
        destroyOnClose
        @afterVisibleChange="afterVisibleChange"
        :width="drawerWidth">
        <template #rightHeader>
            <HelpButton partCode="meetings" />
        </template>
        <template>
            <div>
                <a-form-model
                    ref="meetingForm"
                    class="meeting_form"
                    :model="form"
                    :rules="rules">
                    <a-form-model-item
                        ref="name"
                        class="mb-2"
                        :label="$t('meeting.conferenceName')"
                        prop="name">
                        <a-input
                            :max-length="255"
                            v-model="form.name"
                            @pressEnter="formSubmit()"
                            size="large" />
                    </a-form-model-item>
                    <a-form-model-item
                        :label="$t('meeting.description')"
                        class="mb-2"
                        prop="description">
                        <a-textarea
                            v-model="form.description"
                            size="large"
                            :auto-size="{ minRows: 3, maxRows: 5 }" />
                    </a-form-model-item>
                    <a-form-model-item
                        :label="$t('meeting.startDateTime')"
                        class="mb-2"
                        prop="date_begin">
                        <DatePicker
                            v-model="form.date_begin"
                            size="large"
                            allowClear
                            :show-time="{ format: 'HH:mm' }"
                            @pressEnter="formSubmit()" />
                    </a-form-model-item>
                    <a-form-model-item
                        ref="duration"
                        :label="$t('meeting.duration')"
                        class="mb-2"
                        prop="duration">
                        <a-input-number
                            v-model="form.duration"
                            :min="0"
                            @pressEnter="formSubmit()"
                            :max="1000" />
                    </a-form-model-item>
                    <a-form-model-item
                        ref="project"
                        :label="$t('meeting.project')"
                        class="mb-2"
                        prop="project">
                        <ProjectSelect
                            inputType="defaultInput"
                            :placeholder="$t('meeting.project_select')"
                            v-model="form.project" />
                    </a-form-model-item>
                    <a-form-model-item
                        ref="members"
                        :label="$t('meeting.participants')"
                        prop="members">
                        <UserDrawer 
                            id="meetingCreate"
                            multiple
                            :buttonText="$t(edit ? 'meeting.change_participant_list' : 'meeting.add_participants')"
                            :changeMetadata="changeMetadata"
                            :metadata="{ key: 'members', value: form.metadata }"
                            v-model="form.members" />
                        <template v-if="form.members && form.members.length" >
                            <div class="meeting_users">
                                <div class="label font-light">
                                    {{ $t('meeting.added') }} {{ memberCount }}
                                </div>
                                <UserDrawerCard
                                    v-for="user in meetingMembers"
                                    :key="user.id"
                                    :form="form"
                                    :edit="edit"
                                    :memberDelete="memberDelete"
                                    :memberType="memberType"
                                    :user="user" />
                            </div>
                        </template>
                    </a-form-model-item>
                </a-form-model>
            </div>
        </template>
        <template #footer>
            <a-button 
                :loading="loading" 
                block
                size="large"
                @click="formSubmit()"
                type="primary">
                {{ emded ? $t('meeting.save') : $t('meeting.create') }}
            </a-button>
        </template>
    </DrawerTemplate>
</template>

<script>
import eventBus from '../utils/eventBus'
import gEventBus from '@/utils/eventBus'
import { declOfNum } from '../utils'
import { mapActions } from 'vuex'
import { errorHandler } from '@/utils/index.js'
export default {
    name: "MeetingCreateDrawer",
    components: {
        UserDrawer: () => import('@apps/DrawerSelect/index.vue'),
        UserDrawerCard: () => import('./UserDrawerCard.vue'),
        DatePicker: () => import('@apps/Datepicker'),
        DrawerTemplate: () => import("@/components/DrawerTemplate.vue"),
        HelpButton: () => import('@apps/Support/components/HelpButton.vue'),
        ProjectSelect: () => import("@apps/DrawerSelect/ProjectSelect.vue")
    },
    props: {
        emded: {
            type: Boolean,
            default: false
        },
        parentVisible: {
            type: Boolean,
            default: false
        },
        closeDrawer: {
            type: Function,
            default: () => {}
        },
        meeting: {
            type: Object,
            default: () => null
        },
        updateMeeting: {
            type: Function,
            default: () => {}
        },
        zIndex: {
            type: Number,
            default: 1010
        },
        pageName: {
            type: String,
            default: 'page_list_meetings.PlannedMeetingModel'
        }
    },
    computed: {
        drawerTitle() {
            return this.edit ? this.$t('meeting.editConference') : this.$t('meeting.createConference')
        },
        model() {
            return this.$store.state.meeting.showEdit.model
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        drawerWidth() {
            return this.windowWidth > 600 ? 600 : '100%'
        },
        meetingMembers() {
            return this.form.members
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        visible: {
            get() {
                if(this.emded)
                    return this.parentVisible
                else
                    return this.$store.state.meeting.showEdit.show
            },
            set(val) {
                if(!val)
                    this.edit = false

                if(this.emded)
                    this.closeDrawer()
                else {
                    this.$store.commit('meeting/SET_EDIT_DRAWER', { show: val, model: 'main' })
                }
            }
        },
        memberCount() {
            return this.form.members.length + ' ' + declOfNum(this.form.members.length,
                [this.$t('meeting.participant'), this.$t('meeting.participantGen'), this.$t('meeting.participantsGen')])
        }
    },
    data() {
        return {
            edit: false,
            // deleted: [],
            initMembers: [],
            previousMembers: [],
            memberCountKey: 1, 
            form: {
                metadata: { members: [] },
                name: '',
                project: null,
                date_begin: this.$moment(),
                duration: 50,
                members: [],
                model: ''
            },
            rules: {
                name: [
                    {
                        required: true,
                        message: this.$t('meeting.requiredField'),
                        trigger: 'blur',
                        whitespace: true,
                    }
                ],
                date_begin: [
                    {
                        required: true,
                        message: this.$t('meeting.requiredField'),
                        trigger: 'blur'
                    }
                ],
                duration: [
                    {
                        min: 0,
                        max: 1000,
                        type: "number",
                        trigger: 'blur',
                        whitespace: true,
                    }
                ]
            },
            loading: false
        }
    },
    watch: {
        async visible(val) {
            if(val && this.meeting) {
                this.edit = true
                const members = await this.getUsersMeeting(this.meeting.id)
                const formData = JSON.parse(JSON.stringify(this.meeting))
                const formMembers = members.results.map(user => ({
                    ...user.user,
                    is_moderator: user.is_moderator,
                    updated: false,
                    added: false
                }))
                this.form = {
                    ...formData,
                    members: formMembers,
                    date_begin: this.$moment(formData.date_begin)
                }
                // Vue.set(this.form, 'members', formMembers)
                this.initMembers.push(...members.results.map(el=> ({
                    ...el.user,
                    is_moderator: el.is_moderator,
                    updated: false,
                    added: false
                })))
            }
        }
    },
    created() {
        setTimeout(() => {
            this.checkOpen()
        }, 600)
    },
    methods: {
        ...mapActions({
            getUsersMeeting: 'meeting/getUsersMeeting'
        }),
        changeMetadata({key, value}) {
            this.$set(this.form.metadata, key, value)
        },

        afterVisibleChange(vis) {
            if(!vis) {
                this.clearForm()
            }
        },
        checkOpen() {
            if(this.$route.query?.createMeetings) {
                this.visible = true
                const query = JSON.parse(JSON.stringify(this.$route.query))
                delete query.createMeetings
                this.$router.push({query})
            }
        },
        clearForm() {
            // this.deleted = []
            this.initMembers = []
            this.memberCountKey = 1
            this.previousMembers = []
            this.form = {
                metadata: { members: [] },
                name: '',
                project: null,
                date_begin: this.$moment(),
                duration: 50,
                members: [],
                model: ''
            }
        },
        formSubmit() {
            this.$refs.meetingForm.validate(async valid => {
                if (!valid) { return false }
                const queryData = {
                    ...this.form,
                    members: this.form.members.map(user => ({
                        user: user.id,
                        is_moderator: user.is_moderator,
                    }))
                }
                if(queryData.project?.id)
                    queryData.project = queryData.project.id

                if(!this.edit) {
                    try {
                        this.loading = true
                        const { data } = await this.$http.post('/meetings/create/', queryData)
                        this.$message.success(this.$t('meeting.conferenceCreated'))
                        this.visible = false
                        gEventBus.$emit(`table_row_${this.pageName}`, { 
                            action: 'create',
                            row: data
                        })
                        gEventBus.$emit('reload_meetings_list', true)
                        if (this.$store.hasModule('workplan')) {
                            this.$store.dispatch('workplan/updateItem', {
                                item: data,
                                list: 'meetingList'
                            })
                        }
                        eventBus.$emit('reload_meetings_list', true)
                    } catch(error) {
                        errorHandler({error})
                    } finally {
                        this.loading = false
                    }
                } else {
                    try {
                        this.loading = true
                        
                        queryData.members = this.getPayloadMembers()

                        const {data} = await this.$http.put(`/meetings/${this.meeting.id}/update/`, queryData)
                        this.$message.success(this.$t('meeting.conferenceUpdated'))
                        this.visible = false
                        this.updateMeeting({meeting: data})
                        gEventBus.$emit(`table_row_${this.pageName}`, { 
                            action: 'update',
                            row: data
                        })
                        if (this.$store.hasModule('workplan')) {
                            this.$store.dispatch('workplan/updateItem', {
                                item: data,
                                list: 'meetingList'
                            })
                        }
                        gEventBus.$emit('reload_meetings_list', true)
                        eventBus.$emit('reload_meetings_list', true)
                    } catch(error) {
                        errorHandler({error})
                    } finally {
                        this.loading = false
                    }
                }
            })
        },
        getPayloadMembers() {
            const newMembers = new Map(this.form.members.map(member => [member.id, member]))
            const oldMembers = new Map(this.initMembers.map(member => [member.id, member]))
            const addedUsers = this.form.members.filter(member => !oldMembers.has(member.id))
                .map(user => ({ 
                    user: user.id,
                    is_moderator: user.is_moderator
                }))
            const editedUsers = this.form.members.filter(member => member.updated)
                .map(user => ({
                    user: user.id,
                    is_moderator: user.is_moderator
                }))
            const deletedUsers = this.initMembers.filter(member => !newMembers.has(member.id))
                .map(user => user.id)

            return {
                add: addedUsers, 
                edit: editedUsers, 
                delete: deletedUsers
            }
        },
        memberDelete(user) {
            const index = this.form.members.findIndex(f => f.id === user.id)
            if(index !== -1) {
                this.form.members.splice(index, 1)
            }

            this.form.metadata.members.forEach(organization => {
                const removedIndex = organization.users.findIndex(organizationUser => organizationUser.id === user.id)
                if (removedIndex !== -1) { 
                    organization.users.splice(removedIndex, 1)
                }   
            })
            this.form.metadata.members = this.form.metadata.members.filter(organizations => organizations.users.length > 0)
        },
        memberType(user) {
            const index = this.form.members.findIndex(f => f.id === user.id)
            if(index !== -1) { 
                this.form.members[index].is_moderator = !this.form.members[index].is_moderator
                this.form.members[index].updated = true
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.meeting_edit_drawer{
    .meeting_users{
        .user_card_drawer{
            &:not(:last-child) {
                border-bottom: 1px solid #e8e8e8;
            }
        }
    }
}
</style>