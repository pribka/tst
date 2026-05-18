<template>
    <div class="meeting_select_field">
        <div
            class="ant-input ant-input-lg meeting_select_field__input"
            :title="inputTitle"
            @click="openModal">
            <span
                v-if="modelValue"
                class="meeting_select_field__value truncate">
                {{ inputTitle }}
            </span>
            <span v-else class="meeting_select_field__placeholder truncate">
                {{ placeholder }}
            </span>
            <i
                v-if="modelValue"
                class="fi fi-rr-cross-small meeting_select_field__clear"
                @click.stop="clearSelection" />
            <i
                v-else
                class="fi fi-rr-share-square meeting_select_field__icon" />
        </div>

        <div v-if="modelValue" class="meeting_select_field__card">
            <AddEventMeetingCard
                :item="modelValue"
                @open="openMeeting" />
        </div>

        <a-modal
            :title="$t('calendar.select_meeting')"
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
                        :disabled="!selectedMeetingId"
                        @click="applySelection">
                        {{ $t('select') }}
                    </a-button>
                    <a-button
                        type="ui_ghost"
                        size="large"
                        block
                        @click="close">
                        {{ $t('calendar.close') }}
                    </a-button>
                </div>
            </template>
        </a-modal>
    </div>
</template>

<script>
import { mapState } from 'vuex'
import eventBusGlobal from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'

export default {
    name: 'MeetingSelectField',
    components: {
        PageFilter: () => import('@/components/PageFilter/index.vue'),
        InfiniteLoading: () => import('vue-infinite-loading'),
        AttachMeetingCard: () => import('./EventDrawer/AttachMeetingCard.vue'),
        AddEventMeetingCard: () => import('./AddEventMeetingCard.vue')
    },
    props: {
        value: {
            type: Object,
            default: null
        },
        placeholder: {
            type: String,
            default: ''
        }
    },
    data() {
        return {
            visible: false,
            selectedMeeting: null,
            selectedMeetingId: '',
            page: 0,
            loading: false,
            scrollStatus: true,
            infiniteId: Date.now(),
            meetingList: [],
            currentMeeting: null
        }
    },
    computed: {
        ...mapState({
            isMobile: state => state.isMobile
        }),
        modelValue() {
            return this.value
        },
        inputTitle() {
            return this.modelValue?.string_view || this.modelValue?.name || ''
        },
        modalWrapClass() {
            return `meeting_select_field_modal_${this._uid}`
        },
        pageModel() {
            return 'meetings.PlannedMeetingModel'
        },
        pageName() {
            return 'page_calendar_form_meetings.PlannedMeetingModel'
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
        async openModal() {
            this.selectedMeetingId = this.modelValue?.id || ''
            this.selectedMeeting = this.modelValue ? { ...this.modelValue } : null
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
        openMeeting() {
            if (!this.modelValue?.id) return

            const query = JSON.parse(JSON.stringify(this.$route.query || {}))
            if (query.meeting !== this.modelValue.id) {
                query.meeting = this.modelValue.id
                this.$router.push({ query })
            }
        },
        clearSelection() {
            this.$emit('input', null)
            this.$emit('change', null)
        },
        reloadList() {
            this.page = 0
            this.loading = false
            this.scrollStatus = true
            this.meetingList = []
            this.infiniteId += 1
        },
        async loadCurrentMeeting() {
            if (!this.modelValue?.id) {
                this.currentMeeting = null
                return
            }

            try {
                const { data } = await this.$http.get(`/meetings/${this.modelValue.id}/detail/`)
                this.currentMeeting = data || null
                this.selectedMeeting = this.currentMeeting || this.selectedMeeting
            } catch (error) {
                errorHandler({ error, show: false })
            }
        },
        selectMeeting(item) {
            this.selectedMeeting = item
            this.selectedMeetingId = item?.id || ''
        },
        applySelection() {
            const meeting = this.selectedMeeting || this.currentMeeting || null
            this.$emit('input', meeting)
            this.$emit('change', meeting)
            this.close()
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
.meeting_select_field{
    &__input{
        min-height: 40px;
        height: auto;
        display: flex;
        align-items: center;
        gap: 6px;
        cursor: pointer;
    }

    &__value{
        flex: 1;
    }

    &__placeholder{
        flex: 1;
        color: #bfbfbf;
    }

    &__icon{
        color: #bfbfbf;
        font-size: 14px;
        flex-shrink: 0;
    }

    &__clear{
        color: #bfbfbf;
        font-size: 16px;
        flex-shrink: 0;
        transition: color 0.2s;

        &:hover{
            color: #ff4d4f;
        }
    }

    &__card{
        margin-top: 10px;
    }
}

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
        max-height: calc(100vh - 190px);
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
