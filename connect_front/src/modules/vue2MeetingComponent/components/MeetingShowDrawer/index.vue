<template>
    <DrawerTemplate
        class="meeting_show"
        :class="isMobile && 'meeting_show_mobile'"
        v-model="visible"
        destroyOnClose
        useCopyLink
        useOpenLink
        :width="drawerWidth"
        @afterVisibleChange="afterVisibleChange"
        @close="visible = false">
        <!--:link="{ meeting: meeting ? meeting.id : null }"-->
        <template #title>
            <div class="w-full flex items-center justify-between truncate">
                <a-skeleton
                    v-if="loading"
                    active
                    :paragraph="{ rows: 1 }" />
                <div v-else class="title truncate">
                    <template v-if="meeting">
                        {{ meeting.name }}
                    </template>
                </div>
                <div class="ml-2 gap-2 flex items-center">
                    <template v-if="meeting">
                        <a-button
                            v-if="isAuthor"
                            type="ui"
                            ghost
                            v-tippy
                            :content="$t('edit')"
                            icon="fi-rr-edit"
                            shape="circle"
                            flaticon
                            @click="openEditDrawer()" />
                        <component
                            :is="moreMenuWidget"
                            :isAuthor="isAuthor"
                            :onlyMoreButton="onlyMoreButton"
                            :meeting="meeting"
                            :inviteLink="inviteLink"
                            :actionLoading="actionLoading"
                            :closeConference="closeConference"
                            :share="share"
                            :restartConference="restartConference"
                            :deleteConference="deleteConference"
                            :openEditDrawer="openEditDrawer" />
                    </template>
                </div>
            </div>
        </template>

        <template v-if="meeting" #tabs>
            <div class="drawer_tabs">
                <a-tabs
                    v-model="tab"
                    :showContent="false"
                    @change="changeTab">
                    <a-tab-pane key="info">
                        <template #tab>
                            {{ $t('meeting.conference') }}
                        </template>
                    </a-tab-pane>

                    <a-tab-pane key="session">
                        <template #tab>
                            <div class="flex items-center">
                                {{ $t('meeting.session') }}
                                <a-badge
                                    v-if="sectionsList.count"
                                    :count="sectionsList.count"
                                    style="margin-left: 8px;" />
                            </div>
                        </template>
                    </a-tab-pane>

                    <a-tab-pane key="records">
                        <template #tab>
                            {{ $t('meeting.records') }}
                        </template>
                    </a-tab-pane>
                </a-tabs>
            </div>
        </template>

        <a-tabs
            :activeKey="tab"
            :showBar="false"
            class="body_tab h-full">

            <a-tab-pane key="info">
                <div>
                    <a-skeleton v-if="loading" active />

                    <template v-else>
                        <template v-if="meeting">
                            <CreateDrawer
                                :emded="true"
                                :parentVisible="editDrawer"
                                :zIndex="1050"
                                :updateMeeting="updateMeeting"
                                :closeDrawer="closeEditDrawer"
                                :meeting="meeting" />

                            <div class="meeting_tag flex items-center flex-wrap gap-y-1 pb-4">
                                <Status
                                    v-tippy
                                    :content="$t('meeting.status')"
                                    :class="meeting.status === 'online' ? 'mr-2' : 'mr-1'"
                                    :status="meeting.status" />

                                <a-tag v-tippy :content="$t('meeting.startDateTime')">
                                    <span class="flex items-center">
                                        <i class="flex items-center fi fi-rr-calendar-lines mr-1"></i>
                                        {{ $t('meeting.formated_start_date', {
                                            date: $moment(meeting.date_begin).format('DD.MM.YYYY'),
                                            time: $moment(meeting.date_begin).format('HH:mm')
                                        })}}
                                    </span>
                                </a-tag>

                                <a-tag v-tippy :content="$t('meeting.duration')">
                                    <span class="flex items-center">
                                        <i class="flex items-center fi-rr-clock-nine mr-1"></i>
                                        {{ dFormat }}
                                    </span>
                                </a-tag>

                                <a-tag
                                    v-if="meeting.project"
                                    v-tippy
                                    :content="$t('meeting.project')"
                                    :title="meeting.project.name"
                                    class="truncate">
                                    {{$t('meeting.project')}}:
                                    <span style="max-width: 200px;" class="truncate ml-1">
                                        {{ meeting.project.name }}
                                    </span>
                                </a-tag>
                            </div>

                            <div v-if="meeting && meeting.description" class="desc">
                                <p class="break-words">
                                    {{ descLength }}
                                </p>
                                <div v-if="showDescBtn">
                                    <span
                                        class="desc_more text-xs blue_color cursor-pointer"
                                        @click="showDesc = !showDesc">
                                        {{ showDesc ? $t('meeting.hide') : $t('meeting.more') }}
                                    </span>
                                </div>
                            </div>

                            <a-divider v-if="meeting && meeting.description" />

                            <div class="user_list pb-3">
                                <div class="mb-3 flex items-center justify-between">
                                    <label class="font-semibold block">
                                        {{ $t('meeting.meeting_members') }} ({{ memberCount }})
                                    </label>

                                    <div v-if="isAuthor" class="flex items-center gap-2">
                                        <UserDrawer
                                            id="meetingParticipantsQuick"
                                            multiple
                                            v-model="quickMembers"
                                            @input="onQuickMembersChanged">
                                            <template #openButton>
                                                <a-button 
                                                    v-if="isMobile"
                                                    type="flat_primary" 
                                                    icon="fi-rr-plus"
                                                    :disabled="userLoading"
                                                    shape="circle"
                                                    flaticon
                                                    :loading="quickMembersLoading" />
                                                <a-button 
                                                    v-else
                                                    type="flat_primary" 
                                                    icon="fi-rr-plus"
                                                    :disabled="userLoading"
                                                    flaticon
                                                    :loading="quickMembersLoading">
                                                    {{ $t('meeting.addParticipant') }}
                                                </a-button>
                                            </template>
                                        </UserDrawer>
                                    </div>
                                </div>

                                <a-spin :spinning="userLoading" class="w-full" size="small">
                                    <div v-if="!isMobile" class="flex items-center justify-between mb-3 users_header rounded-xl">
                                        <div class="users_header__col">
                                            {{ $t('meeting.participant_table') }}
                                        </div>
                                        <div class="users_header__col" style="min-width: 150px;">
                                            {{ $t('meeting.role') }}
                                        </div>
                                    </div>

                                    <UserCard
                                        v-for="mUser in userList.results"
                                        :key="mUser.user.id"
                                        :user="mUser.user"
                                        :isModerator="mUser.is_moderator"
                                        :meeting="meeting"
                                        :canEditModerators="isAuthor"
                                        :toggleModerator="toggleModerator" />
                                </a-spin>
                            </div>
                        </template>
                    </template>
                </div>
            </a-tab-pane>

            <a-tab-pane key="session" forceRender>
                <template v-if="tab === 'session' && meeting">
                    <a-spin :spinning="sectionLoading" size="small" class="w-full">
                        <component
                            v-for="(session, index) in sectionsForRender"
                            :is="sectionCard"
                            :key="session.id"
                            useInject
                            :indexValue="index+1"
                            useIndex
                            :showAIIntents="false"
                            :useOpen="false"
                            :getInjectActions="getInjectActions"
                            useLocalStore
                            :changeListItem="changeListItem"
                            :storeKey="storeKey"
                            :meeting="session" />

                        <a-empty
                            v-if="!sectionLoading && !sectionsList.results.length"
                            :description="$t('meeting.no_session')" />

                        <div v-if="sectionsList.next" class="pt-1 flex justify-center">
                            <a-button
                                type="ui"
                                ghost
                                block
                                :loading="sectionMoreLoading"
                                @click="getSections()">
                                {{ $t('load_more') }}
                            </a-button>
                        </div>
                    </a-spin>
                </template>
            </a-tab-pane>

            <a-tab-pane key="records" forceRender>
                <Records 
                    v-if="meeting"
                    :meeting="meeting"  />
            </a-tab-pane>
        </a-tabs>

        <template #footer>
            <div class="flex items-center w-full gap-2">
                <a-skeleton
                    v-if="loading"
                    active
                    :paragraph="{ rows: 1 }" />
                <template v-else>
                    <template v-if="meeting">
                        <a
                            v-if="meeting.status !== 'ended' && !meeting.is_external"
                            :href="meeting.target"
                            :class="[isMobile && 'ant-btn-lg ant-btn-block justify-center']"
                            class="ant-btn ant-btn-primary flex items-center"
                            target="_blank">
                            <i class="fi fi-rr-play icon mr-2" /> {{ $t('meeting.connect') }}
                        </a>
                        <a-button
                            v-if="meeting.invite_link && !meeting.is_external"
                            type="flat_primary"
                            :size="isMobile ? 'large' : 'default'"
                            flaticon
                            icon="fi-rr-copy-alt"
                            @click="inviteLink">
                            <template v-if="!isMobile">{{ $t('meeting.inviteLink') }}</template>
                        </a-button>
                    </template>
                </template>
            </div>
        </template>
    </DrawerTemplate>
</template>

<script>
import { mapState } from 'vuex'
import { durationFormat } from '../../utils'
import eventBus from '../../utils/eventBus'
import globalEventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'
import { clearTabQuery } from '@/utils/routerUtils.js'

const session_page_size = 10
const members_page_size = 10000

export default {
    name: "MeetingShowDrawer",
    components: {
        DrawerTemplate: () => import("@/components/DrawerTemplate.vue"),
        CreateDrawer: () => import('../CreateDrawer'),
        UserCard: () => import('./UserCard.vue'),
        Status: () => import('../Status.vue'),
        UserDrawer: () => import('@apps/DrawerSelect/index.vue'),
        Records: () => import('./Records.vue')
    },
    props: {
        pageName: {
            type: String,
            default: 'page_list_meetings.PlannedMeetingModel'
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user,
            windowWidth: state => state.windowWidth
        }),
        sectionCard() {
            if (this.tab === 'session')
                return () => import('@apps/WorkPlan/Drawer/widgets/MeetingList/Card.vue')
            return null
        },
        dFormat() {
            return durationFormat(this.meeting.duration)
        },
        drawerWidth() {
            if (this.windowWidth > 950) return 950
            return '100%'
        },
        memberCount() {
            return this.meeting.members_count
        },
        descLength() {
            if (!this.showDesc && this.meeting?.description?.length > 475)
                return this.meeting.description.substr(0, 475) + '...'
            return this.meeting.description
        },
        isAuthor() {
            return !!(this.user && this.meeting?.author?.id && this.user.id === this.meeting.author.id)
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        moreMenuWidget() {
            if (this.isMobile) return () => import('./MoreMenuMobile.vue')
            return () => import('./MoreMenuDropdown.vue')
        },
        onlyMoreButton() {
            return this.meeting.status === 'ended'
        },
        sectionsForRender() {
            return (this.sectionsList.results || []).map(item => ({
                meeting: this.meeting,
                ...item
            }))
        }
    },
    data() {
        return {
            storeKey: 'main',
            actions: null,
            visible: false,
            loading: false,
            meeting: null,
            tab: 'info',
            actionLoading: false,
            editDrawer: false,
            showDesc: false,
            showDescBtn: false,
            userLoading: false,
            sectionLoading: true,
            sectionMoreLoading: false,
            userList: {
                results: [],
                next: false,
                count: 0
            },
            sectionsList: {
                results: [],
                next: true,
                count: 0,
                page: 0,
                page_size: session_page_size
            },
            quickMembers: [],
            quickMembersInitIds: [],
            quickMembersLoading: false,
            moderatorLoading: false
        }
    },
    watch: {
        '$route.name'() {
            if (this.$route.query?.meeting)
                this.visible = false
        },
        '$route.query.meeting'(val) {
            if (val && !this.visible)
                this.openDrawer()
            else this.visible = false
        }
    },
    mounted() {
        if (this.$route.query?.meeting) {
            this.openDrawer()
        }
    },
    methods: {
        inviteLink() {
            try {
                navigator.clipboard.writeText(this.meeting.invite_link)
                this.$message.success(this.$t('meeting.linkCopied'))
            } catch(e) {
                console.log(e)
            }
        },
        changeListItem({ item, field, value }) {
            if(this.sectionsList?.results?.length) {
                const index = this.sectionsList.results.findIndex(f => f.id === item)
                if(index !== -1)
                    this.$set(this.sectionsList.results[index], field, value)
            }
        },
        async restartConference() {
            try {
                this.actionLoading = true
                await this.$http(`meetings/${this.meeting.id}/restart/`)
                eventBus.$emit(`reload_meetings_list`, true)
                globalEventBus.$emit(`table_row_${this.pageName}`, {
                    action: 'delete',
                    row: { id: this.meeting.id }
                })
                this.meeting.status = "new"
            } catch(error) {
                errorHandler({error})
            } finally {
                this.actionLoading = false
            }
        },
        async getInjectActions(item) {
            try {
                const { data } = await this.$http.get(`/meetings/sections/${item.id}/action_info/`)
                if (data) {
                    const index = this.sectionsList.results.findIndex(f => f.id === item.id)
                    if (index !== -1)
                        this.$set(this.sectionsList.results[index], 'actions', data.actions)
                }
            } catch (error) {
                errorHandler({ error, show: false })
            }
        },
        changeTab(val) {
            const query = JSON.parse(JSON.stringify(this.$route.query))
            query.meettab = val
            this.$router.push({ query })
        },
        resetSectionsList() {
            this.sectionLoading = true
            this.sectionMoreLoading = false
            this.sectionsList = {
                results: [],
                next: true,
                count: 0,
                page: 0,
                page_size: session_page_size
            }
        },
        async getSections(reset) {
            if (!this.meeting?.id) return
            if (this.sectionMoreLoading) return

            const isReset = !!reset

            try {
                if (isReset) this.resetSectionsList()
                else this.sectionMoreLoading = true

                const nextPage = isReset ? 1 : (this.sectionsList.page + 1)

                const { data } = await this.$http.get('/meetings/sections/', {
                    params: { 
                        meeting: this.meeting.id,
                        paginate: true,
                        page_size: this.sectionsList.page_size,
                        page: nextPage
                    }
                })

                const results = data?.results || []

                if (isReset) this.sectionsList.results = results
                else this.sectionsList.results = this.sectionsList.results.concat(results)

                this.sectionsList.next = data?.next
                this.sectionsList.count = data?.count || this.sectionsList.count
                this.sectionsList.page = nextPage
            } catch(error) {
                errorHandler({ error, show: false })
                if (!isReset && this.sectionsList.page > 0) this.sectionsList.page -= 1
            } finally {
                this.sectionLoading = false
                this.sectionMoreLoading = false
            }
        },
        resetMembersList() {
            this.userLoading = false
            this.userList = { results: [], next: false, count: 0 }
            this.quickMembers = []
            this.quickMembersInitIds = []
            this.quickMembersLoading = false
            this.moderatorLoading = false
        },
        async loadMembersAll() {
            if (!this.meeting?.id) return
            try {
                this.userLoading = true
                const { data } = await this.$http.get('/meetings/members/', {
                    params: {
                        meeting: this.meeting.id,
                        page_size: members_page_size,
                        page: 1
                    }
                })

                this.userList.results = data?.results || []
                this.userList.next = data?.next
                this.userList.count = data?.count || 0

                const members = (this.userList.results || []).map(m => ({
                    ...m.user,
                    is_moderator: m.is_moderator
                }))

                this.quickMembers = members
                this.quickMembersInitIds = members.map(u => u.id)
            } catch (error) {
                errorHandler({ error, show: false })
                this.userList = { results: [], next: false, count: 0 }
                this.quickMembers = []
                this.quickMembersInitIds = []
            } finally {
                this.userLoading = false
            }
        },
        afterVisibleChange(vis) {
            if (vis) {
                if (this.$route.query?.meettab) this.tab = this.$route.query.meettab
                this.getMeeting()
            } else {
                this.close()
            }
        },
        share() {
            this.$store.commit('share/SET_SHARE_PARAMS', {
                model: 'tasks.TaskModel',
                shareId: this.meeting.id,
                object: this.meeting,
                shareUrl: `${window.location.origin}/?meeting=${this.meeting.id}`,
                shareTitle: `${this.$t('meeting.conference')} - ${this.meeting.name}`
            })
        },
        deleteConference() {
            this.$confirm({
                title: this.$t('meeting.warning'),
                content: this.$t('meeting.confirmDeleteConference'),
                zIndex: 1200,
                cancelText: this.$t('meeting.close'),
                okText: this.$t('meeting.delete'),
                okType: 'danger',
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post('/table_actions/update_is_active/', [{ id: this.meeting.id, is_active: false }])
                            .then(() => {
                                this.$message.success(this.$t('meeting.conferenceDeleted'))
                                eventBus.$emit(`reload_meetings_list`, true)
                                if (this.$store.hasModule('workplan')) {
                                    this.$store.dispatch('workplan/updateItem', {
                                        item: this.meeting,
                                        list: 'meetingList'
                                    })
                                }
                                globalEventBus.$emit(`table_row_${this.pageName}`, {
                                    action: 'delete',
                                    row: { id: this.meeting.id }
                                })
                                this.visible = false
                                resolve()
                            })
                            .catch((error) => {
                                errorHandler({ error })
                                reject()
                            })
                    })
                },
                onCancel() {}
            })
        },
        closeConference() {
            this.$confirm({
                title: this.$t('meeting.warning'),
                content: this.$t('meeting.confirmEndConference'),
                zIndex: 1200,
                cancelText: this.$t('meeting.close'),
                okText: this.$t('meeting.end'),
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post('/meetings/end_meeting/', { id: this.meeting.id })
                            .then(() => {
                                this.$message.success(this.$t('meeting.conferenceEnded'))
                                this.meeting.status = 'ended'
                                eventBus.$emit(`END_CONFERENCE`, this.meeting.id)
                                if (this.$store.hasModule('workplan')) {
                                    this.$store.dispatch('workplan/updateItem', {
                                        item: this.meeting,
                                        list: 'meetingList'
                                    })
                                }
                                globalEventBus.$emit(`table_row_${this.pageName}`, {
                                    action: 'update',
                                    row: { id: this.meeting.id, status: 'ended' }
                                })
                                resolve()
                            })
                            .catch((error) => {
                                errorHandler({ error })
                                reject()
                            })
                    })
                },
                onCancel() {}
            })
        },
        updateMeeting({ meeting }) {
            this.meeting = meeting
            this.resetMembersList()
            this.loadMembersAll()
        },
        closeEditDrawer() {
            this.editDrawer = false
        },
        close() {
            this.sectionLoading = true
            this.meeting = null
            this.actions = null
            this.tab = 'info'
            this.resetMembersList()
            this.resetSectionsList()

            const next = clearTabQuery({
                ...this.$route.query,
                meeting: undefined,
                meettab: undefined
            })

            Object.keys(next).forEach(k => {
                if (next[k] === undefined || next[k] === null || next[k] === '') delete next[k]
            })

            const same = JSON.stringify(this.$route.query) === JSON.stringify(next)
            if (same) return

            this.$router.replace({
                name: this.$route.name,
                params: this.$route.params,
                query: next
            })
        },
        async getMeeting() {
            try {
                this.loading = true
                const { data } = await this.$http.get(`/meetings/${this.$route.query.meeting}/detail/`)
                if (data) {
                    this.meeting = data
                    if (this.meeting?.description?.length > 175) this.showDescBtn = true
                    this.loadMembersAll()
                    this.getSections(true)
                }
            } catch (error) {
                errorHandler({ error })
                this.visible = false
            } finally {
                this.loading = false
            }
        },
        onQuickMembersChanged(val) {
            if (!this.meeting?.id) return
            if (!Array.isArray(val)) return
            if (this.quickMembersLoading) return

            const newIds = val.map(u => u.id)
            const oldIds = this.quickMembersInitIds

            const same =
                newIds.length === oldIds.length &&
                newIds.every(id => oldIds.includes(id))

            if (same) return

            const added = newIds.filter(id => !oldIds.includes(id))
            const deleted = oldIds.filter(id => !newIds.includes(id))

            const payload = {
                ...this.meeting,
                members: {
                    add: added.map(id => ({ user: id, is_moderator: false })),
                    edit: [],
                    delete: deleted
                }
            }

            if (payload.project?.id) payload.project = payload.project.id

            this.quickMembersLoading = true
            this.$http.put(`/meetings/${this.meeting.id}/update/`, payload)
                .then(({ data }) => {
                    this.$message.success(this.$t('meeting.conferenceUpdated'))
                    this.meeting = data
                    this.quickMembersInitIds = newIds
                    this.loadMembersAll()
                })
                .catch((error) => {
                    errorHandler({ error })
                    this.loadMembersAll()
                })
                .finally(() => {
                    this.quickMembersLoading = false
                })
        },
        async toggleModerator({ userId, value }) {
            if (!this.isAuthor) return
            if (!this.meeting?.id) return
            if (this.moderatorLoading) return
            if (!userId) return

            const payload = {
                ...this.meeting,
                members: {
                    add: [],
                    edit: [{ user: userId, is_moderator: value }],
                    delete: []
                }
            }

            if (payload.project?.id) payload.project = payload.project.id

            const listIndex = this.userList.results.findIndex(m => m?.user?.id === userId)
            const quickIndex = this.quickMembers.findIndex(u => u?.id === userId)

            try {
                this.moderatorLoading = true

                if (listIndex !== -1) {
                    this.$set(this.userList.results[listIndex], 'is_moderator', value)
                }
                if (quickIndex !== -1) {
                    this.$set(this.quickMembers[quickIndex], 'is_moderator', value)
                }

                const { data } = await this.$http.put(`/meetings/${this.meeting.id}/update/`, payload)
                this.meeting = data

                await this.loadMembersAll()
                this.$message.success(this.$t('meeting.conferenceUpdated'))
            } catch (error) {
                errorHandler({ error })
                await this.loadMembersAll()
            } finally {
                this.moderatorLoading = false
            }
        },
        openDrawer() {
            this.visible = true
        },
        openEditDrawer() {
            this.editDrawer = true
        }
    }
}
</script>

<style lang="scss" scoped>
.users_header {
    background: #f0f1f6;
    padding: 10px 15px;
    &__col {
        opacity: 0.8;
    }
}
.record_list {
    .item {
        cursor: pointer;
    }
}
.meeting_show {
    .user_list {
        .user_card {
            &:not(:last-child) {
                border-bottom: 1px solid var(--border2);
                margin-bottom: 10px;
                padding-bottom: 10px;
            }
        }
    }
    .meeting_tag {
        &::v-deep {
            .ant-tag {
                display: flex;
                align-items: center;
                &:not(:last-child) {
                    margin-right: 4px;
                }
            }
        }
    }
    .drawer_header {
        height: 40px;
        border-bottom: 1px solid var(--border2);
        padding: 0 15px;
        &::v-deep {
            .ant-skeleton-title {
                margin: 0px;
            }
            .ant-skeleton-paragraph {
                display: none;
            }
        }
        .title {
            margin: 0;
            color: rgba(0, 0, 0, 0.85);
            font-weight: 500;
            font-size: 16px;
            line-height: 22px;
        }
    }
    .drawer_body {
        padding: 15px;
        height: calc(100% - 80px);
        overflow-y: auto;
    }
    .drawer_footer {
        height: 40px;
        border-top: 1px solid var(--border2);
        padding: 0 15px;
        &::v-deep {
            .ant-skeleton-title {
                margin: 0px;
            }
            .ant-skeleton-paragraph {
                display: none;
            }
        }
    }
}
</style>
