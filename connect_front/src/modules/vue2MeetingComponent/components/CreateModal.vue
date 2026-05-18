<template>
    <a-modal
        :width="600"
        v-model="visible"
        class="meeting_edit_drawer"
        @cancel="visible = false"
        destroyOnClose
        @afterVisibleChange="afterVisibleChange"
        placement="right">
        <template #title>
            <a-form-model
                ref="nameForm"
                :model="form"
                class="name_form"
                :rules="nameRules">
                <a-form-model-item 
                    ref="name" 
                    prop="name" 
                    class="mb-0 name_row">
                    <div class="flex items-center justify-between">
                        <a-input 
                            v-model="form.name"
                            ref="nameInput"
                            inputType="ghost"
                            :placeholder="`${$t('meeting.conferenceName')} *`"
                            size="large"
                            @pressEnter="formSubmit()" />
                        <HelpButton partCode="meetings" class="ml-2" />
                    </div>
                </a-form-model-item>
            </a-form-model>
        </template>
        <template>
            <a-form-model
                ref="meetingForm"
                class="meeting_form mini_form"
                :model="form"
                :label-col="{ span: 8, style: { textAlign: 'left' } }"
                :wrapper-col="{ span: 16 }"
                :rules="rules">
                <a-form-model-item
                    :wrapper-col="{ span: 24 }"
                    prop="description">
                    <div class="text_block px-4 py-3 rounded-xl mt-3">
                        <a-textarea
                            v-model="form.description"
                            :placeholder="$t('meeting.description')"
                            size="large"
                            inputType="ghost"
                            :auto-size="{ minRows: 1, maxRows: 10 }" />
                    </div>
                </a-form-model-item>
                <a-form-model-item
                    :label="$t('meeting.startDateTime')"
                    class="flex items-center h-9 date_select"
                    prop="date_begin">
                    <DatePicker
                        v-model="form.date_begin"
                        inputType="ghost"
                        iconPosition="left"
                        :show-time="{ format: 'HH:mm' }"
                        @pressEnter="formSubmit()" />
                </a-form-model-item>
                <a-form-model-item
                    ref="duration"
                    class="flex items-center h-9"
                    :label="$t('meeting.duration')"
                    prop="duration">
                    <a-input-number
                        v-model="form.duration"
                        :min="0"
                        class="number_ghost"
                        @pressEnter="formSubmit()"
                        :max="1000" />
                </a-form-model-item>
                <a-form-model-item
                    ref="project"
                    class="flex items-center h-9"
                    :label="$t('meeting.project')"
                    prop="project">
                    <ProjectSelect
                        inputType="input"
                        :placeholder="$t('meeting.project_select')"
                        v-model="form.project" />
                </a-form-model-item>
                <a-form-model-item
                    ref="members"
                    :label="$t('meeting.participants')"
                    class="flex items-center h-9"
                    prop="members">
                    <UserDrawer 
                        id="meetingCreate"
                        multiple
                        inputType="ghost"
                        :buttonText="$t(edit ? 'meeting.change_participant_list' : 'meeting.add_participants')"
                        :changeMetadata="changeMetadata"
                        :metadata="{ key: 'members', value: form.metadata }"
                        v-model="form.members" />
                </a-form-model-item>
            </a-form-model>
            <template v-if="form.members && form.members.length" >
                <div class="meeting_users">
                    <div class="label font-light">
                        {{ $t('meeting.added') }} {{ memberCount }}
                    </div>
                    <UserDrawerCard
                        v-for="user in meetingMembers"
                        :key="user.id"
                        :memberDelete="memberDelete"
                        :memberType="memberType"
                        :user="user" />
                </div>
            </template>
        </template>
        <template #footer>
            <div ref="modal_footer" class="flex items-center justify-between w-full">
                <div class="flex gap-1 items-center">
                    <a-button 
                        :loading="loading" 
                        block
                        size="large"
                        @click="formSubmit()"
                        type="primary">
                        {{ emded ? $t('meeting.save') : $t('meeting.create') }}
                    </a-button>
                    <a-button type="ui_ghost" block ghost size="large" @click="visible = false">
                        {{ $t("close") }}
                    </a-button>
                </div>
                <!--<a-button type="ui_ghost" ghost size="large" @click="openFullForm()">
                    {{ $t('open_full_form') }}
                </a-button>-->
            </div>
        </template>
    </a-modal>
</template>

<script>
import eventBus from '../utils/eventBus'
import gEventBus from '@/utils/eventBus'
import { declOfNum } from '../utils'
import { mapActions } from 'vuex'
import { errorHandler } from '@/utils/index.js'
export default {
    name: "MeetingCreateModal",
    components: {
        UserDrawer: () => import('@apps/DrawerSelect/index.vue'),
        UserDrawerCard: () => import('./UserDrawerCard.vue'),
        DatePicker: () => import('@apps/Datepicker'),
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
            return this.$store.state.meeting.showEditModal.model
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
                    return this.$store.state.meeting.showEditModal.show
            },
            set(val) {
                if(!val)
                    this.edit = false

                if(this.emded)
                    this.closeDrawer()
                else {
                    this.$store.commit('meeting/SET_EDIT_MODAL', { show: val, model: 'main' })
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
            userDrawer: false,
            edit: false,
            // deleted: [],
            initMembers: [],
            previousMembers: [],
            memberCountKey: 1, 
            nameRules: {
                name: [
                    { required: true, message: '', trigger: 'blur' }
                ]
            },
            form: {
                metadata: { members: [] },
                name: '',
                date_begin: this.$moment(),
                duration: 50,
                members: [],
                project: null,
                model: ''
            },
            rules: {
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
        openFullForm() {
            this.visible = false
            this.$store.commit('meeting/SET_EDIT_DRAWER', { 
                show: true, 
                model: this.model,
                form: JSON.parse(JSON.stringify(this.form))
            })
        },
        // changeUsers(users) {

        //     const oldMembersMap = new Map(this.initMembers.map(m => [m.id, m]))
        //     const newMembersMap = new Map(users.map(m => [m.id, m]))

        //     users.forEach(user => {
        //         if (!oldMembersMap.has(user.id)) {
        //             this.$set(user, "added", true)
        //         } else {
        //             const original = oldMembersMap.get(user.id)
        //             const { added, updated, ...newData } = user
        //             const { added: oldAdded, updated: oldUpdated, ...oldData } = original
        //             if (JSON.stringify(newData) !== JSON.stringify(oldData)) {
        //                 this.$set(user, "updated", true)
        //             }
        //         }
        //     })

        //     const deletedUsers = this.initMembers.filter(member => !newMembersMap.has(member.id))
        //     deletedUsers.forEach(user => {
        //         if (!this.deleted.some(deletedUser => deletedUser.id === user.id)) {
        //             this.deleted.push(user)
        //         }
        //     })

        //     this.initMembers = JSON.parse(JSON.stringify(users))
        //     this.form.members = users
        // },
        changeMetadata({key, value}) {
            this.$set(this.form.metadata, key, value)
        },

        afterVisibleChange(vis) {
            if(!vis) {
                this.clearForm()
            } else {
                this.$nextTick(() => {
                    if(this.$refs?.nameInput)
                        this.$refs.nameInput.focus()
                })
            }
        },
        checkOpen() {
            if(this.$route.query?.createMeetings) {
                this.visible = true
                let query = JSON.parse(JSON.stringify(this.$route.query))
                delete query.createMeetings
                this.$router.push({query})
            }
        },
        clearForm() {
            // this.deleted = []
            this.previousMembers = []
            this.form = {
                metadata: { members: [] },
                name: '',
                date_begin: this.$moment(),
                duration: 50,
                project: null,
                members: [],
                memberKey: 1,
                model: ''
            }
        },
        formSubmit() {
            this.$refs.meetingForm.validate(async valid => {
                this.$refs.nameForm.validate(async valid2 => {
                    if (!valid && !valid2) { return false }
                    let queryData = {
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
                            this.clearForm()
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
                            this.clearForm()
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
        closeUserDrawer() {
            this.userDrawer = false
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
.text_block{
    background-color: #f8f9fd;
}
.name_form{
    margin-bottom: -15px;
}
.name_row{
    &::v-deep{
        .has-error{
            .ant-input.ant-input-ghost{
                color: #ff5d5d!important;
                &::placeholder{
                    color: #ff5d5d!important;
                }
            }
            .ant-form-explain{
                display: none;
            }
        }
    }
}
.number_ghost{
    &.ant-input-number{
        border: 0px;
        outline: none!important;
        box-shadow: none!important;
        &::v-deep{
            .ant-input-number-input{
                padding-left: 0px;
            }
        }
    }
}
.date_select{
    &::v-deep{
        .ant-calendar-picker-ghost.ant-calendar-picker-icon-left .ant-calendar-picker-input{
            padding-left: 25px;
        }
    }
}
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