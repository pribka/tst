<template>
    <div>
        <div v-if="isMobile && actions && actions.on_rework && actions.on_rework.availability" class="sidebar_item">
            <a-button
                type="flat_primary"
                size="large"
                flaticon
                block
                style="padding-left: 30px;padding-right: 30px;"
                :loading="loading"
                @click="$emit('on-rework')">
                {{ $t('approvals.on_rework') }}
            </a-button>
        </div>
        <div v-if="isMobile" class="sidebar_item">
            <a-tag :color="approvals.status.color" contrastText useTextColor block size="large" class="main_status">
                {{ approvals.status.name }}
            </a-tag>
        </div>
        <div v-if="approvals.amount_requested" class="sidebar_item">
            <div class="mb-1 opacity-60">{{ $t('approvals.detail_amount') }}</div>
            <div class="amount_sum">{{ formattedAmount }} &#8376;</div>
            <a-button 
                v-if="actions && actions.money_under_report && actions.money_under_report.availability" 
                block 
                :disabled="loading"
                class="mt-2"
                @click="moneyUnderReport()">
                {{ approvals.money_under_report ? $t('approvals.no_money_under_report') : $t('approvals.money_under_report') }}
            </a-button>
        </div>
        <template v-if="approvals.routes && approvals.routes.length">
            <div 
                v-for="route in approvals.routes"
                :key="route.id"
                class="sidebar_item">
                <div class="mb-1 opacity-60">
                    {{ route.workflow_position.name }}
                </div>
                <div>
                    <div 
                        v-for="rUser in route.request_route_user_through" 
                        :key="rUser.id"
                        class="flex items-center justify-between user_list_item">
                        <Profiler 
                            :user="rUser.user" 
                            initStatus
                            :avatarSize="28"
                            hideSupportTag
                            :getPopupContainer="trigger => trigger.parentNode" />
                        <div class="ml-2">
                            <a-tag :color="rUser.status.color" contrastText size="small">
                                {{ rUser.status.name }}
                            </a-tag>
                        </div>
                    </div>
                </div>
            </div>
        </template>
        <div 
            v-if="approvals.author" 
            class="sidebar_item">
            <div class="mb-1 opacity-60">
                {{ $t('approvals.author') }}
            </div>
            <div class="flex items-center">
                <Profiler 
                    :user="approvals.author" 
                    initStatus
                    :avatarSize="28"
                    hideSupportTag
                    :getPopupContainer="trigger => trigger.parentNode" />
            </div>
        </div>
        <div 
            v-if="approvals.organization" 
            class="sidebar_item">
            <div class="mb-1 opacity-60">
                {{$t('task.organization')}}
            </div>
            <div class="flex items-center" >
                <div>
                    <a-avatar 
                        :src="approvals.organization.logo" 
                        icon="team" 
                        :size="28" />
                </div>
                <span class="ml-2">{{approvals.organization.name}}</span>
            </div>
        </div>
        <div 
            v-if="approvals.project" 
            class="sidebar_item">
            <div class="mb-1 opacity-60">
                {{ formInfo.project ? formInfo.project.label : $t('task.project')}}
            </div>
            <div 
                class="flex items-center cursor-pointer" 
                @click="openProject('viewProject', approvals.project)">
                <div>
                    <a-avatar 
                        :src="workgroupLogoPath(approvals.project)" 
                        icon="team" 
                        :size="28" />
                </div>
                <span class="ml-2">{{approvals.project.name}}</span>
            </div>
        </div>
        <div 
            v-if="approvals.dead_line" 
            class="sidebar_item">
            <div class="mb-1 opacity-60">
                {{ formInfo.dead_line ? formInfo.dead_line.label : $t('approvals.dead_line') }}
            </div>
            <div class="flex items-center">
                {{ $moment(approvals.dead_line).format('DD.MM.YYYY') }}
            </div>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        approvals: {
            type: Object,
            required: true
        },
        closeDrawer: {
            type: Function,
            default: () => {}
        },
        formInfo: {
            type: Object,
            required: true
        },
        actions: {
            type: Object,
            default: () => null
        },
        moneyUnderReport: {
            type: Function,
            default: () => {}
        },
        loading: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        formattedAmount() {
            if (!this.approvals?.amount_requested) return ''

            const value = String(this.approvals.amount_requested)

            const [intPart, decimalPart] = value.split('.')

            const formattedInt = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')

            if (decimalPart && Number(decimalPart) !== 0) {
                return `${formattedInt}.${decimalPart}`
            }

            return formattedInt
        }
    },
    methods: {
        async openProject() {
            const query = JSON.parse(JSON.stringify(this.$route.query))
            query.viewProject = this.approvals.project.id
            this.$router.replace({query})
        },
        workgroupLogoPath(workgroup) {
            return workgroup?.workgroup_logo?.path || ''
        }
    }
}
</script>

<style lang="scss" scoped>
.user_list_item{
    &:not(:last-child){
        margin-bottom: 10px;
    }
    &::v-deep{
        .ant-tag.ant-tag-sm{
            line-height: 22px;
            padding: 0 8px;
        }
    }
}
.amount_sum{
    font-size: 20px;
    font-weight: 700;
}
.sidebar_item{
    &:not(:last-child){
        border-bottom: 1px solid #E5E7EF;
        padding-bottom: 15px;
    }
    &:not(:first-child){
        padding-top: 15px;
    }
}
</style>
