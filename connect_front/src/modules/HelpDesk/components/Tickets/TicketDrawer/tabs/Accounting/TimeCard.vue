<template>
    <div class="time_card">
        <div
            v-for="col in mobileTableInfo"
            :key="col.field"
            :class="col.class ? col.class : ''"
            class="item_field">
            <template v-if="col.field === 'work_type'">
                <template v-if="item.work_type">
                    <div class="item_field">
                        <span class="item_head">
                            {{ col.headerName }}:
                        </span>
                        <span>
                            {{ item.work_type.name }}
                        </span>
                    </div>
                </template>
            </template>
            <template v-if="col.field === 'description'">
                <div class="item_field">
                    <div v-if="item.description">
                        <span class="item_head">
                            {{ col.headerName }}:
                        </span>
                        <div class="mt-1">
                            <TextViewer
                                collapsible
                                overlayColor="#fff"
                                :body="item.description" />
                        </div>
                    </div>
                </div>
            </template>
            <template v-if="col.field === 'is_result' && item.is_result">
                <div class="item_field flex items-center gap-2">
                    <span class="item_head">
                        {{ col.headerName }}:
                    </span>
                    <i class="fi fi-rr-check text-green-500" />
                </div>
            </template>
            <template v-if="col.field === 'author'">
                <div class="item_field flex items-center">
                    <span class="item_head mr-2">
                        {{ col.headerName }}:
                    </span>
                    <span>
                        <Profiler
                            :user="item.user"
                            :avatarSize="18"
                            :getPopupContainer="trigger => trigger.parentNode"
                            hideSupportTag />
                    </span>
                </div>
            </template>
            <div v-if="col.field === 'duration'" class="item_field">
                <span class="item_head">
                    {{ col.headerName }}:
                </span>
                <span>
                    {{ formattedDuration }}
                </span>
            </div>
            <template v-if="col.field === 'date'">
                <div v-if="item.date" class="item_field">
                    <span class="item_head">
                        {{ col.headerName }}:
                    </span>
                    <span>
                        {{ $moment(item.date).format('DD.MM.YYYY') }}
                    </span>
                </div>
            </template>
        </div>
        <TicketsAccountingActionsRow
            v-if="colParams?.id"
            :record="item"
            :colParams="colParams"/>
    </div>
</template>

<script>
export default {
    components: {
        TicketsAccountingActionsRow: () => import('@/components/TableWidgets/Widgets/TicketsAccountingActionsRow.vue'),
        TextViewer: () => import('@apps/CKEditor/TextViewer.vue')
    },
    props: {
        ticket: {type: Object, required: true},
        item: {type: Object, required: true},
        pageModel: {type: String, required: true},
        pageName: {type: String, required: true},
        colParams: {type: Object, default: () => null}
    },
    methods: {
        formatDate(date) {
            if (!date) return ''
            return this.$moment(date).format('DD.MM.YYYY')
        },

    },
    computed:{
        isMobile() {
            return this.$store.state.isMobile
        },
        workTimeSettings() {
            return this.$store.state.tickets.workTimeSettings
        },
        pageConfig() {
            if(this.workTimeSettings)
                return this.workTimeSettings
            else
                return null
        },
        mobileTableInfo() {
            const tableInfo = this.pageConfig?.tableInfo || []
            if (!this.isMobile) return tableInfo

            const isResultCol = tableInfo.find(col => col.field === 'is_result')
            const withoutIsResult = tableInfo.filter(col => col.field !== 'is_result')
            const dateIndex = withoutIsResult.findIndex(col => col.field === 'date')

            if (!isResultCol || dateIndex === -1) return withoutIsResult

            const result = [...withoutIsResult]
            result.splice(dateIndex + 1, 0, isResultCol)
            return result
        },
        formattedDuration() {
            const sec = Number(this.item.duration)
            if (!sec || !Number.isFinite(sec)) return '0 секунд'

            const hours = Math.floor(sec / 3600)
            const minutes = Math.floor((sec % 3600) / 60)
            const seconds = sec % 60

            const plural = (num, one, few, many) => {
                const n = Math.abs(num) % 100
                const n1 = n % 10
                if (n > 10 && n < 20) return many
                if (n1 > 1 && n1 < 5) return few
                if (n1 === 1) return one
                return many
            }

            let res = ''

            if (hours > 0)
                res += `${hours} ${plural(hours, this.$t('helpdesk.hour1'), this.$t('helpdesk.hour2'), this.$t('helpdesk.hour3'))}`

            if (minutes > 0) {
                if (res) res += ' '
                res += `${minutes} ${plural(minutes, this.$t('helpdesk.minute1'), this.$t('helpdesk.minute2'), this.$t('helpdesk.minute3'))}`
            }

            if (!res)
                res = `${seconds} ${plural(seconds, this.$t('helpdesk.second1'), this.$t('helpdesk.second2'), this.$t('helpdesk.second3'))}`

            return res
        }
    }
}
</script>

<style lang="scss">
.time_card {
    &:not(:last-child) {
        margin-bottom: 10px;
        padding-bottom: 10px;
        border-bottom: 1px solid var(--borderColor);
    }
    .item_field {
        margin-bottom: 8px;
    }
    .item_head {
        margin-bottom: 0.3em;
    }
}
</style>
