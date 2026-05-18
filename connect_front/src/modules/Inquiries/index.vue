<template>
    <ModuleWrapper :pageTitle="pageTitle">
        <template v-if="!isMobile" v-slot:h_left>
            <PageFilter
                :model="model"
                :key="page_name"
                class="mr-2"
                size="large"
                :popoverMaxWidth="400"
                :page_name="page_name" />
        </template>
        <template v-if="!isMobile" v-slot:h_right>
            <a-button
                type="primary" 
                icon="fi-rr-plus-small"
                flaticon
                @click="newInquir()">
                {{ $t('inquiries.resAdd') }}
            </a-button>
            <HelpButton partCode="inquiries" type="button" class="ml-2" />
        </template>
        <component
            :is="listComponent"
            :page_name="page_name"
            :name="page_name"
            :model="model"
            class="w-full"
            showPageTitle
            showHeader
            showFilter
            showAddButton
            :newInquir="newInquir">
        </component>
        <NewInquir :pageName="page_name" />
    </ModuleWrapper>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    name: 'InquiriesIndex',
    components: {
        ModuleWrapper: () => import('@/components/ModuleWrapper/index.vue'),
        PageFilter: () => import('@/components/PageFilter'),
        NewInquir: () => import('./components/NewInquir'),
        HelpButton: () => import('@apps/Support/components/HelpButton.vue')
    },
    data() {
        return {
            page_name: 'citizen_inquiries_list',
            model: 'risk_assessment.RiskAssessmentModel',
            listComponent: null
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        pageTitle() {
            return this.$route?.meta?.title || ''
        },
    },
    created() {
        this.listComponent = this.isMobile
            ? () => import('./components/MobileList.vue')
            : () => import('./components/List.vue')
    },
    methods: {
        newInquir() {
            eventBus.$emit('new_inquir')
        }
    }
}
</script>
