<template>
    <UserDrawer 
        id="meetingCreate"
        multiple
        buttonMode
        buttonBlock
        :dialog-style="{ top: '15px' }"
        buttonSize="large"
        :title="$t('project.invite_participants')"
        :submitHandler="commitPartisipants"
        :buttonText="$t('project.invite_participants')"
        :changeMetadata="changeMetadata"
        :metadata="{ key: 'partisipants', value: metadata }"
        v-model="form.partisipants"
        @change="changeUserSelected"
        @afterVisibleChange="afterVisibleChange">
        <template #content>
            <div v-if="inviteLoading">
                <a-spin size="small" class="w-full" />
            </div>
            <div v-if="inviteData && inviteData.invite" class="flex">
                <div>
                    <qr-code :size="120" :text="inviteData.invite" />
                </div>
                <div class="ml-3 truncate">
                    <p style="word-break: break-word;white-space: normal;font-size: 13px;line-height: 18px;max-width: 360px;" class="mb-2">
                        {{ $t('share_qr') }}
                    </p>
                    <div class="flex items-center gap-1">
                        <div class="link_input truncate">
                            <span
                                ref="inviteText"
                                class="w-full truncate cursor-pointer"
                                @click="selectInvite">
                                {{ inviteData.invite }}
                            </span>
                            <a-button 
                                type="link"
                                size="small"
                                class="ant-btn-icon-only" 
                                v-tippy
                                :content="$t('copy_link')" 
                                @click="copyLink()">
                                <i class="fi fi-rr-copy-alt" />
                            </a-button>
                        </div>
                        <a-button 
                            type="ui_ghost"
                            flaticon
                            :loading="reloadLoading"
                            v-tippy
                            :content="$t('update_link')" 
                            style="max-height: 32px;min-height: 32px;"
                            icon="fi-rr-refresh"
                            @click="linkReload()" />
                    </div>
                </div>
            </div>
        </template>
    </UserDrawer>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
import eventBus from "@/utils/eventBus"
export default {
    components: {
        UserDrawer: () => import('@apps/DrawerSelect/index.vue'),
        QrCode: () => import('vue-qrcode-component')
    },
    props: {
        value: {
            type: [Array, Object, String, Number]
        },
        actions: {
            type: Object,
            default: () => null
        },
        requestData: {
            type: Object,
            required: true
        },
        useChangeMetadata: {
            type: Function,
            default: () => {}
        },
        useSubmitHandler: {
            type: Function,
            default: () => {}
        },
        useInject: {
            type: Boolean,
            default: false
        },
        updatePartisipants: {
            type: Function,
            default: () => {}
        },
        addToMembersList: {
            type: Function,
            default: () => {}
        },
        injectMetadata: {
            type: Object,
            default: () => {}
        }
    },
    computed: {
        isMobile() { 
            return this.$store.state.isMobile
        },
        tableCount() {
            return this.$store.state.projects.tables?.[this.tableKey]?.count
        },
        metadata() {
            if(this.useInject) {
                return this.injectMetadata
            }
            return this.form.metadata
        }
    },
    data() {
        return {
            pageSize: 15,
            page: 1,
            reloadLoading: false,
            form: {
                partisipants: [],
                metadata: {
                    partisipants: []
                }
            },
            tableKey: `project_members_${this.requestData.id}`,
            visible: false,
            loading: false,
            inviteData: null,
            inviteLoading: false
        }
    },
    methods: {
        async linkReload() {
            try {
                this.reloadLoading = true
                const { data } = await this.$http.post(`/work_groups/workgroups/${this.requestData.id}/invite/`, {
                    deactivate_at: null,
                    is_create_new_contractor: true
                })
                if(data) {
                    this.inviteData = data
                }
            } catch(error) {
                errorHandler({error})
            } finally {
                this.reloadLoading = false
            }
        },
        selectInvite() {
            const el = this.$refs.inviteText
            if (!el) return
            const sel = window.getSelection()
            if (!sel) return
            const range = document.createRange()
            range.selectNodeContents(el)
            sel.removeAllRanges()
            sel.addRange(range)
        },
        changeUserSelected(value) {
            this.commitPartisipants(value)
            if(this.useInject)
                this.$emit('input', value)
        },
        commitPartisipants(value) {
            if(this.useInject) {
                this.useSubmitHandler()
            } else {
                if(value.length === 0)
                    return 0

                const prifileIds = value.map(user => user.id)
                const payload = { profile_id: prifileIds }
                this.$http.post(`/work_groups/workgroups/${this.requestData.id}/send_invitations/`, payload)
                    .then(() => {
                        this.addToMembersList(value)
                        this.getData()
                        if(this.isMobile)
                            eventBus.$emit(`update_member_list_${this.requestData.id}`)
                        //this.saveMetadata()
                        this.$message.success(this.$t('project.successful'))
                    })
                    .catch(error => {
                        errorHandler({error})
                    })
            }
        },
        async saveMetadata() {
            try {
                await this.$http.patch(`/work_groups/workgroups/${this.requestData.id}/`, {
                    metadata: this.form.metadata
                })
            } catch(error) {
                errorHandler({error})
            }
        },
        getData() {
            const params = {
                page: this.page,
                page_size: this.pageSize
            }
            const actionPayload = { 
                endpoint: `work_groups/workgroups/${this.requestData.id}/get_workgroups_members/`, 
                params, 
                tableKey: this.tableKey
            }
            this.$store.dispatch('projects/setTable', actionPayload)
                .then(() => {
                    this.updatePartisipants(this.tableCount)
                })
                .catch(error => {
                    errorHandler({error})
                })
        },
        changeMetadata({key, value}) {
            if(this.useInject) {
                this.useChangeMetadata({key, value})
            } else {
                this.$set(this.form.metadata, key, value)
            }
        },
        copyLink() {
            try {
                navigator.clipboard.writeText(this.inviteData.invite)
                this.$message.success(this.$t('link_succes_copy'))
            } catch(e) {
                console.log(e)
            }
        },
        afterVisibleChange(vis) {
            if(vis) {
                if(!this.inviteData)
                    this.getToken()
            } else {
                /*if(!this.useInject) {
                    this.form = {
                        partisipants: [],
                        metadata: {
                            partisipants: []
                        }
                    }
                }*/
            }
        },
        async getToken() {
            try {
                this.inviteLoading = true
                this.loading = true
                const { data } = await this.$http.get(`/work_groups/workgroups/${this.requestData.id}/invite/`)
                if(data) {
                    this.inviteData = data
                }
            } catch(error) {
                errorHandler({error})
            } finally {
                this.loading = false
                this.inviteLoading = false
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.invite_block{
    h1{
        font-size: 18px;
        margin-bottom: 10px;
    }
    p{
        margin-bottom: 10px;
        max-width: 340px;
        margin-left: auto;
        margin-right: auto;
        color: #888;
    }
}
.link_input{
    background-color: #f7f9fc;
    border-radius: var(--borderRadius);
    display: flex;
    align-items: center;
    padding: 5px 15px;
    line-height: 22px;
    max-width: 100%;
    width: 100%;
}
</style>
