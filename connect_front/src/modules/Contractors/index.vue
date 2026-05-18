<template>
    <div :class="isMobile ? 'mobile_wrapper' : 'wrapper flex flex-col flex-grow'">
        <h1 v-if="isMobile && pageH1Title" class="m_page_title">
            {{ pageH1Title }}
        </h1>
        <ContractorsView
            :pageName="pageName">
            <template v-slot:pageFilter>
                <PageFilter
                    :model="model"
                    :key="pageName"
                    size="large"
                    :page_name="pageName"/>
            </template>
        </ContractorsView>
    </div>
</template>

<script>
import { mapState } from 'vuex'
export default {
    components: {
        ContractorsView: () => import('./components/ViewTypes/ContractorsView.vue'),
        PageFilter: () => import('@/components/PageFilter')
    },
    data() {
        return {
        }
    },
    computed: {
        ...mapState({
            contractorsType: state => state.contractors.contractorsType,
            models: state => state.contractors.models
        }),
        pageH1Title() {
            return this.$route?.meta?.title ? this.$route.meta.title : null
        },
        model() {
            return this.models[this.contractorsType]
        },
        pageName() {
            return `${this.model}_${this.contractorsType}`
        },
        isMobile() {
            return this.$store.state.isMobile
        },
    },
    methods: {
        changeTabHandler(tab) {
            this.contractorsType = tab
        }
    }
}
</script>

<style scoped>
.search {
    padding: 15px;
    padding-top: 0;
}
.wrapper {
    padding: 20px 30px;
}

.mobile_wrapper {
    padding: 15px;
}
</style>