<template>
    <a-spin :spinning="loading" class="w-full report_spin">
        <div class="report_dashboard">
            <div class="pb-3">
                <DSelect
                    v-model="organization"
                    size="large"
                    apiUrl="/users/my_organizations/"
                    class="w-full"
                    firstSelected
                    oneSelect
                    showPlaceholder
                    infinity
                    labelKey="name"
                    :placeholder="$t('reports_mobule.select_org')"
                    @change="orgChange" />
            </div>
            <div class="report_dashboard__grid">
                <div class="grid gap-4 grid-cols-1 md:grid-cols-2">
                    <ReportTask :statData="statData" />
                    <ReportProject :statData="statProjectData" />
                </div>
            </div>
        </div>
    </a-spin>
</template>

<script>
export default {
    components: {
        ReportTask: () => import('../ReportTask.vue'),
        ReportProject: () => import('../ReportProject.vue'),
        DSelect: () => import('@apps/DrawerSelect/Select.vue')
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    data() {
        return {
            loading: false,
            organization: null,
            statData: null,
            statProjectData: null
        }
    },
    watch: {
        organization() {
            this.getReportsTask()
            this.getReportsProjects()
        }
    },
    methods: {
        orgChange() {
            this.getReportsTask()
            this.getReportsProjects()
        },
        async getReportsTask() {
            try {
                this.loading = true
                const { data } = await this.$http.get('/contractor_reports/contractor_tasks/', {
                    params: {
                        organization: this.organization
                    }
                })
                this.statData = data
            } catch(error) {
                console.error(error)
            } finally {
                this.loading = false
            }
        },
        async getReportsProjects() {
            try {
                this.loading = true
                const { data } = await this.$http.get('/contractor_reports/contractor_projects/', {
                    params: {
                        organization: this.organization
                    }
                })
                this.statProjectData = data
            } catch(error) {
                console.error(error)
            } finally {
                this.loading = false
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.report_dashboard{
    display: flex;
    flex-direction: column;
    height: 100%;
    &__grid{
        flex-grow: 1;
    }
}
.report_spin{
    height: 100%;
    &::v-deep{
        .ant-spin-container{
            height: 100%;
        }
    }
}
</style>