<template>
    <ModuleWrapper
        :pageTitle="pageTitle"
        :pageRoutes="routes"
        hideOneRoute
        :bodyPadding="true">
        <template v-if="!isMobile" #h_left>
            <div class="flex items-center gap-2">
                <PageFilter
                    v-if="isEmployees"
                    :model="initPageModel"
                    :key="initPageName"
                    size="large"
                    :page_name="initPageName" />
                <RangeInput />
            </div>
        </template>
        <Segmented
            v-if="isMobile && showViewSwitcher"
            v-model="currentView"
            class="workplan_view_switcher mb-3"
            :options="viewSwitcherOptions"
            @change="changeView" />
        <MobileRangeInput
            v-if="isMobile"
            class="mb-3" />
        <router-view
            :initPageName="initPageName"
            :initPageModel="initPageModel"
            :openUserModal="openUserModal"
            :dateRange="employeesDateRange" />
        <div
            v-if="isMobile && isEmployees"
            class="float_add">
            <div class="filter_slot">
                <PageFilter
                    :model="initPageModel"
                    :key="initPageName"
                    size="large"
                    :popoverMaxWidth="400"
                    :page_name="initPageName" />
            </div>
        </div>
        <EmployeePulseModal
            :visible="employeeModalVisible"
            :record="employeeModalRecord"
            @close="closeUserModal" />
    </ModuleWrapper>
</template>

<script>
import routes from './config/router.js'
import store from './store/index.js'
import eventBus from '@/utils/eventBus'

export default {
    components: {
        ModuleWrapper: () => import('@/components/ModuleWrapper/index.vue'),
        Segmented: () => import('@apps/UIModules/Segmented/index.vue'),
        PageFilter: () => import('@/components/PageFilter'),
        RangeInput: () => import('./components/RangeInput.vue'),
        MobileRangeInput: () => import('./components/MobileRangeInput.vue'),
        EmployeePulseModal: () => import('./components/EmployeePulseModal.vue')
    },
    created() {
        if (!this.$store.hasModule('workplan'))
            this.$store.registerModule('workplan', store)
    },
    beforeDestroy() {
        if (this.tableReloadTimer)
            clearTimeout(this.tableReloadTimer)
    },
    computed: {
        pageTitle() {
            const routeTitle = this.$route?.meta?.title || ''
            if (typeof routeTitle === 'string' && routeTitle.includes('.'))
                return this.$t(routeTitle)
            return routeTitle
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        isEmployees() {
            return this.$route.name === 'workplan-employees'
        },
        isConsolidation() {
            return this.$route.name === 'workplan-consolidation'
        },
        showViewSwitcher() {
            return this.isEmployees || this.isConsolidation
        },
        viewSwitcherOptions() {
            return [
                {
                    key: 'workplan-consolidation',
                    title: this.$t('workplan.consolidation_page_title')
                },
                {
                    key: 'workplan-employees',
                    title: this.$t('workplan.employees_page_title')
                }
            ]
        },
        initPageModel() {
            if (this.isEmployees)
                return 'day_summary.DaySummaryNoteModel'
            return ''
        },
        initPageName() {
            if (this.isEmployees)
                return 'day_summary.DaySummaryNoteModel_page_name'
            return ''
        },
        employeesDateRange() {
            return this.$store.state.workplan?.employeesDateRange || []
        },
        employeesDateRangeKey() {
            const start = this.employeesDateRange?.[0] ? this.$moment(this.employeesDateRange[0]).format('YYYY-MM-DDTHH:mm:ss') : ''
            const end = this.employeesDateRange?.[1] ? this.$moment(this.employeesDateRange[1]).format('YYYY-MM-DDTHH:mm:ss') : ''
            return `${start}_${end}`
        },
        currentView: {
            get() {
                return this.$route.name
            },
            set() {}
        }
    },
    watch: {
        employeesDateRangeKey() {
            this.scheduleEmployeesTableReload()
        }
    },
    data() {
        return {
            routes,
            employeeModalVisible: false,
            employeeModalRecord: null,
            tableReloadTimer: null
        }
    },
    methods: {
        changeView(name) {
            if (!name || name === this.$route.name) return
            this.$router.push({ name })
        },
        openUserModal(record) {
            this.employeeModalRecord = record || null
            this.employeeModalVisible = true
        },
        closeUserModal() {
            this.employeeModalVisible = false
            this.employeeModalRecord = null
        },
        scheduleEmployeesTableReload() {
            if (!this.isEmployees || !this.initPageModel || !this.initPageName) return
            if (this.tableReloadTimer)
                clearTimeout(this.tableReloadTimer)
            this.tableReloadTimer = setTimeout(() => {
                eventBus.$emit(`update_filter_${this.initPageModel}_${this.initPageName}`)
            }, 600)
        }
    }
}
</script>

<style lang="scss" scoped>
.workplan_view_switcher{
    &.segmented{
        flex-wrap: nowrap;
        &::v-deep{
            .segmented__item{
                width: 100%;
                text-align: center;
                justify-content: center;
            }
        }
    }
}
</style>
