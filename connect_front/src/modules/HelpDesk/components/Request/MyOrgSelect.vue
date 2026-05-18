<template>
    <div :class="!isMobile && 'ml-4'">
        <AdminOrgSelect 
            v-model="selectedOrg" 
            :injectLoading="loading"
            :block="isMobile"
            :firstSelect="firstSelect"
            placement="bottomLeft"
            @change="changeSelectOrg" />
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'
export default {
    components: {
        AdminOrgSelect: () => import('../AdminOrgSelect.vue')
    },
    props: {
        orgInit: {
            type: Boolean,
            default: false
        },
        setOrgInit: {
            type: Function,
            default: () => {}
        },
        firstSelect: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        isMobile() { 
            return this.$store.state.isMobile
        }
    },
    data() {
        return {
            model: "help_desk.HelpDeskForClientTicketModel",
            pageName: "help_desk.HelpDeskForClientTicketModel_page",
            selectedOrg: null,
            loading: false,
            init: false
        }
    },
    created() {
        if(!this.orgInit) {
            this.getActiveOrg()
            this.setOrgInit(true)
        }
    },
    methods: {
        async changeSelectOrg(item) {
            try {
                this.loading = true
                await this.$http.post('/help_desk/select_org_admin/', {
                    id: item.id
                })
                eventBus.$emit(`update_filter_${this.model}_${this.pageName}`)
            } catch(error) {
                errorHandler({error})
            } finally {
                this.loading = false
            }
        },
        async getActiveOrg() {
            try {
                this.loading = true
                const { data } = await this.$http.get('/help_desk/select_org_admin/')
                if(data)
                    this.selectedOrg = data
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                this.loading = false
            }
        }
    }
}
</script>