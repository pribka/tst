<template>
    <div>
        <div class="flex">
            <Segmented  
                v-model="templatesSource"
                @change="changeTemplateSource"
                :options="tabOptions" />
        </div>
        <TemplateGrid
            ref="templateGrid"
            :templatesSource="templatesSource"
            class="mt-3" />
    </div>
</template>

<script>
export default {
    components: {
        Segmented: () => import('@apps/UIModules/Segmented'),
        TemplateGrid: () => import('../components/Templates/TemplateGrid.vue')
    },
    props: {
        tableType: {
            type: String,
            default: 'projects'
        },
    },
    computed: {
        pageTitle() {
            return this.$route?.meta?.title || ''
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        tabOptions() {
            return [{ key: 'templates', title: this.$t('reports_mobule.report_catalog') }, { key: 'my_templates', title: this.$t('reports_mobule.save_versions') },]
        }
    },
    data() {
        return {
            templatesSource: 'templates'
        }
    },
    mounted() {
        this.getTemplates()
    },
    methods: {
        changeTemplateSource() {
            this.$refs.templateGrid.reload()
        },
        getTemplates() {
            this.$http('reports/report_settings/')
                .then(({ data }) => {
                    this.templateList = data.results
                })
                .catch(error => {
                    console.error(error)
                })
        }
    }
}
</script>

<style lang="scss" scoped>
.header__button + .header__button {
    margin-left: 10px;
}
</style>