<template>
    <ModuleWrapper
        :pageTitle="pageTitle"
        :bodyPadding="false"
        :bodyXPadding="false"
        :bodyOHidden="!isInitPage">
        <template v-if="!isMobile && canCreate" v-slot:h_right>
            <div class="flex items-center gap-2">
                <a-button type="ui" icon="fi-rr-add-folder" flaticon @click="addSection()">
                    {{ $t('support.category') }}
                </a-button>
                <a-button type="ui" icon="fi-rr-layer-plus" flaticon @click="addChapter()">
                    {{ $t('support.subsection') }}
                </a-button>
                <a-button type="primary" icon="fi-rr-add-document" flaticon @click="addPage()">
                    {{ $t('support.createArticle') }}
                </a-button>
            </div>
        </template>
        <PageBase />
        <div
            v-if="isMobile && canCreate && isInitPage"
            class="float_add">
            <a-button
                flaticon
                shape="circle"
                class="mb-2"
                size="large"
                icon="fi-rr-add-folder"
                @click="addSection()" />
            <a-button
                flaticon
                shape="circle"
                size="large"
                class="mb-2"
                icon="fi-rr-layer-plus"
                @click="addChapter()" />
            <a-button
                flaticon
                shape="circle"
                size="large"
                type="primary"
                icon="fi-rr-add-document"
                @click="addPage()" />
        </div>
        <div
            v-else-if="isMobile && !isInitPage"
            class="float_add">
            <a-button
                flaticon
                shape="circle"
                size="large"
                type="primary"
                icon="fi-rr-menu-burger"
                @click="openMobileAside()" />
        </div>
    </ModuleWrapper>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'
import store from './store/index'

export default {
    components: {
        ModuleWrapper: () => import('@/components/ModuleWrapper/index.vue'),
        PageBase: () => import('./components/PageBase/index.vue')
    },
    computed: {
        pageTitle() {
            return this.$route?.meta?.title || this.$t('support.knowledgeBase')
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        user() {
            return this.$store.state.user.user
        },
        currentContractorId() {
            return this.user?.current_contractor?.id || null
        },
        isInitPage() {
            return !this.$route.params?.wikiType || !this.$route.params?.wikiId
        },
        canCreate() {
            return this.$store.getters['supportWiki/canCreate']
        }
    },
    watch: {
        currentContractorId: {
            handler(value) {
                this.fetchActionInfo(value)
            }
        }
    },
    created() {
        if(!this.$store.hasModule('supportWiki')) {
            this.$store.registerModule('supportWiki', store)
        }

        this.fetchActionInfo(this.currentContractorId)
        eventBus.$on('support_current_contractor_changed', this.handleCurrentContractorChange)
    },
    beforeDestroy() {
        eventBus.$off('support_current_contractor_changed', this.handleCurrentContractorChange)
    },
    methods: {
        async fetchActionInfo(contractorId) {
            if(!this.$store.hasModule('supportWiki')) return

            try {
                await this.$store.dispatch('supportWiki/fetchActionInfo', contractorId)
            } catch(error) {
                errorHandler({ error, show: false })
            }
        },
        async handleCurrentContractorChange({ contractorId = null } = {}) {
            const nextContractorId = contractorId || this.currentContractorId

            if(this.$route.name !== 'company-wiki') {
                return
            }

            if(this.$route.params?.wikiType && this.$route.params?.wikiId) {
                await this.$router.push({
                    name: 'company-wiki',
                    query: this.$route.query
                })
            }

            await this.fetchActionInfo(nextContractorId)

            this.$nextTick(() => {
                eventBus.$emit('support_wiki_force_reload')
            })
        },
        addSection() {
            eventBus.$emit('open_support_page_section_drawer')
        },
        addChapter() {
            eventBus.$emit('open_support_page_chapter_drawer')
        },
        addPage() {
            eventBus.$emit('open_support_page_page_drawer')
        },
        openMobileAside() {
            eventBus.$emit('support_open_mobile_aside')
        }
    }
}
</script>

<style lang="scss" scoped>
.support_mobile_actions{
    display: flex;
    align-items: center;
    gap: 8px;
}
</style>
