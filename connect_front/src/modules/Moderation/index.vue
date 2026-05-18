<template>
    <ModuleWrapper 
        :pageTitle="pageTitle"
        :pageRoutes="routes">
        <template v-if="!isMobile" v-slot:h_left>
            <PageFilter 
                :model="pageModel"
                :key="pageName"
                size="large"
                :page_name="pageName" />
        </template>
        <template v-if="!isMobile" v-slot:h_right>
            <SettingsButton
                :pageName="pageName"
                class="ml-2" />
        </template>

        <div 
            v-if="isMobile"
            class="float_add">
            <div class="filter_slot">
                <PageFilter 
                    :model="pageModel"
                    :key="pageName"
                    size="large"
                    :page_name="pageName" />
            </div>
        </div>
        <router-view />    
    </ModuleWrapper>
</template>

<script>
import routes from './config/router.js'

const pageModelByRouteName = {
    'moderation-list': 'catalogs.ContractorProfileRequestModel',
    'moderation-new-clients': 'users.NewUserInfoModel'
}

const pageNameByRouteName = {
    'moderation-list': 'catalogs.ContractorProfileRequestModel',
    'moderation-new-clients': 'users.NewUserInfoModel'
}

const tableTypeByRouteName = {
    'moderation-list': 'moderation',
    'moderation-new-clients': 'new-clients'
}

export default {
    components: {
        ModuleWrapper: () => import('@/components/ModuleWrapper/index.vue'),    
        SettingsButton: () => import('@/components/TableWidgets/SettingsButton'),
        PageFilter: () => import('@/components/PageFilter')
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        pageTitle() {
            return this.$route?.meta?.title || ''
        },
        pageModel() {
            return pageModelByRouteName[this.$route.name]
        },
        pageName() {
            return pageNameByRouteName[this.$route.name]
        },
        tableType() {
            return tableTypeByRouteName[this.$route.name]
        }
    },
    data() {
        return {
            routes
        }
    }
}
</script>