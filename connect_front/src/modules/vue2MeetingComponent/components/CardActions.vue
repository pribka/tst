<template>
    <div>
        <component 
            :is="actionsComponent" 
            :item="item"
            :isAuthor="isAuthor"
            :recordLoading="recordLoading"
            :restartConference="restartConference"
            :closeConference="closeConference"
            :inviteLink="inviteLink"
            :share="share"
            :deleteConference="deleteConference"
            :openEdit="openEdit"
            :activity="activity"
            :conferenceLink="conferenceLink"
            :closeDrawer="closeDrawer"
            :openRec="openRec" />
        <CreateDrawer 
            :emded="true"
            :parentVisible="editDrawer"
            :zIndex="1050"
            :closeDrawer="closeEditDrawer"
            :meeting="item" />
    </div>
</template>

<script>
import eventBus from '../utils/eventBus'
import globalEventBus from '@/utils/eventBus'
import { mapState } from 'vuex'
import { errorHandler } from '@/utils/index.js'
export default {
    components: {
        CreateDrawer: () => import('./CreateDrawer.vue')
    },
    props: {
        item: {
            type: Object,
            required: true
        },
        page_name: {
            type: String,
            default: 'page_list_meetings.PlannedMeetingModel'
        },
    },
    data() {
        return {
            editDrawer: false,
            recordLoading: false,
            meetingRecVisible: false,
            activity: false
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        isMobile() {
            return this.$store.state.isMobile
        },
        isAuthor() {
            return this.user && this.user.id === this.item.author.id
        },
        actionsComponent() {
            if(this.isMobile)
                return () => import ('./ActionsList.vue')
            else    
                return () => import ('./ActionsTable.vue')
        }
    },
    methods: {
        conferenceLink() {
            this.activity = false
            window.open(this.item.target, '_blank').focus()
        },
        openActionsDrawer() {
            this.activity = true
        },
        closeDrawer() {
            this.activity = false
        },
        closeEditDrawer() {
            this.editDrawer = false
        },
        openEdit() {
            this.activity = false
            this.editDrawer = true
        },
        openRec() {
            this.activity = false
            const query = JSON.parse(JSON.stringify(this.$route.query))
            if(!query?.meeting) {
                query.meeting = this.item.id
                query.meettab = 'records'
                this.$router.push({query})
            }
        },
        async restartConference() {
            try {
                await this.$http(`meetings/${this.item.id}/restart/`)
                eventBus.$emit(`RESTART_CONFERENCE`, this.item.id)
                globalEventBus.$emit(`table_row_${this.page_name}`, {
                    action: 'update',
                    row: { 
                        ...this.item,
                        status: 'new'
                    }
                })

            } catch(e) {
                console.error(e)
            }
        },
        closeConference() {
            this.activity = false
            this.$confirm({
                title: this.$t('meeting.warning'),
                content: this.$t('meeting.confirmEndConference'),
                zIndex: 5000,
                cancelText: this.$t('meeting.cancel'),
                okText: this.$t('meeting.end'),
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post('/meetings/end_meeting/', { id: this.item.id })
                            .then(() => {
                                this.$message.success(this.$t('meeting.conferenceEnded'))
                                eventBus.$emit(`END_CONFERENCE`, this.item.id)
                                if (this.$store.hasModule('workplan')) {
                                    this.$store.dispatch('workplan/updateItem', {
                                        item: this.item,
                                        list: 'meetingList'
                                    })
                                }
                                globalEventBus.$emit(`table_row_${this.page_name}`, {
                                    action: 'update',
                                    row: { 
                                        ...this.item,
                                        status: 'ended'
                                    }
                                })

                                resolve()
                            })
                            .catch(error => {
                                errorHandler({error})
                                reject()
                            })
                    })
                },
                onCancel() {}
            })
        },
        inviteLink() {
            try {
                this.activity = false
                navigator.clipboard.writeText(this.item.invite_link)
                this.$message.success(this.$t('meeting.linkCopied'))
            } catch(e) {
                console.log(e)
            }
        },
        share() {
            this.activity = false
            this.$store.commit('share/SET_SHARE_PARAMS', {
                model: 'meetings.PlannedMeetingModel',
                shareId: this.item.id,
                object: this.item,
                shareUrl: `${window.location.origin}/?meeting=${this.item.id}`,
                shareTitle: `${this.$t('meeting.conference')} - ${this.item.name}`
            })
        },
        deleteConference() {
            this.activity = false
            this.$confirm({
                title: this.$t('meeting.warning'),
                content: this.$t('meeting.confirmDeleteConference'),
                zIndex: 5000,
                cancelText: this.$t('meeting.cancel'),
                okText: this.$t('meeting.delete'),
                okType: 'danger',
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post('/table_actions/update_is_active/', [{ id: this.item.id, is_active: false }])
                            .then(() => {
                                this.$message.success(this.$t('meeting.conferenceDeleted'))
                                if (this.$store.hasModule('workplan')) {
                                    this.$store.dispatch('workplan/updateItem', {
                                        item: this.item,
                                        list: 'meetingList'
                                    })
                                }
                                eventBus.$emit(`reload_list_${this.page_name}`, true)
                                globalEventBus.$emit(`table_row_${this.page_name}`, {
                                    action: 'delete',
                                    row: { id: this.item.id }
                                })
                                resolve()
                            })
                            .catch(error => {
                                errorHandler({error})
                                reject()
                            })
                    })
                },
                onCancel() {}
            })
        }
    }
}
</script>