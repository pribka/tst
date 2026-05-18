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
        <div v-if="modalLoader" class="flex justify-center h-full items-center" style="min-height: 300px;">
            <a-spin />
        </div>
        <div v-if="!modalLoader && org" class="org_invite_modal py-7">
            <div class="mb-6 flex items-center justify-center">
                <a-avatar 
                    :size="isMobile ? 85 : 110"
                    :src="org.contractor.logo"
                    flaticon
                    icon="fi-rr-users-alt" />
                <div class="mx-4 md:mx-6 text-xl md:text-2xl gray">
                    <i class="fi fi-rr-exchange-alt"></i>
                </div>
                <a-avatar 
                    :size="isMobile ? 85 : 110"
                    :src="org.contractor_parent.logo"
                    flaticon
                    icon="fi-rr-users-alt" />
            </div>
            <div class="wrap">
                <h2 v-html="org.inviteMessage"></h2>
                <div class="md:flex items-center justify-center mt-8">
                    <a-button 
                        type="primary" 
                        block 
                        :loading="inviteLoading" 
                        class="md:mr-1 px-5 mb-2 md:mb-0" 
                        size="large" 
                        ghost 
                        @click="inviteAccept()">
                        {{ $t('team.join') }}
                    </a-button>
                    <a-button class="md:ml-1 px-5" block size="large" :loading="rejectLoading" type="danger" ghost @click="inviteReject()">
                        {{ $t('team.decline') }}
                    </a-button>
                </div>
            </div>
        </div>
    </a-modal>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    data() {
        return {
            visible: false,
            token: null,
            loading: false,
            org: null,
            inviteLoading: false,
            rejectLoading: false,
            modalLoader: false
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    created() {
        eventBus.$on('open_org_modal_invite', () => {
            this.getOrg()
        })
    },
    watch: {
        '$route.query.orginvite'(val) {
            if(val) {
                this.token = val
                let query = Object.assign({}, this.$route.query)
                delete query.orginvite
                this.$router.push({query})
                this.getOrg()
            }
        }
    },
    methods: {
        afterClose() {
            this.token = null
            this.org = null
        },
        async getOrg() {
            try {
                this.visible = true
                this.modalLoader = true
                const { data } = await this.$http.get(`/contractor_invites/${this.token}/`)
                if(data) {
                    this.org = data
                }
            } catch(error) {
                if(error.message) {
                    this.$message.error(error.message, 4)
                }
                console.log(error)
            } finally {
                this.modalLoader = false
            }
        },
        async inviteAccept() {
            try {
                this.inviteLoading = true
                const { data } = await this.$http.post('/contractor_invites/accept/', {
                    id: this.org.id
                })
                if(data) {
                    this.$message.info(this.$t('team.invitation_accepted'))
                    this.visible = false
                }
            } catch(error) {
                console.log(error)
                if(error.message)
                    this.$message.error(error.message)
                else
                    this.$message.error(this.$t('team.error'))
            } finally {
                this.inviteLoading = false
            }
        },
        async inviteReject() {
            try {
                this.rejectLoading = true
                const { data } = await this.$http.post('/contractor_invites/reject/', {
                    id: this.org.id
                })
                if(data) {
                    this.$message.info(this.$t('team.invitation_rejected'))
                    this.visible = false
                }
            } catch(error) {
                console.log(error)
                if(error.message)
                    this.$message.error(error.message)
                else
                    this.$message.error(this.$t('team.error'))
            } finally {
                this.rejectLoading = false
            }
        },
    },
    beforeDestroy() {
        eventBus.$off('open_org_modal_invite')
    }
}
</script>

<style lang="scss" scoped>
.org_invite_modal{
    text-align: center;
    h2{
        font-weight: 600;
        font-size: 18px;
        margin-bottom: 20px;
    }
    .wrap{
        max-width: 450px;
        margin: 0px auto;
    }
}
</style>