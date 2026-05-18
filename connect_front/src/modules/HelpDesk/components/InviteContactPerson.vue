<template>
    <div
        v-if="!contactPerson.user"
        class="flex items-start gap-1">
        <a-button
            @click="createInvite"
            :loading="getInviteLinkLoading"
            type="ui"
            v-tippy
            shape="circle"
            :content="$t('helpdesk.create_invitation')"
            flaticon
            icon="fi-rr-share" />
        <a-button
            @click="createInviteAndCopy"
            :loading="getInviteLinkLoading"
            type="ui"
            shape="circle"
            v-tippy
            flaticon
            :content="$t('copy_link')"
            icon="fi-rr-copy-alt" />
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'

export default {
    props: {
        contactPerson: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            inviteURL: "",
            getInviteLinkLoading: false
        }
    },
    beforeDestroy() {
        this.inviteURL = ''
    },
    methods: {
        async getInviteLink() {
            if (this.inviteURL) {
                return this.inviteURL
            }
            try {
                this.getInviteLinkLoading = true
                const params = {
                    contact_person: this.contactPerson.id
                }
                const { data } = await this.$http.get('/help_desk/customer_cards/contact_persons/invite/', { params })
                if(data) {
                    this.inviteURL = data.url
                }
                return this.inviteURL
            } catch(error) {
                errorHandler({ error })
                return null
            } finally {
                this.getInviteLinkLoading = false
            }
        },
        async createInvite() {
            const inviteURL = await this.getInviteLink()
            if (!inviteURL) return
            this.share()
        },
        async createInviteAndCopy() {
            const inviteURL = await this.getInviteLink()
            if (!inviteURL) return

            try {
                if (!navigator?.clipboard?.writeText) {
                    throw new Error('Clipboard API is not available')
                }
                await navigator.clipboard.writeText(inviteURL)
                this.$message.success(this.$t('link_succes_copy'))
            } catch(error) {
                this.$message.error(this.$t('copy_link_error'))
                console.error(error)
            }
        },
        share() {
            this.$store.commit("share/SET_SHARE_PARAMS", {
                model: 'invite_contact_person',
                shareId: this.contactPerson.id,
                object: { ...this.contactPerson, link: this.inviteURL, shareWidget: 'link' },
                messageText: `${this.$t('helpdesk.invitation_link')}: ${this.inviteURL}`,
                shareUrl: this.inviteURL,
                shareTitle: this.$t('helpdesk.invite_to_support_system'),
            });
        },
    }
}
</script>
