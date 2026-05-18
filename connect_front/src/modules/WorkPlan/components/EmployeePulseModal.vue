<template>
    <a-modal
        :visible="visible"
        :width="1000"
        :dialog-style="{ top: '20px' }"
        wrapClassName="pulse_employee_modal"
        :destroyOnClose="true"
        @cancel="close">
        <div class="employee_modal">
            <div class="employee_modal__header">
                <div class="employee_modal__user">
                    <Profiler
                        v-if="user"
                        :user="user"
                        :showPopup="false"
                        :avatarSize="isMobile ? 35 : 46"
                        hideSupportTag
                        wrapperClass="w-full"
                        :nameClass="`${!isMobile && 'text-lg'} font-semibold`"
                        :subtitle="subtitle" />
                </div>
                <div v-if="!isMobile" class="employee_modal__period pr-8">
                    <div class="label">{{ $t('table.period') }}</div>
                    <div class="value">{{ periodLabel }}</div>
                </div>
            </div>

            <div class="employee_modal__body">
                <div class="employee_modal__controls">
                    <a-button 
                        type="link" 
                        flaticon
                        class="employee_modal__nav_btn"
                        icon="fi-rr-angle-small-left"
                        shape="circle"
                        @click="goPrev" />
                    <a-date-picker
                        class="employee_modal__date_picker"
                        :value="selectedDateValue"
                        format="DD.MM.YYYY"
                        :allowClear="false"
                        @change="onDateChange" />
                    <a-button 
                        type="link" 
                        flaticon
                        class="employee_modal__nav_btn"
                        icon="fi-rr-angle-small-right"
                        shape="circle"
                        @click="goNext" />
                    <a-button
                        v-if="!isTodaySelected"
                        type="ui_ghost" 
                        flaticon
                        v-tippy
                        :content="$t('workplan.today_short')"
                        icon="fi-rr-calendar-day"
                        class="blue_color employee_modal__today_btn"
                        shape="circle"
                        @click="setToday" />
                </div>
                <div v-if="empty" class="pt-5 pb-5">
                    <a-empty :description="$t('workplan.day_pulse_empty')" />
                </div>
                <div v-else class="notes_list">
                    <NoteCard
                        v-for="item in list.results"
                        :key="item.id"
                        :note="item"
                        :storeKey="noteStoreKey"
                        :readonly="true" />
                </div>

                <infinite-loading
                    :identifier="infiniteId"
                    @infinite="getList"
                    :distance="10">
                    <div slot="spinner" class="flex items-center justify-center inf_spinner">
                        <a-spin />
                    </div>
                    <div slot="no-more"></div>
                    <div slot="no-results"></div>
                </infinite-loading>
            </div>
        </div>

        <template #footer>
            <div class="w-full flex items-center justify-end">
                <a-button type="ui_ghost" :block="isMobile" @click="close">{{ $t('close') }}</a-button>
            </div>
        </template>
    </a-modal>
</template>

<script>
import { dateFormat } from '../utils.js'

export default {
    components: {
        Profiler: () => import('@apps/Profiler/Profiler.vue'),
        NoteCard: () => import('../Drawer/widgets/DayPulse/components/NoteCard.vue'),
        InfiniteLoading: () => import('vue-infinite-loading')
    },
    props: {
        visible: {
            type: Boolean,
            default: false
        },
        record: {
            type: Object,
            default: null
        }
    },
    data() {
        return {
            noteStoreKey: 'main',
            selectedDateValue: null,
            infiniteId: Date.now(),
            loading: false,
            empty: false,
            list: {
                results: [],
                next: true,
                count: 0,
                page: 0
            }
        }
    },
    computed: {
        isMobile() { 
            return this.$store.state.isMobile
        },
        user() {
            return this.record?.author || null
        },
        userId() {
            return this.user?.id || null
        },
        subtitle() {
            const text = [this.user?.job_title].filter(Boolean).join(' • ')
            if (!text) return null
            return { text }
        },
        periodLabel() {
            if (this.selectedDate)
                return this.selectedDate.format('DD MMM YYYY')
            return ''
        },
        selectedDate() {
            if (!this.selectedDateValue) return null
            const date = this.$moment(this.selectedDateValue)
            if (!date.isValid()) return null
            return date
        },
        isTodaySelected() {
            if (!this.selectedDate) return true
            return this.selectedDate.isSame(this.$moment(), 'day')
        }
    },
    watch: {
        visible(value) {
            if (value) {
                this.initSelectedDate()
                this.resetList()
            }
        },
        'record.id'() {
            if (this.visible) {
                this.initSelectedDate()
                this.resetList()
            }
        }
    },
    methods: {
        initSelectedDate() {
            const initial = this.record?.date ? this.$moment(this.record.date) : this.$moment()
            this.selectedDateValue = initial.isValid() ? initial : this.$moment()
        },
        close() {
            this.$emit('close')
        },
        onDateChange(value) {
            if (!value) return
            this.selectedDateValue = value
            this.resetList()
        },
        shiftDate(days) {
            if (!this.selectedDateValue) return
            this.selectedDateValue = this.$moment(this.selectedDateValue).clone().add(days, 'day')
            this.resetList()
        },
        goPrev() {
            this.shiftDate(-1)
        },
        goNext() {
            this.shiftDate(1)
        },
        setToday() {
            this.selectedDateValue = this.$moment()
            this.resetList()
        },
        resetList() {
            this.empty = false
            this.loading = false
            this.list = {
                results: [],
                next: true,
                count: 0,
                page: 0
            }
            this.infiniteId = Date.now()
        },
        async getList($state) {
            if (this.loading || !this.list.next || !this.visible || !this.userId || !this.selectedDate) {
                $state.complete()
                return
            }
            this.loading = true

            try {
                const nextPage = this.list.page + 1
                const start = this.selectedDate.clone().startOf('day')
                const end = this.selectedDate.clone().endOf('day')
                const params = {
                    page: nextPage,
                    page_size: 15,
                    start: dateFormat(start),
                    end: dateFormat(end),
                    user: this.userId
                }
                const { data } = await this.$http.get('/day_summary/note/', { params })
                const results = Array.isArray(data?.results) ? data.results : []
                this.list.page = nextPage
                this.list.count = data?.count || 0
                this.list.next = Boolean(data?.next)
                this.list.results = this.list.results.concat(results)
                this.empty = this.list.page === 1 && !this.list.results.length

                if (this.list.next)
                    $state.loaded()
                else
                    $state.complete()
            } catch (e) {
                $state.complete()
            } finally {
                this.loading = false
            }
        }
    }
}
</script>

<style lang="scss">
.pulse_employee_modal{
    .ant-modal-body{
        padding: 0px;
    }
    .ant-modal-close{
        z-index: 20;
    }
}

@media (max-width: 768px) {
    .pulse_employee_modal{
        .ant-modal{
            width: 100vw !important;
            max-width: 100vw !important;
            margin: 0 !important;
            top: 0 !important;
            padding-bottom: 0 !important;
        }
        .ant-modal-content{
            min-height: 100vh;
            border-radius: 0 !important;
            display: flex;
            flex-direction: column;
        }
        .ant-modal-body{
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .ant-modal-footer{
            border-radius: 0 !important;
        }
    }
}
</style>

<style lang="scss" scoped>
.employee_modal{
    &__header{
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        padding: 10px 20px;
        background: #fff;
        position: sticky;
        top: 0;
        width: 100%;
        z-index: 10;
        border-radius: 16px 16px 0 0;
    }
    &__period{
        text-align: right;
        .label{
            text-transform: uppercase;
            color: #8a94a6;
            font-size: 13px;
        }
        .value{
            font-size: 16px;
            font-weight: 600;
            line-height: 1.15;
        }
    }
    &__body{
        overflow: auto;
        background: #f7f9fc;
        padding: 10px 20px;
    }
    &__controls{
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 12px;
    }
    &__nav_btn{
        border: 0!important;
        box-shadow: none!important;
        background: #fff!important;
        color: #888!important;
    }
    &__date_picker{
        background: #fff;
        border-radius: 10px;
        &::v-deep{
            .ant-input{
                border: 0!important;
                box-shadow: none!important;
                background: #fff;
            }
        }
    }
    &__today_btn{
        border: 0!important;
        box-shadow: none!important;
        background: #fff!important;
    }
}
.notes_list{
    display: flex;
    flex-direction: column;
    gap: 12px;
}

@media (max-width: 768px) {
    .employee_modal{
        height: 100%;
        &__header{
            border-radius: 0;
        }
        &__body{
            flex: 1;
            min-height: 0;
        }
        &__controls{
            justify-content: center;
        }
        &__date_picker{
            max-width: 190px;
            flex: 0 1 auto;
        }
    }
}
</style>
