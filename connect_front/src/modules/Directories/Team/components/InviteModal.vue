<template>
    <a-modal
        title=""
        :visible="visible"
        :zIndex="99999"
        :width="600"
        :header="null"
        :footer="null"
        :afterClose="afterClose"
        @cancel="visible = false">
        <a-spin :spinning="loading">
            <template v-if="mode === 'join'">
                <div v-if="workgroupToJoin" class="org_invite_modal py-7">
                    <div class="mb-4 flex justify-center">
                        <a-avatar :size="130" :src="workgroupToJoin.workgroup_logo" icon="picture" />
                    </div>
                    <div class="wrap">
                        <h2>{{ $t('team.workgroup_invites_you', { name: workgroupToJoin.name }) }}</h2>
                        <div class="md:flex items-center justify-center mt-8">
                            <a-button
                                type="primary"
                                block
                                :loading="invLoading"
                                class="md:mr-1 px-5 mb-2 md:mb-0"
                                size="large"
                                @click="inviteSuccess()">
                                {{ $t('team.join') }}
                            </a-button>
                            <a-button
                                class="md:ml-1 px-5"
                                block
                                type="ui_ghost"
                                size="large"
                                @click="visible = false">
                                {{ $t('team.close') }}
                            </a-button>
                        </div>
                    </div>
                </div>
                <div v-else-if="org" class="org_invite_modal py-7">
                    <div class="mb-4 flex justify-center">
                        <a-avatar :size="130" :src="org.logo" icon="picture" />
                    </div>
                    <div class="wrap">
                        <h2>{{ $t('team.organization_invites_you', { name: org.name }) }}</h2>
                        <div class="md:flex items-center justify-center mt-8">
                            <a-button
                                type="primary"
                                block
                                :loading="invLoading"
                                class="md:mr-1 px-5 mb-2 md:mb-0"
                                size="large"
                                @click="inviteSuccess()">
                                {{ $t('team.join') }}
                            </a-button>
                            <a-button
                                class="md:ml-1 px-5"
                                block
                                type="ui_ghost"
                                size="large"
                                @click="visible = false">
                                {{ $t('team.close') }}
                            </a-button>
                        </div>
                    </div>
                </div>
            </template>
            <template v-else-if="mode === 'member_organization_invite'">
                <div class="pt-7">
                    <h2 class="text-lg text-center">{{ modalText }}</h2>
                    <div class="flex mt-8">
                        <a-button
                            class="mr-2"
                            size="large"
                            type="primary"
                            :loading="memberInviteLoading"
                            block
                            @click="inviteProject('added')">
                            {{ $t('team.enter') }}
                        </a-button>
                        <a-button
                            class="mr-2"
                            size="large"
                            block
                            type="danger"
                            :loading="memberInviteLoading"
                            @click="inviteProject('refused')">
                            {{ $t('team.decline') }}
                        </a-button>
                        <a-button size="large" block type="ui_ghost" @click="visible = false">
                            {{ $t('team.close') }}
                        </a-button>
                    </div>
                </div>
            </template>
            <template v-else-if="mode === 'invite_to_helpdesk'">
                <div v-if="org" class="org_invite_modal py-7">
                    <div class="mb-4 flex justify-center">
                        <a-avatar :size="130" :src="org.logo" icon="picture" />
                    </div>
                    <div class="max-w-[640px] mx-auto">
                        <h2>
                            {{ $t('team.helpdesk_invite_message', { name: org.name }) }}
                        </h2>
                        <div class="grid grid-cols-3 gap-2 mt-8 mx-auto">
                            <a-button
                                type="primary"
                                block
                                :loading="invLoading"
                                size="large"
                                @click="inviteSuccess()">
                                {{ $t('team.join_helpdesk') }}
                            </a-button>
                            <a-button
                                block
                                size="large"
                                type="danger"
                                ghost
                                @click="visible = false">
                                {{ $t('team.refuse') }}
                            </a-button>
                            <a-button
                                block
                                size="large"
                                type="ui_ghost"
                                @click="visible = false">
                                {{ $t('team.close') }}
                            </a-button>
                        </div>
                    </div>
                </div>

            </template>
        </a-spin>
    </a-modal>
</template>

<script>
import eventBus from "@/utils/eventBus";
import { mapState } from "vuex";
export default {
    computed: {
        ...mapState({
            user: (state) => state.user.user,
        }),
    },
    data() {
        return {
            visible: false,
            token: null,
            loading: false,
            org: null,
            invLoading: false,
            memberInviteLoading: false,
            mode: "join",
            projectInviteData: null,
            modalText: '',
            workgroupToJoin: null
        };
    },
    mounted() {
        eventBus.$on("open_modal_invite", () => {
            this.mode = "join";
            this.visible = true;
        });

        eventBus.$on("open_member_organization_invite_modal", ({ data, message }) => {
            this.mode = "member_organization_invite";
            this.modalText = message
            this.projectInviteData = data
            this.visible = true;
        });
    },
    watch: {
        "$route.query.token"(val) {
            // TODO: Сделал true, чтобы ссылка работала на тех, кто уже в организации
            // const join = this.$route.query.join
            const join = true;
            this.mode = this.$route.query?.mode || "join";

            if (this.mode === "invite_to_helpdesk") {
                return this.connectToHelpdesk()
            }
            if (val && join) {
                this.token = val;

                this.getOrg();

                let query = Object.assign({}, this.$route.query);
                delete query.token; 
                delete query.join;
                this.$router.push({ query });
            }
            if (val && !join) {
                let query = Object.assign({}, this.$route.query);
                delete query.token;
                this.$router.push({ query });
            }
        },
    },
    methods: {
        connectToHelpdesk() {
            this.token = this.$route.query.token
            this.getContractorByInviteToken()
                .then(data => {
                    this.org = data
                    this.visible = true
                    const { token, mode, ...query } = this.$route.query
                    this.$router.replace({ query })
                })
                .catch(error => {
                    this.$message.error(error)
                    console.error(error)
                })
        },
        inviteProject(status) {
            const { project, organization_member } = this.projectInviteData
            const url = `work_groups/workgroups/${project}/approve_invite/`
            const payload = {
                organization_member_id: organization_member,
                status: status
            }
            this.memberInviteLoading = true
            this.$http.post(url, payload)
                .then(({ data }) => {
                    this.memberInviteLoading = false
                    this.visible = false
                    this.$message.success(this.$t('team.invitation_status_changed'))
                    eventBus.$emit('reload_member_organization_list')
                })
                .catch(error => {
                    console.error(error)
                    this.$message.error(this.$t('team.failed_to_change_invitation_status'))
                })
            
        },
        afterClose() {
            this.token = null;
            this.org = null;
            this.workgroupToJoin = null
        },
        getContractorByInviteToken() {
            const payload = { token: this.token }
            const url = '/users/my_organizations/get_contractor_by_invite_token/'
            return this.$http
                .post(url, payload)
                .then(({ data }) => data)
                .catch((error) => {
                    console.error(error);
                })
        },
        async getOrg() {
            try {
                const params = { token: this.token, skip_membership_check: true }
                const url = "/users/my_organizations/invite/info/"
                const { data } = await this.$http.get(url, {params})
                if(data) {
                    if (data.workgroup) {
                        const workgroupType = data.workgroup.is_project ? 'viewProject' : 'viewGroup'
                        const query = JSON.parse(JSON.stringify(this.$route.query))
                        query[workgroupType] = data.workgroup.id
                        this.$router.replace({query})
                    } else {
                        if (data.contractor) {
                            this.org = data.contractor;
                            this.visible = true;
                        }
                    }
                }
            } catch (error) {
                if (error[0]) {
                    this.$message.error(error[0]);
                } else if (error.message) {
                    this.$message.error(error.message, 4);
                } else {
                    this.$message.error(this.$t('team.error'), 4);
                }
                console.error(error);
            }
        },
        async inviteSuccess() {
            try {
                this.invLoading = true;
                const { data } = await this.$http.post(
                    "/users/my_organizations/join_by_invite/",
                    {
                        token: this.token,
                    }
                );
                if (data === "ok") {
                    this.visible = false;
                    this.$message.info(this.$t('team.successfully_joined_organization'), 4);
                }
            } catch (error) {
                if (error.message) {
                    this.$message.error(error.message, 4);
                }
                console.log(error);
            } finally {
                this.invLoading = false;
            }
        },
    },
    beforeDestroy() {
        eventBus.$off("open_modal_invite");
        eventBus.$off("open_member_organization_invite_modal");
    },
};
</script>

<style lang="scss" scoped>
.org_invite_modal {
  text-align: center;
  h2 {
    font-weight: 600;
    font-size: 18px;
  }
  .wrap {
    max-width: 370px;
    margin: 0px auto;
  }
}
</style>