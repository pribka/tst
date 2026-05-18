import eventBus from '@/utils/eventBus'
import { mapState } from 'vuex'
export default {
    props: {
        id: {
            type: [String, Number],
            required: true
        },
        record: {
            type: Object,
            required: true
        },
        dropTrigger: {
            type: Array,
            default: () => ['click']
        },
        toggleChildren: {
            type: Function,
            default: () => {}
        },
        expanded: {
            type: Number,
            default: null
        },
        reloadMainList: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        isAuthor() {
            return this.user && this.record?.director?.id === this.user.id
        }
    },
    data() {
        return {
            loading: false,
            actionLoading: false,
            actionsList: null,
            visible: false
        }
    },
    methods: {
        openActionDrawer() {
            this.visible = true
            this.visibleChange(this.visible)
        },
        orgCopyId() {
            try {
                navigator.clipboard.writeText(this.id)
                this.$message.success(this.$t('team.organization_id_copied'))
            } catch(e) {
                console.log(e)
                this.$message.error(this.$t('team.error'))
            }
        },
        openOrgInvite() {
            eventBus.$emit('invite_organization', this.record)
        },
        openOrgEnter() {
            eventBus.$emit('enter_organization')
        },
        openOrgMap() {
            eventBus.$emit('org_map_open')
        },
        leaveOrg() {
            this.$confirm({
                title: this.$t('team.confirm_leave_organization'),
                okText: this.$t('team.leave'),
                okType: 'danger',
                cancelText: this.$t('team.cancel'),
                closable: true,
                maskClosable: true,
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        // this.$http.post(`/users/my_organizations/${this.id}/leave/`)
                        //     .then(() => {
                        //         this.$message.info(this.$t('team.successfully_left_organization'))
                        //         eventBus.$emit('orgTableReload')
                        //         this.reloadMainList()
                        //         resolve(true)
                        //     })
                        //     .catch((error) => { 
                        //         this.$message.error(this.$t('team.error'))
                        //         reject(error)
                        //     })
                    })
                }
            })
        },
        async getInviteLink() {
            try {
                this.loading = true
                const { data } = await this.$http.get(`/users/my_organizations/${this.id}/invite/`)
                if(data?.invite) {
                    navigator.clipboard.writeText(data.invite)
                    this.$message.success(this.$t('team.link_copied'))
                }
            } catch(e) {
                console.log(e)
                this.$message.error(this.$t('team.error'))
            } finally {
                this.loading = false
            }
        },
        userList() {
            this.toggleChildren({ value: this.record.showChildren ? false : true, key: 'showChildren', id: this.record.id, expanded: this.expanded })
        },
        invite() {
            eventBus.$emit('open_invite', this.id)
        },
        edit() {
            eventBus.$emit('edit_organization', this.record)
        },
        visibleChange(visible) {
            if(visible) {
                this.getActions()
            } else {
                this.clearActions()
            }
        },
        async getActions() {
            try {
                this.actionLoading = true
                const { data } = await this.$http.get(`/users/my_organizations/${this.id}/action_info/`)
                if(data?.actions) {
                    this.actionsList = data.actions
                }
            } catch(e) {
                this.$message.error(this.$t('team.error'))
            } finally {
                this.actionLoading = false
            }
        },
        clearActions() {
            this.actionsList = null
        }
    }
}