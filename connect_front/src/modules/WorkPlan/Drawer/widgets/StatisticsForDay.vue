<template>
    <div
        v-if="dayStatistics"
        class="list_item rounded-lg mr-2"
        style="background: rgb(223, 237, 255);padding-right: 10px;">
        <div class="list_head whitespace-nowrap">
            <div class="icon_wrapper rounded-lg">
                <div class="icon_bg" style="background: #4777FF;" />
                <i class="fi fi-rr-clock" style="color: #4777FF;" />
            </div>
            <div class="info_wrapper">
                <div class="info_wrapper__label opacity-60">
                    {{ $t('workplan.total_spent') }}
                </div>
                <div class="info_wrapper__value">
                    {{ secondsFormat(dayStatistics.total_duration) }}
                </div>
            </div>
            <component
                :is="reportButtonComponent"
                v-if="reportButtonComponent"
                :reportSetting="reportSetting"
                :payloadTransformer="prepareReportPayload"
                :showText="false"
                type="link"
                btnClass="flex items-center justify-center ant-btn-icon-only"
                class="report_button" />
        </div>
    </div>
</template>

<script>
import { secondsFormat } from '@/utils/utils.js'

export default {
    props: {
        storeKey: {
            type: String,
            required: true
        }
    },
    computed: {
        dayStatistics() {
            return this.$store.state.workplan.day_statistics?.[this.storeKey]?.data || null
        },
        reportSetting() {
            return this.$store.state.workplan.reportSettings?.[this.storeKey] || null
        },
        mainDate() {
            return this.$store.state.workplan.mainDate?.[this.storeKey] || []
        },
        reportUsers() {
            const selectedUsers = this.$store.state.workplan.user?.[this.storeKey] || []
            if (selectedUsers.length) {
                return selectedUsers
            }

            const currentUser = this.$store.state.user?.user
            return currentUser?.id ? [currentUser] : []
        },
        hasSelectedUsers() {
            return Boolean(this.$store.state.workplan.user?.[this.storeKey]?.length)
        },
        currentContractor() {
            if (this.hasSelectedUsers) {
                return null
            }

            return this.$store.state.user?.user?.current_contractor || null
        },
        reportButtonComponent() {
            if(!this.reportSetting)
                return null
            return () => import('@/modules/Reports/components/OpenReportBySettingButton.vue')
        }
    },
    methods: {
        secondsFormat,
        normalizeFilterKey(value) {
            return String(value || '')
                .toLowerCase()
                .replace(/\s+/g, '')
                .replace(/[^a-zа-яё0-9_]+/gi, '')
        },
        isPeriodFilter(filter) {
            const keys = [
                filter?.name,
                filter?.title,
                filter?.verbose_name,
                filter?.defaultTitle
            ].map(this.normalizeFilterKey)

            return keys.includes('period') || keys.includes('период')
        },
        isUserFilter(filter) {
            const keys = [
                filter?.name,
                filter?.title,
                filter?.verbose_name,
                filter?.defaultTitle
            ].map(this.normalizeFilterKey)

            return keys.includes('user') || keys.includes('пользователь')
        },
        isUserOrganizationFilter(filter) {
            const keys = [
                filter?.name,
                filter?.title,
                filter?.verbose_name,
                filter?.defaultTitle
            ].map(this.normalizeFilterKey)

            return keys.includes('usercurrentcontractor')
                || keys.includes('пользовательорганизацияпоумолчанию')
        },
        mapUserOption(user, valueKey = 'id') {
            const repr = user?.repr
                || user?.string_view
                || user?.full_name
                || user?.fullname
                || user?.name
                || [user?.last_name, user?.first_name].filter(Boolean).join(' ')
                || `ID ${user?.id}`

            return {
                ...user,
                id: user?.id,
                value: user?.id,
                [valueKey]: user?.id,
                repr,
                string_view: repr,
                full_name: user?.full_name || user?.fullname || repr,
                name: user?.name || repr
            }
        },
        mapContractorOption(contractor, valueKey = 'id') {
            const repr = contractor?.repr
                || contractor?.string_view
                || contractor?.name
                || [contractor?.last_name, contractor?.first_name].filter(Boolean).join(' ')
                || `ID ${contractor?.id}`

            return {
                ...contractor,
                id: contractor?.id,
                value: contractor?.id,
                [valueKey]: contractor?.id,
                repr,
                string_view: repr,
                name: contractor?.name || repr,
                full_name: contractor?.full_name || contractor?.fullname || repr
            }
        },
        prepareReportPayload(payload) {
            const nextPayload = JSON.parse(JSON.stringify(payload || {}))
            const filters = nextPayload?.metadata?.filters

            if (!Array.isArray(filters)) {
                return nextPayload
            }

            const start = this.mainDate?.[0] ? this.$moment(this.mainDate[0]).format('YYYY-MM-DD') : null
            const end = this.mainDate?.[1] ? this.$moment(this.mainDate[1]).format('YYYY-MM-DD') : null
            const users = this.reportUsers
                .filter(user => user?.id)
                .map(this.mapUserOption)
            const contractor = this.currentContractor?.id ? this.currentContractor : null

            filters.forEach(filter => {
                if (this.isPeriodFilter(filter) && start && end) {
                    filter.active = true
                    filter.value = [start, end]
                }

                if (this.isUserFilter(filter) && users.length) {
                    const valueKey = filter?.to_field || 'id'
                    const normalizedUsers = users.map(user => this.mapUserOption(user, valueKey))
                    filter.active = true
                    filter.value = normalizedUsers.map(user => user[valueKey])
                    filter.initOptionList = normalizedUsers
                }

                if (this.isUserOrganizationFilter(filter) && contractor) {
                    const valueKey = filter?.to_field || 'id'
                    const normalizedContractor = this.mapContractorOption(contractor, valueKey)
                    filter.active = true
                    filter.value = normalizedContractor[valueKey]
                    filter.initOptionList = [normalizedContractor]
                }
            })

            return nextPayload
        }
    }
}
</script>

<style lang="scss" scoped>
.list_item{
    display: flex;
    flex-direction: column;
    background: #F8F9FD;
    padding: 10px;
    margin-bottom: 10px;
    .list_head{
        width: 100%;
        display: flex;
        align-items: center;
    }
    .info_wrapper{
        flex: 1;
        min-width: 0;
        &__label{
            opacity: 0.9;
            word-break: break-word;
            margin-bottom: 2px;
            font-size: 12px;
            line-height: 12px;
        }
        &__value{
            color: #000;
            word-break: break-word;
            font-size: 16px;
            line-height: 20px;
            font-weight: 600;
        }
    }
    .icon_wrapper{
        width: 36px;
        height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 10px;
        font-size: 18px;
        position: relative;
        overflow: hidden;
        .icon_bg{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            opacity: 0.2;
        }
        i{
            position: relative;
            z-index: 5;
        }
    }
    .report_button{
        margin-left: 8px;
    }
}
</style>
