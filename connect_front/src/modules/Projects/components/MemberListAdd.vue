<template>
    <InviteButton
        class="w-full"
        :requestData="requestData"
        :addToMembersList="addToMembersList"
        :updatePartisipants="updatePartisipants" />
</template>

<script>
import UserDrawer from '@apps/DrawerSelect/index.vue'
import eventBus from "@/utils/eventBus"
import InviteButton from './InviteButton.vue'
import Vue from 'vue'
import { errorHandler } from '@/utils/index.js'
export default {
    components: {
        InviteButton
    },
    props: {
        id: {
            type: String,
            default: ''
        },
        requestData: {
            type: Object,
            required: true
        },
        updatePartisipants: {
            type: Function,
            default: () => {}
        },
        addToMembersList: {
            type: Function,
            default: () => {}
        },    
    },
    data() {
        return {
            form: {
                partisipants: [],
                metadata: {
                    partisipants: []
                }
            },
            loading: false,
        }
    },
    computed: {
        pageName() {
            return `members_${this.id}`
        },
    },
    methods: {        
        commitPartisipants() {
            if(this.form.partisipants.length === 0)
                return 0

            const prifileIds = this.form.partisipants.map(user => user.id)
            const payload = { profile_id: prifileIds }
            this.$http.post(`/work_groups/workgroups/${this.id}/send_invitations/`, payload)
                .then(() => {
                    eventBus.$emit(`update_member_list_${this.id}`)
                })
                .catch(error => {
                    errorHandler({error})
                })
        },
        changeMetadata({key, value}) {
            Vue.set(this.form.metadata, key, value)
        },
    }
}
</script>

