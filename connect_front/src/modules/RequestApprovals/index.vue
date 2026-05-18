<template>
    <ModuleWrapper :pageTitle="pageTitle" :headerBg="!isMobile">
        <template v-if="!isMobile" v-slot:h_left>
            <PageFilter
                :model="pageModel"
                :key="page_name"
                size="large"
                :page_name="page_name" />
        </template>
        <template v-slot:h_right>
            <a-button 
                v-if="!isMobile && useAddButton"
                class="header__button"
                icon="fi-rr-plus-small" 
                flaticon
                type="primary"
                @click="createHandler()" >
                {{ $t('approvals.add_request') }}
            </a-button>
            <HelpButton partCode="request-approvals" type="button" class="ml-2" />
            <component
                v-if="!isMobile"
                :is="settingsButtonWidget"   
                :pageName="page_name"
                size="default"
                class="ml-2" />
        </template>
        <component 
            :is="listComponent"
            :pageModel="pageModel"
            :page_name="page_name" />
        <div 
            v-if="isMobile"
            class="float_add">
            <div class="filter_slot">
                <PageFilter
                    :model="pageModel"
                    :key="page_name"
                    size="large"
                    :popoverMaxWidth="400"
                    :page_name="page_name" />
            </div>
            <a-button 
                flaticon
                shape="circle"
                size="large"
                type="primary"
                icon="fi-rr-plus"
                @click="createHandler()" />
        </div>
    </ModuleWrapper>
</template>

<script>
import eventBus from "@/utils/eventBus"
export default {
    name: 'RequestApprovalsModule',
    components: {
        PageFilter: () => import('@/components/PageFilter'),
        ModuleWrapper: () => import('@/components/ModuleWrapper/index.vue'),
        UniversalTable: () => import('@/components/TableWidgets/UniversalTable'),
        SettingsButton: () => import('@/components/TableWidgets/SettingsButton'),
        HelpButton: () => import('@apps/Support/components/HelpButton.vue'),
    },
    props: {
        pageModel: {
            type: String,
            default: 'processes.WorkflowRequestModel'
        },
        page_name: {
            type: String,
            default: 'page_list_processes.WorkflowRequestModel'
        }
    },
    computed: {
        settingsButtonWidget() {
            return () => import(/* webpackMode: "lazy" */'@/components/TableWidgets/SettingsButton')
        },
        currentRoute() {
            return this.$route.name
        },
        pageTitle() {
            return this.$route?.meta?.title || ''
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        getRouteInfo() {
            return this.$store.getters['navigation/getRouteInfo'](this.currentRoute)
        }, 
        useAddButton() {
            if(this.getRouteInfo?.pageActions?.add) 
                return true
            return null
        },
    },
    data() {
        return {
            listComponent: null
        }
    },
    created() {
        this.listComponent = this.isMobile
            ? () => import('./List.vue')
            : () => import('./Table.vue')
    },
    methods: {
        createHandler() {
            eventBus.$emit('add_request_approvals')
        }
    }
}
</script>
