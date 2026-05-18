<template>
    <ModuleWrapper
        :pageTitle="pageTitle"
        :headerBg="!isMobile"
        :pageRoutes="pageRoutes"
        hideOneRoute
        :bodyPadding="isWrapperInit ? true : false"
        :bodyOHidden="isWrapperInit ? false : true">
        <template v-if="!isMobile" v-slot:h_left>
            <PageFilter
                v-if="filterShow"
                :model="initPageModel"
                :key="initPageName"
                size="large"
                :popoverMaxWidth="filterWidth"
                :page_name="initPageName" />
            <!--
                <MyOrgSelect
                v-if="isRequest"
                :orgInit="orgInit"
                firstSelect
                :setOrgInit="setOrgInit" />-->
        </template>
        <template v-if="!isMobile" v-slot:h_right>
            <template v-if="showAddButton">
                <a-button
                    class="header__button"
                    icon="fi-rr-plus-small"
                    flaticon
                    type="primary"
                    @click="addHandler()">
                    {{ addButtonText }}
                </a-button>
            </template>
            <HelpButton v-if="isTickets || isClients || isUnconfirmedAppeals || isSpam || isCategories || isPositions" partCode="helpdesk" type="button" class="ml-2" />
            <component
                v-if="viewType === 'table' || viewType === 'list'"
                :is="settingsButtonWidget"
                :pageName="initPageName"
                :key="$route.name"
                size="default"
                class="ml-2" />
        </template>
        <router-view
            :changeMainViewType="changeMainViewType"
            :initPageName="initPageName"
            :initPageModel="initPageModel" />
    </ModuleWrapper>
</template>

<script>
import routes from './config/router.js'
import eventBus from '@/utils/eventBus'
export default {
    components: {
        PageFilter: () => import('@/components/PageFilter'),
        ModuleWrapper: () => import('@/components/ModuleWrapper/index.vue'),
        HelpButton: () => import('@apps/Support/components/HelpButton.vue'),
        //MyOrgSelect: () => import('./components/Request/MyOrgSelect.vue')
    },
    computed: {
        filterShow() {
            return true
        },
        addButtonText() {
            if (this.isClients)
                return this.$t('helpdesk.create_contractor')
            if (this.isTickets)
                return this.$t('helpdesk.create_appeal')
            if (this.isRequest)
                return this.$t('helpdesk.create_ticket')
            return this.$t('helpdesk.create')
        },
        filterWidth() {
            if (this.isClients) { return 600 }
            return null
        },
        showAddButton() {
            return this.getRouteInfo?.pageActions?.add
        },
        getRouteInfo() {
            return this.$store.getters['navigation/getRouteInfo'](this.$route.name)
        },
        apiRoute() {
            return this.$store.state.navigation?.apiRoute || []
        },
        pageTitle() {
            return this.$route?.meta?.title || ''
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        isClients() {
            return this.$route.name === 'clients'
        },
        isSpam() {
            return this.$route.name === 'spam'
        },
        isRequest() {
            return this.$route.name === 'request'
        },
        isCategories() {
            return this.$route.name === 'categories'
        },
        isPositions() {
            return this.$route.name === 'positions'
        },
        isTickets() {
            return this.$route.name === 'tickets'
        },
        isUnconfirmedAppeals() {
            return this.$route.name === 'unconfirmed_appeals'
        },
        isWrapperInit() {
            if(this.isTickets || this.isUnconfirmedAppeals) {
                if(this.viewType === 'table' || this.viewType === 'list')
                    return true
                return false
            }
            return true
        },
        initPageModel() {
            if (this.isClients)
                return 'help_desk.CustomerCardModel'
            if (this.isSpam)
                return 'help_desk.ContactPersonModel'
            if (this.isRequest)
                return 'help_desk.HelpDeskTicketModel'
            if (this.isCategories)
                return 'help_desk.HelpDeskTicketCategoryModel'
            if (this.isPositions)
                return 'help_desk.ContactPersonPostModel'
            return 'help_desk.HelpDeskTicketModel'
        },
        initPageName() {
            if(this.isClients)
                return 'list_help_desk.CustomerCardModel'
            if (this.isSpam)
                return 'list_help_desk.SpamContactPersonModel'
            if (this.isUnconfirmedAppeals)
                return 'help_desk.UnconfirmedAppealsPage'
            if (this.isRequest)
                return 'help_desk.HelpDeskForClientTicketModel_page'
            if (this.isCategories)
                return 'help_desk.HelpDeskTicketCategoryModel'
            if (this.isPositions)
                return 'help_desk.ContactPersonPostModel'
            return 'help_desk.HelpDeskTicketModel_page'
        },
        settingsButtonWidget() {
            return () => import(/* webpackMode: "lazy" */'@/components/TableWidgets/SettingsButton')
        },
        pageRoutes() {
            const names = new Set()
            const walk = o => {
                if (!o || typeof o !== 'object') return
                Object.keys(o).forEach(k => {
                    names.add(k)
                    const v = o[k]
                    if (v && typeof v === 'object') walk(v)
                })
            }
            walk(this.apiRoute)

            const allowed = new Set(
                this.isRequest
                    ? ['request']
                    : ['tickets', 'clients', 'spam', 'categories', 'positions']
            )

            const filterRoutes = list => {
                if (!Array.isArray(list)) return []
                return list.reduce((acc, r) => {
                    const includeSelf = allowed.has(r.name)
                    if (includeSelf) {
                        const copy = { ...r }
                        acc.push(copy)
                    }
                    return acc
                }, [])
            }
            return filterRoutes(this.routes)
        }
    },
    data() {
        return {
            routes,
            viewType: 'list',
            orgInit: false
        }
    },
    methods: {
        addHandler() {
            if (this.isClients) { return this.addClient() }
            if (this.isTickets) { return this.addTicket() }
            if (this.isRequest) { return this.addRequestTicket() }
            if (this.isCategories) { return this.addCategpries() }
            if (this.isPositions) { return this.addPositions() }
        },
        setOrgInit(init) {
            this.orgInit = init
        },
        changeMainViewType(value) {
            this.viewType = value
        },
        addCategpries() {
            eventBus.$emit('open_modal_category_add')
        },
        addPositions() {
            eventBus.$emit('open_modal_position_add')
        },
        addClient() {
            eventBus.$emit('helpdesc_add_client')
        },
        addTicket() {
            eventBus.$emit('helpdesc_add_tickets')
        },
        addRequestTicket() {
            eventBus.$emit('helpdesc_add_request_tickets')
        }
    }
}
</script>