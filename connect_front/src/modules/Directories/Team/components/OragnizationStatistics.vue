<template>
    <div>
        <div class="mb-4 relative">
            <template v-if="!isMobile">
                <swiper 
                    ref="swiper"
                    class="swiper"
                    :options="swiperOption">
                    <!-- Сотрудники -->
                    <swiper-slide>
                        <div class="py-2">
                            <div class="custom-h w-52 relative">
                                <div 
                                    class="w-52 h-full flex items-center text-white text-base py-2 px-4 cursor-pointer border custom_bg custom_hover rounded"
                                    @click="openOrganizationDrawer">
                                    <div class="font-medium text-3xl mr-3">
                                        {{ organization.members_count }}
                                    </div>
                                    <div class="font-medium leading-tight">
                                        {{ employeesLabel }}
                                    </div>
                                </div>
                                <template v-if="canManage">
                                    <template v-if="isDepartment">
                                        <a-button 
                                            v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }" 
                                            :content="$t('team.add_employee')"
                                            shape="circle"
                                            @click="addDepartmentEmployee"
                                            class="statistic_button w-9 h-9 text-base flex items-center justify-center">
                                            <i class="fi fi-rr-plus"></i>
                                        </a-button>
                                        <DrawerSelectUser
                                            ref="drawerSelectUser"
                                            v-model="usersToAdd"
                                            multiple
                                            hide
                                            :isDepartment="isDepartment"
                                            showAddEmployeeButton
                                            :parentId="parentId"
                                            :organizationId="organization.id"
                                            :title="$t('team.select_employee')" />
                                    </template>
                                    <template v-else>
                                        <a-button 
                                            v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }" 
                                            :content="$t('team.add_employee')"
                                            shape="circle"
                                            @click="openOrganizationDrawer"
                                            class="statistic_button w-9 h-9 text-base flex items-center justify-center">
                                            <i class="fi fi-rr-plus"></i>
                                        </a-button>
                                        <DrawerSelectUser
                                            ref="drawerSelectUser"
                                            v-model="usersToAdd"
                                            multiple
                                            hide
                                            :isDepartment="isDepartment"
                                            showAddEmployeeButton
                                            :parentId="parentId"
                                            :organizationId="organization.id"
                                            :title="$t('team.select_employee')" />        
                                    </template>
                                </template>
                            </div>
                        </div>
                    </swiper-slide>
                    <!-- Структурные организации -->
                    <swiper-slide v-if="!isDepartment">
                        <div class="py-2">
                            <div class="custom-h w-52 relative">
                                <div 
                                    class="w-52 h-full flex items-center text-white text-base py-2 px-4 cursor-pointer custom_bg_orange border rounded">
                                    <div class="font-medium text-3xl mr-3">
                                        {{ organization.structural_division_count }}
                                    </div>
                                    <div class="font-medium leading-tight">
                                        {{ structuresLabel }}
                                    </div>
                                </div>
                                <template v-if="canManage">
                                    <a-button 
                                        v-tippy="!isMobile ? { inertia: true, duration: '[600,300]',} : { touch: false }" 
                                        :content="$t('team.add_subdivision_tooltip')"
                                        shape="circle"
                                        @click="openOrganizationCreateDrawer('subdivision', organization.id)"
                                        class="statistic_button w-9 h-9 text-base flex items-center justify-center">
                                        <i class="fi fi-rr-plus"></i>
                                    </a-button>
                                </template>
                            </div>
                        </div>
                    </swiper-slide>
                    <!-- Внутренние организации -->
                    <swiper-slide v-if="!isDepartment">
                        <div class="py-2">
                            <div class="custom-h w-52 relative">
                                <div class="w-52 h-full flex items-center text-white text-base py-2 px-4 border custom_bg_blue rounded">
                                    <div class="font-medium text-3xl mr-3">
                                        {{ organization.department_count }}
                                    </div>
                                    <div class="font-medium leading-tight">
                                        {{ departmentsLable }}
                                    </div>
                                </div>
                                <template v-if="canManage">
                                    <a-button 
                                        v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }" 
                                        :content="$t('team.add_department_tooltip')"
                                        shape="circle"
                                        @click="openOrganizationCreateDrawer('department', organization.id)"
                                        class="statistic_button w-9 h-9 text-base flex items-center justify-center">
                                        <i class="fi fi-rr-plus"></i>
                                    </a-button>
                                </template>
                            </div>
                        </div>
                    </swiper-slide>
                    <!-- Проекты -->
                    <swiper-slide v-if="!isDepartment">
                        <div class="py-2">
                            <div class="custom-h w-52 relative">
                                <div class="w-52 h-full flex items-center text-white text-base py-2 px-4 border custom_purple_bg rounded">
                                    <div class="font-medium text-3xl mr-3">
                                        {{ organization.project_count || 0 }}
                                    </div>
                                    <div class="font-medium leading-tight">
                                        {{ projectLabel }}
                                    </div>
                                </div>
                                <template v-if="canCreateProject">
                                    <a-button 
                                        v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }" 
                                        :content="$t('team.add_project')"
                                        shape="circle"
                                        @click="openCreateProjectDrawer"
                                        class="statistic_button w-9 h-9 text-base flex items-center justify-center">
                                        <i class="fi fi-rr-plus"></i>
                                    </a-button>
                                </template>
                            </div>
                        </div>
                    </swiper-slide>
                    <!-- Задачи -->
                    <swiper-slide v-if="!isDepartment">
                        <div class="py-2">
                            <div class="custom-h w-52 relative">
                                <div 
                                    class="w-52 h-full flex items-center text-white text-base py-2 px-4 border cursor-pointer custom_red_bg rounded"
                                    @click="openStatistics">
                                    <div class="font-medium text-3xl mr-3">
                                        {{ activeTaskCount }}
                                    </div>
                                    <div class="font-medium leading-tight">
                                        {{ taskLabel }}
                                    </div>
                                </div>
                                <template v-if="canManage">
                                    <a-button 
                                        v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }" 
                                        :content="$t('team.add_task')"
                                        shape="circle"
                                        @click="openCreateTaskDrawer"
                                        class="statistic_button w-9 h-9 text-base flex items-center justify-center">
                                        <i class="fi fi-rr-plus"></i>
                                    </a-button>
                                </template>
                            </div>
                        </div>
                    </swiper-slide>
                </swiper>
                <div 
                    class="custom_arrow_left"
                    :class="`prev_${organization.id}_${parentId}`">
                    <!-- <i class="fi fi-rr-angle-left"></i> -->
                    <i class="fi fi-rr-arrow-small-left"></i>
                </div>
                <div
                    class="custom_arrow_right" 
                    :class="`next_${organization.id}_${parentId}`">
                    <!-- <i class="fi fi-rr-angle-right"></i> -->
                    <i class="fi fi-rr-arrow-small-right"></i>
                </div>
            </template>
            <template v-else>
                <div class="flex justify-between">
                    <div 
                        v-tippy="{ 
                            inertia: true, 
                            duration : '[600,300]',
                            trigger: 'click',
                            zIndex: 900}"
                        :content="$t('team.employees')"
                        class="flex flex-col items-center">
                        <div 
                            @click="openOrganizationDrawer"
                            class="relative px-2 pt-2 pb-1 border custom_bg rounded-full">
                            <template v-if="canManage">
                                <template v-if="isDepartment">
                                    <a-button 
                                        v-tippy="!isMobile ? { 
                                            inertia: true, 
                                            duration : '[600,300]',
                                            trigger: 'click',
                                            zIndex: 900} : { touch: false }" 
                                        :content="$t('team.add_employee')"
                                        shape="circle"
                                        @click="addDepartmentEmployee"
                                        class="statistic_button w-6 h-6 text-xs flex items-center justify-center">
                                        <i class="fi fi-rr-plus"></i>
                                    </a-button>
                                    <DrawerSelectUser
                                        ref="drawerSelectUser"
                                        v-model="usersToAdd"
                                        multiple
                                        hide
                                        :isDepartment="isDepartment"
                                        showAddEmployeeButton
                                        :parentId="parentId"
                                        :organizationId="organization.id"
                                        :title="$t('team.select_employee')" />
                                </template>
                                <template v-else>
                                    <a-button 
                                        v-tippy="!isMobile ? { 
                                            inertia: true, 
                                            duration : '[600,300]',
                                            trigger: 'click',
                                            zIndex: 900} : { touch: false }" 
                                        :content="$t('team.add_employee')"
                                        shape="circle"
                                        @click="openOrganizationDrawer"
                                        class="statistic_button w-6 h-6 text-xs flex items-center justify-center">
                                        <i class="fi fi-rr-plus"></i>
                                    </a-button>
                                    <DrawerSelectUser
                                        ref="drawerSelectUser"
                                        v-model="usersToAdd"
                                        multiple
                                        hide
                                        :isDepartment="isDepartment"
                                        showAddEmployeeButton
                                        :parentId="parentId"
                                        :organizationId="organization.id"
                                        :title="$t('team.select_employee')" />        
                                </template>
                            </template>
                            <i class="fi fi-rr-users-alt text-xl"></i>
                        </div>
                        <span class="leading-none mt-2 custom_bg">
                            {{ organization.members_count }}
                        </span>
                    </div>
                    <template v-if="!isDepartment">
                        <div 
                            v-tippy="{ 
                                inertia: true, 
                                duration : '[600,300]',
                                trigger: 'click',
                                zIndex: 900}"
                            :content="$t('team.structural_subdivisions')"
                            class="flex flex-col items-center">
                            <div class="relative px-2 pt-2 pb-1 border custom_bg_orange rounded-full">
                                <i class="fi fi-rr-sitemap text-xl"></i>
                                <template v-if="canManage">
                                    <a-button 
                                        v-tippy="!isMobile ? { 
                                            inertia: true, 
                                            duration : '[600,300]',
                                            trigger: 'click',
                                            zIndex: 900} : { touch: false }" 
                                        :content="$t('team.add_subdivision_tooltip')"
                                        shape="circle"
                                        @click="openOrganizationCreateDrawer('subdivision', organization.id)"
                                        class="statistic_button w-6 h-6 text-xs flex items-center justify-center">
                                        <i class="fi fi-rr-plus"></i>
                                    </a-button>
                                </template>
                            </div>
                            <span class="leading-none mt-2 custom_bg_orange">
                                {{ organization.structural_division_count }}
                            </span>
                        </div>
                        <div 
                            v-tippy="{ 
                                inertia: true, 
                                duration : '[600,300]',
                                trigger: 'click',
                                zIndex: 900}"
                            :content="$t('team.internal_subdivisions')"
                            class="flex flex-col items-center">
                            <div class="relative px-2 pt-2 pb-1 border custom_bg_blue rounded-full">
                                <i class="fi fi-rr-sitemap text-xl"></i>
                                <template v-if="canManage">
                                    <a-button 
                                        v-tippy="!isMobile ? { 
                                            inertia: true, 
                                            duration : '[600,300]',
                                            trigger: 'click',
                                            zIndex: 900} : { touch: false }" 
                                        :content="$t('team.add_department_tooltip')"
                                        shape="circle"
                                        @click="openOrganizationCreateDrawer('department', organization.id)"
                                        class="statistic_button w-6 h-6 text-xs flex items-center justify-center">
                                        <i class="fi fi-rr-plus"></i>
                                    </a-button>
                                </template>
                            </div>
                            <span class="leading-none mt-2 custom_bg_blue">
                                {{ organization.department_count }}
                            </span>
                        </div>
                        <div 
                            v-tippy="{ 
                                inertia: true, 
                                duration : '[600,300]',
                                trigger: 'click',
                                zIndex: 900}"
                            :content="$t('team.projects')"
                            class="flex flex-col items-center">
                            <div class="relative px-2 pt-2 pb-1 border custom_purple_bg rounded-full">
                                <i class="fi fi-rr-money-check text-xl"></i>
                                <template v-if="canCreateProject">
                                    <a-button 
                                        v-tippy="!isMobile ? { 
                                            inertia: true, 
                                            duration : '[600,300]',
                                            trigger: 'click',
                                            zIndex: 900} : { touch: false }" 
                                        :content="$t('team.add_project')"
                                        shape="circle"
                                        @click="openCreateProjectDrawer"
                                        class="statistic_button w-6 h-6 text-xs flex items-center justify-center">
                                        <i class="fi fi-rr-plus"></i>
                                    </a-button>
                                </template>
                            </div>
                            <span class="leading-none mt-2 custom_purple_bg">
                                {{ organization.project_count }}
                            </span>
                        </div>
                        <div 
                            v-tippy="{ 
                                inertia: true, 
                                duration : '[600,300]',
                                trigger: 'click',
                                zIndex: 900}"
                            :content="$t('team.active_tasks')"
                            class="flex flex-col items-center">
                            <div class="relative px-2 pt-2 pb-1 border custom_red_bg rounded-full">
                                <i class="fi fi-rr-list-check text-xl"></i>
                                <template v-if="canManage">
                                    <a-button 
                                        v-tippy="!isMobile ? { 
                                            inertia: true, 
                                            duration : '[600,300]',
                                            trigger: 'click',
                                            zIndex: 900} : { touch: false }" 
                                        :content="$t('team.add_task')"
                                        shape="circle"
                                        @click="openCreateTaskDrawer"
                                        class="statistic_button w-6 h-6 text-xs flex items-center justify-center">
                                        <i class="fi fi-rr-plus"></i>
                                    </a-button>
                                </template>
                            </div>
                            <span class="leading-none mt-2 custom_red_bg">
                                {{ activeTaskCount }}
                            </span>
                        </div>
                    </template>
                </div>
            </template>
        </div>
        <template v-if="!isDepartment">
            <div 
                class="mb-6"
                :class="isMobile && 'mobile_statistics -mt-4'">
                <div :class="isMobile ? 'mt-4 ' : 'pt-6'">
                    <a-radio-group 
                        v-model="statisticsSource" 
                        @change="changeStatisticsSource">
                        <a-radio 
                            value="organization">
                            {{ $t('team.organization_stats') }}
                        </a-radio>
                        <a-radio 
                            value="organization_with_children">
                            {{ $t('team.with_structural_subdivisions') }}
                        </a-radio>
                        <a-radio 
                            value="children">
                            {{ $t('team.structural_subdivisions_only') }}
                        </a-radio>
                    </a-radio-group>
                </div>
            </div>
            <div
                :class="isStatisticsLoading && 'opacity-40'" 
                class="pb-4 overflow-x-auto opacity_transition">
                <template v-if="!isMobile">
                    <ChartList
                        :taskStatistics="taskStatistics" />
                </template>
                <template v-else>
                    <div class="mt-4 ml-2 mobile_statistics_info">
                        <div 
                            v-for="(statistics, key) in percentageStatistics"
                            :key="key">
                            <template v-if="Number(statistics)">
                                <div class="flex justify-between custom_leading">
                                    <span>
                                        <a-badge :color="taskStatusColorByKey(key)" />
                                        <span class="mr-2">{{ taskStatusNameByKey(key) }}:</span>
                                    </span>
                                    <span>{{ statistics }}%</span>
                                </div>
                            </template>
                        </div>
                    </div>
                </template>
            </div>
        </template>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { mapState } from 'vuex'
import { Swiper, SwiperSlide } from 'vue-awesome-swiper'
import 'swiper/css/swiper.css'

export default {
    components: {
        DrawerSelectUser: () => import('./Drawers/DrawerSelectUser.vue'),
        Swiper,
        SwiperSlide,
        ChartList: () => import('./Statistics/ChartList.vue')
    },
    props: {
        organization: {
            type: Object,
            required: true
        },
        isDepartment: {
            type: Boolean,
            default: false
        },
        parentId: {
            type: String,
            default: null
        },
        parentMemberCount: {
            type: Number,
            default: null
        },
        isExpand: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            usersToAdd: [],

            swiperOption: {
                spaceBetween: 20,
                slidesPerView: 'auto',
                navigation: {
                    nextEl: `.next_${this.organization.id}_${this.parentId}`,
                    prevEl: `.prev_${this.organization.id}_${this.parentId}`
                }
            },
            taskStatistics: null,
            statisticsSource: 'organization',
            isStatisticsLoading: false,

        }
    },
    computed: {
        ...mapState({
            departments: state => state.organization.departments,
            organizations: state => state.organization.organizations,
            organizationChildren: state => state.organization.organizationChildren,
            actionInfo: state => state.organization.actionInfo
        }),
        activeTaskCount() {
            if(this.taskStatistics) {
                const activeTaskStatistics = JSON.parse(JSON.stringify(this.taskStatistics))
                delete activeTaskStatistics.completed
                delete activeTaskStatistics.overdue
                let resultCount = 0
                for(const key in activeTaskStatistics) {
                    resultCount += activeTaskStatistics[key]
                }
                return resultCount
            }
            return this.organization.task_count || 0
        },
        
        taskCount() {
            return this.allTasksStatistics.reduce((globalTaskCount, taskCount) => globalTaskCount + taskCount, 0)
        },
        permissions() {
            return this.actionInfo?.[this.organization.id]
        },
        parentPermissions() {
            return this.actionInfo?.[this.parentId]
        },
        employeesLabel() {
            const caseList = [
                this.$t('team.employee_1'), 
                this.$t('team.employee_2'), 
                this.$t('team.employee_5')
            ] 
            const count = this.organization.members_count
            return caseList[this.getCaseIndex(count)]
        },
        projectLabel() {
            const caseList = [
                this.$t('team.project_1'), 
                this.$t('team.project_2'), 
                this.$t('team.project_5')
            ] 
            const count = this.organization.project_count
            return caseList[this.getCaseIndex(count)]
        },
        taskLabel() {
            const caseList = [
                this.$t('team.active_task_1'), 
                this.$t('team.active_task_2'),
                this.$t('team.active_task_5'),
            ] 
            const count = this.organization.task_count
            return caseList[this.getCaseIndex(count)]
        },
        structuresLabel() {
            const caseList = [
                this.$t('team.structural_subdivision_1'), 
                this.$t('team.structural_subdivision_2'), 
                this.$t('team.structural_subdivision_5')
            ] 
            const count = this.organization.structural_division_count
            return caseList[this.getCaseIndex(count)]
        },
        departmentsLable() {
            const caseList = [
                this.$t('team.internal_subdivision_1'), 
                this.$t('team.internal_subdivision_2'), 
                this.$t('team.internal_subdivision_5')
            ] 
            const count = this.organization.department_count
            return caseList[this.getCaseIndex(count)]
        },        
        isMobile() {
            return this.$store.state.isMobile
        },
        canManage() {
            if(this.isDepartment)
                return this.parentPermissions?.manage?.availability
            return this.permissions?.manage?.availability
        },
        canCreateProject() {
            if(this.isDepartment)
                return this.parentPermissions?.create_project?.availability
            return this.permissions?.create_project?.availability
        },
        allTasksStatistics() {
            const series = []
            for(const key in this.taskStatistics) {
                series.push(this.taskStatistics[key])
            }
            return series
        },
        percentageStatistics() {
            const percentages = {} 
            // JSON.parse(JSON.stringify(this.taskStatistics))
            for(const key in this.taskStatistics) {
                const percentage = this.taskStatistics[key] / this.taskCount * 100
                percentages[key] = isNaN(percentage) ? 0 : percentage.toFixed(2)
            }
            return percentages
        },
        params() {
            if(this.statisticsSource === 'children') {
                return {
                    display: 'children'
                }
            }
            if(this.statisticsSource === 'organization_with_children') {
                return {
                    display: 'node_children'
                }
            }
            return {}
        }

    },
    created() {
        if(!this.isDepartment) {
            this.getStatisticsByOrganization()
        }    
    },
    methods: {
        taskStatusNameByKey(key) {
            const statusMap = {
                'new': this.$t('team.task_status_new'),
                'in_work': this.$t('team.task_status_in_work'),
                'on_pause': this.$t('team.task_status_on_pause'),
                'on_check': this.$t('team.task_status_on_check'),
                'on_rework': this.$t('team.task_status_on_rework'),
                'completed': this.$t('team.task_status_completed'),
                'overdue': this.$t('team.task_status_overdue')
            }
            return statusMap[key] || ''
        },
        taskStatusColorByKey(key) {
            switch(key) {
            case 'new': return '#80c6ff'
            case 'in_work': return '#ca97ca'
            case 'on_pause': return '#ffc618'
            case 'on_check': return '#c2d88e'
            case 'on_rework': return '#f7636f'
            case 'completed': return '#c2d88e'
            case 'overdue': return '#f7636f'
            }
            return ''
        },
        async changeStatisticsSource() {
            this.getStatisticsByOrganization(this.statisticsSource)
        },
        async getStatisticsByOrganization(source='organization') {
            const url = `/users/my_organizations/${this.organization.id}/task_count/`
            this.isStatisticsLoading = true
            try {
                const { data } = await this.$http.get(url, { params: this.params })
                this.taskStatistics = data
            } catch(error) {
                console.error(error)
                this.$message.error(this.$t('team.failed_to_get_statistics'))
            } finally {
                this.isStatisticsLoading = false
            }
        },
        openOrganizationDrawer() {
            const query = {
                organization_drawer: 'detail',
                organization_id: this.organization.id,
            }
            if(this.parentId) {
                query.parent_id = this.parentId
            }
            if(this.isDepartment) {
                query.is_department = true
            }
            this.$router.push({ query })
        },
        openStatistics() {
            const query = {
                organization_drawer: 'statistics',
                organization_id: this.organization.id,
            }
            if(this.parentId) {
                query.parent_id = this.parentId
            }
            if(this.isDepartment) {
                query.is_department = true
            }
            this.$router.push({ query })
        },
        openCreateProjectDrawer() {
            eventBus.$emit('open_create_project_drawer', ({ 
                organization: this.organization
            }))
        },
        openCreateTaskDrawer() {
            eventBus.$emit('add_task_modal_watch', {
                type: 'add_task', 
                data: {
                    organization: this.organization
                }
            })
        },
        openInvite() {
            eventBus.$emit('open_invite', { 
                organizationId: this.organization.id, 
                isDepartment: this.isDepartment
            })
        },
        openOrganizationInvite() {
            eventBus.$emit('invite_organization', { 
                organization: this.organization,
                isSubdivision: true
            })
        },
        openOrganizationCreateDrawer(organizationType, organizationParent) {
            eventBus.$emit('create_organization', { 
                organizationType, 
                organizationParent, 
                organization: this.organization,
                isDepartment: organizationType === 'department'
            })
        },
        openDepartmentDrawer() {
            eventBus.$emit('open_department_drawer', { organization: this.organization })
        },
        addDepartmentEmployee() {
            this.$refs.drawerSelectUser.open()
        },

        /**
         * Возвращает индекс склонения.<br>
         * На примере слова "Сотрудник":<br>
         * 0 - "Сотрудник",<br>
         * 1 - "Сотрудника",<br>
         * 2 - "Сотрудников"
         * @param {Number} count 
         */
        getCaseIndex(count) {
            if((count < 5) || (count > 20)) {
                const remaind = count % 10
                if(remaind === 1)
                    return 0
                if((remaind > 1) && (remaind < 5))
                    return 1
            } 
            return 2
        }
    }
}
</script>

<style scoped lang="scss">
$breakpoint: 600px;
.mobile_statistics_info {
    width: 200px;
    margin-left: auto;
    @media(max-width: $breakpoint) {
        width: 100%;
    }
}
.mobile_statistics {
    display: flex;
    justify-content: space-between;
    @media(max-width: $breakpoint) {
        flex-direction: column;
    }
}
.custom_leading {
    line-height: 30px;
}
.custom_arrow_left,
.custom_arrow_right {
    position: absolute;
    top: 50%;

    display: flex;
    align-items: center;
    justify-content: center;
    
    width: 36px;
    height: 36px;
    
    color: var(--blue);
    font-size: 20px;
    border-radius: 100%;
    border: 1px solid var(--blue);
    transform: translateY(-50%);
    transition: 
        border-color 0.3s ease,
        color 0.3s ease;
    &:hover {
        opacity: 0.6;
    }
}
.swiper-button-disabled.custom_arrow_left,
.swiper-button-disabled.custom_arrow_right {
    border-color: #d9d9d9;
    color: #d9d9d9;
    cursor: default;
}
.custom_arrow_right {
    right: 0;
}
.opacity_transition {
    transition: opacity 0.3s ease;
}
.custom_border_color {
    border-color: var(--bgColor6);
}
.custom-h {
    height: 60px;
}
.swiper {
    width: calc(100% - 2 * 50px);
}
.swiper-slide {
    width: 220px;
}
.custom_hover {
    transition: background 0.3s ease;
}
.custom_hover:hover {
    background-color: #d9ffd8;
}

.custom_bg_blue {
    color: var(--blue);
    border-color: var(--blue);
}
.custom_bg {
    color: #53E151;
    border-color: #53E151;
}
.custom_purple_bg {
    color: #9951e1;
    border-color: #9951e1;
}

.custom_red_bg {
    color: #ff7b75;
    border-color: #ff7b75;
    transition: background 0.3s ease;
}
.custom_red_bg:hover {
    background: #ff7b7530;
}
.custom_hover_blue {
    transition: background 0.3s ease;
}
.custom_hover_blue:hover {
    background-color: #cfe9ff;
}
.custom_bg_orange {
    color: #e1af4e;
    border-color: #e1af4e;
    transition: background 0.3s ease;
}

.statistic_button {
    position: absolute;
    right: 0;
    bottom: 0;
    transform: translate(30%, 20%);
}
::v-deep {
    .statistic_button.ant-btn-circle {
        min-width: 0;
    }
}
</style>