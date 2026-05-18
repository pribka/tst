<template>
    <a-modal
        :title="$t('calendar.attach_meeting')"
        destroyOnClose
        :width="isMobile ? '100%' : '560px'"
        :visible="visible"
        :maskClosable="true"
        :wrapClassName="modalWrapClass"
        @cancel="close">
        <div class="drawer_content">
            <div v-if="!isMobile" ref="header" class="drawer_content__header">
                <PageFilter
                    :model="pageModel"
                    :key="pageName"
                    size="large"
                    :zIndex="999999"
                    ref="pageFilter"
                    initInputFocus
                    autoAdjustOverflow
                    class="modal_filter"
                    transitionName=""
                    placement="bottom"
                    :popoverMaxWidth="600"
                    :getPopupContainer="() => $refs.header"
                    :page_name="pageName" />
            </div>

            <div class="drawer_content__list">
                <AttachMeetingCard
                    v-for="item in displayedMeetings"
                    :key="item.id"
                    :item="item"
                    :selected="selectedMeetingId === item.id"
                    @select="selectMeeting" />

                <div v-if="page === 1 && loading" class="flex justify-center py-2">
                    <a-spin size="small" />
                </div>

                <div v-if="!loading && !displayedMeetings.length" class="empty_text">
                    {{ $t('calendar.no_data') }}
                </div>

                <infinite-loading
                    ref="meetingInfinite"
                    :identifier="infiniteId"
                    @infinite="getMeetingList"
                    v-bind:distance="10">
                    <div slot="spinner"><a-spin v-if="page !== 1" size="small" /></div>
                    <div slot="no-more"></div>
                    <div slot="no-results"></div>
                </infinite-loading>
            </div>

            <div v-if="isMobile" class="float_add mobile">
                <div class="filter_slot">
                    <PageFilter
                        :model="pageModel"
                        :key="pageName"
                        :zIndex="999999"
                        ref="pageFilterMobile"
                        initInputFocus
                        autoAdjustOverflow
                        size="large"
                        :popoverMaxWidth="600"
                        :page_name="pageName" />
                </div>
            </div>
        </div>

        <template #footer>
            <div class="flex items-center gap-2 w-full">
                <a-button
                    type="primary"
                    size="large"
                    block
                    :loading="attachLoading"
                    :disabled="!selectedMeetingId"
                    @click="attach">
                    {{ $t('calendar.attach_and_close') }}
                </a-button>
                <a-button
                    type="ui_ghost"
                    size="large"
                    block
                    :disabled="attachLoading"
                    @click="close">
                    {{ $t('calendar.close') }}
                </a-button>
            </div>
        </template>
    </a-modal>
</template>

<script>
import { mapState } from 'vuex'
import { errorHandler } from '@/utils/index.js'
import eventBusGlobal from '@/utils/eventBus'

export default {
    components: {
        PageFilter: () => import('@/components/PageFilter/index.vue'),
        InfiniteLoading: () => import('vue-infinite-loading'),
        AttachMeetingCard: () => import('./AttachMeetingCard.vue')
    },
    props: {
        eventId: {
            type: String,
            required: true
        },
        currentMeetingId: {
            type: String,
            default: ''
        }
    },
    data() {
        return {
            visible: false,
            selectedMeeting: null,
            selectedMeetingId: '',
            attachLoading: false,
            currentMeeting: null,
            page: 0,
            loading: false,
            scrollStatus: true,
            infiniteId: Date.now(),
            meetingList: []
        }
    },
    computed: {
        ...mapState({
            isMobile: state => state.isMobile
        }),
        modalWrapClass() {
            return `attach_meeting_modal_${this._uid}`
        },
        pageModel() {
            return 'meetings.PlannedMeetingModel'
        },
        pageName() {
            return 'page_calendar_attach_meetings.PlannedMeetingModel'
        },
        displayedMeetings() {
            const uniq = new Map()

            ;[
                ...(this.currentMeeting?.id ? [this.currentMeeting] : []),
                ...this.meetingList
            ].forEach(item => {
                if (item?.id && !uniq.has(item.id)) {
                    uniq.set(item.id, item)
                }
            })

            return Array.from(uniq.values())
        }
    },
    methods: {
        async open() {
            this.selectedMeetingId = this.currentMeetingId || ''
            this.selectedMeeting = this.currentMeeting?.id === this.currentMeetingId
                ? this.currentMeeting
                : null
            this.reloadList()
            this.visible = true
            await this.loadCurrentMeeting()
            this.$nextTick(() => {
                if (this.isMobile) {
                    this.$refs.pageFilterMobile?.searchFocus?.()
                } else {
                    this.$refs.pageFilter?.searchFocus?.()
                }
            })
        },
        close() {
            this.visible = false
        },
        reloadList() {
            this.page = 0
            this.loading = false
            this.scrollStatus = true
            this.meetingList = []
            this.infiniteId += 1
        },
        async loadCurrentMeeting() {
            if (!this.currentMeetingId) {
                this.currentMeeting = null
                return
            }

            try {
                const { data } = await this.$http.get(`/meetings/${this.currentMeetingId}/detail/`)
                this.currentMeeting = data || null

                if (!this.selectedMeeting && this.currentMeeting?.id === this.currentMeetingId) {
                    this.selectedMeeting = this.currentMeeting
                }
            } catch (error) {
                errorHandler({ error, show: false })
            }
        },
        selectMeeting(item) {
            this.selectedMeeting = item
            this.selectedMeetingId = item?.id || ''
        },
        async getMeetingList($state = null) {
            if (!this.loading && this.scrollStatus && this.visible) {
                try {
                    this.loading = true
                    this.page += 1
                    const { data } = await this.$http.get('/meetings/', {
                        params: {
                            page: this.page,
                            page_size: 15,
                            page_name: this.pageName,
                            model: this.pageModel
                        }
                    })

                    if (data?.results?.length) {
                        const existingIds = new Set(this.meetingList.map(item => item.id))
                        const newMeetings = data.results.filter(item => !existingIds.has(item.id))
                        this.meetingList = this.meetingList.concat(newMeetings)
                    }

                    if (!data?.next) {
                        this.scrollStatus = false
                        $state?.complete?.()
                    } else {
                        $state?.loaded?.()
                    }
                } catch (error) {
                    errorHandler({ error, show: false })
                    $state?.complete?.()
                } finally {
                    this.loading = false
                }
            } else {
                $state?.complete?.()
            }
        },
        async attach() {
            if (!this.selectedMeetingId) return

            try {
                this.attachLoading = true
                await this.$http.patch(`/calendars/events/${this.eventId}/`, {
                    meeting: this.selectedMeetingId
                })
                this.$message.success(this.$t('calendar.attach_meeting_success'))
                this.$emit('attached')
                this.close()
            } catch (error) {
                errorHandler({ error })
            } finally {
                this.attachLoading = false
            }
        }
    },
    mounted() {
        eventBusGlobal.$on(`update_filter_${this.pageModel}`, this.reloadList)
    },
    beforeDestroy() {
        eventBusGlobal.$off(`update_filter_${this.pageModel}`, this.reloadList)
    }
}
</script>

<style lang="scss" scoped>
.drawer_content {
    width: 100%;
    min-height: 320px;
    display: flex;
    flex-direction: column;
}

.drawer_content__header{
    margin-bottom: 12px;
}

.drawer_content__list{
    min-height: 320px;
    max-height: calc(100vh - 220px);
    overflow: auto;
}

.empty_text {
    text-align: center;
    color: #888888;
    padding: 20px 0;
}

.modal_filter{
    &::v-deep{
        .filter_input{
            border-radius: 8px;
            background: #f7f9fc;
            border-color: #f7f9fc !important;
            box-shadow: initial !important;
            color: var(--text);
            .ant-input{
                background: #f7f9fc;
            }
        }
    }
}

::v-deep .ant-modal{
    top: 20px;
}

::v-deep .ant-modal-content{
    overflow: hidden;
}

::v-deep .ant-modal-footer{
    z-index: 2;
}

@media (max-width: 768px) {
    .float_add.mobile{
        bottom: calc(88px + env(safe-area-inset-bottom));
    }

    .drawer_content{
        min-height: 0;
    }

    ::v-deep .ant-modal{
        top: 0 !important;
        max-width: 100vw;
        width: 100vw !important;
        margin: 0;
        padding-bottom: 0;
    }

    ::v-deep .ant-modal-content{
        height: 100vh;
        border-radius: 0;
    }

    ::v-deep .ant-modal-body{
        padding-bottom: 0;
    }

    .drawer_content__list{
        max-height: calc(100vh - 140px - env(safe-area-inset-bottom));
        padding-bottom: 88px;
    }

    ::v-deep .ant-modal-header{
        border-radius: 0;
    }

    ::v-deep .ant-modal-footer{
        border-radius: 0;
        padding-bottom: calc(12px + env(safe-area-inset-bottom));
    }
}
</style>
