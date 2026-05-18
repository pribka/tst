<template>
    <a-spin :spinning="sectionLoading" class="w-full" size="small">
        <div
            class="records_wrapper mb-3"
            @mouseenter="onWrapperEnter"
            @mouseleave="onWrapperLeave">
            <a-button
                v-if="showLeftArrow"
                class="scroll_arrow left"
                shape="circle"
                size="small"
                type="flat_primary"
                flaticon
                icon="fi-rr-angle-small-left"
                @mouseenter="startHoverScroll('left')"
                @mouseleave="stopHoverScroll"/>

            <a-button
                v-if="showRightArrow"
                class="scroll_arrow right"
                shape="circle"
                size="small"
                type="flat_primary"
                flaticon
                icon="fi-rr-angle-small-right"
                @mouseenter="startHoverScroll('right')"
                @mouseleave="stopHoverScroll"/>

            <div ref="recordsList" class="records_list" @scroll="onRecordsScroll">
                <div
                    v-for="(record, index) in sections"
                    :key="record.id"
                    :ref="'recordItem_' + record.id"
                    :class="active === record.id && 'active'"
                    class="records_list__item truncate"
                    :title="`${$t('meeting.session_2')} #${sections.length - index} ${record.name || ''}`"
                    @click="setActive(record.id)">
                    <div class="session_label">#{{ sections.length - index }}</div>
                    <div class="session_name truncate">{{ record.name }}</div>
                </div>
            </div>
        </div>

        <a-empty v-if="!sectionLoading && !sections.length" :description="$t('meeting.no_session')" />

        <a-spin :spinning="detailLoading" size="small" class="w-full">
            <template v-if="detail">
                <RecordsItem
                    v-for="record in detail.records"
                    :key="record.id"
                    :meeting="meeting"
                    :detail="detail"
                    :record="record"/>
            </template>
        </a-spin>
    </a-spin>
</template>

<script>
import { errorHandler } from '@/utils/index.js'

export default {
    components: {
        RecordsItem: () => import('./RecordsItem.vue')
    },
    props: {
        meeting: { type: Object, required: true }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        showLeftArrow() {
            return !this.isMobile && this.isWrapperHover && this.canScrollLeft
        },
        showRightArrow() {
            return !this.isMobile && this.isWrapperHover && this.canScrollRight
        }
    },
    data() {
        return {
            active: null,
            sectionLoading: true,
            detail: null,
            detailLoading: false,
            videoLoading: false,
            localRecordFile: null,
            tab: 'summary',
            sections: [],
            isWrapperHover: false,
            canScrollLeft: false,
            canScrollRight: false,
            hoverScrollTimer: null,
            hoverScrollDir: null
        }
    },
    created() {
        this.getSections()
    },
    mounted() {
        window.addEventListener('resize', this.updateArrows)
        this.$nextTick(() => this.updateArrows())
    },
    beforeDestroy() {
        this.stopHoverScroll()
        window.removeEventListener('resize', this.updateArrows)
        this.tab = 'summary'
    },
    watch: {
        sections() {
            this.$nextTick(() => this.updateArrows())
        },
        isMobile() {
            this.$nextTick(() => this.updateArrows())
        }
    },
    methods: {
        onWrapperEnter() {
            this.isWrapperHover = true
            this.$nextTick(() => this.updateArrows())
        },

        onWrapperLeave() {
            this.isWrapperHover = false
            this.stopHoverScroll()
        },

        onRecordsScroll() {
            this.updateArrows()
        },

        getEl() {
            return this.$refs.recordsList
        },

        updateArrows() {
            const el = this.getEl()
            if (!el || this.isMobile) {
                this.canScrollLeft = false
                this.canScrollRight = false
                return
            }

            const max = el.scrollWidth - el.clientWidth
            if (max <= 0) {
                this.canScrollLeft = false
                this.canScrollRight = false
                return
            }

            const left = el.scrollLeft
            const eps = 1

            this.canScrollLeft = left > eps
            this.canScrollRight = left < max - eps
        },

        startHoverScroll(dir) {
            if (this.isMobile) return
            if (!this.isWrapperHover) return

            const el = this.getEl()
            if (!el) return

            this.stopHoverScroll()
            this.hoverScrollDir = dir

            const step = 8
            const tick = 16

            this.hoverScrollTimer = setInterval(() => {
                if (!this.isWrapperHover) {
                    this.stopHoverScroll()
                    return
                }

                const max = el.scrollWidth - el.clientWidth
                if (max <= 0) {
                    this.updateArrows()
                    this.stopHoverScroll()
                    return
                }

                let next = el.scrollLeft
                if (this.hoverScrollDir === 'left') next = next - step
                if (this.hoverScrollDir === 'right') next = next + step

                if (next < 0) next = 0
                if (next > max) next = max

                el.scrollLeft = next
                this.updateArrows()

                if (next === 0 || next === max) this.stopHoverScroll()
            }, tick)
        },

        stopHoverScroll() {
            if (this.hoverScrollTimer) {
                clearInterval(this.hoverScrollTimer)
                this.hoverScrollTimer = null
            }
            this.hoverScrollDir = null
        },

        async getSections() {
            try {
                const { data } = await this.$http.get('/meetings/sections/', {
                    params: { meeting: this.meeting.id, has_records: true, paginate: false }
                })
                if (data) {
                    this.sections = data
                    if (this.sections?.length) {
                        this.active = this.sections[0].id
                        this.getDetail()
                    }
                }
            } catch (error) {
                errorHandler({ error, show: false })
            } finally {
                this.sectionLoading = false
                this.$nextTick(() => this.updateArrows())
            }
        },

        scrollActiveToStart(id) {
            const container = this.getEl()
            const refEl = this.$refs['recordItem_' + id]
            const el = Array.isArray(refEl) ? refEl[0] : refEl
            if (!container || !el) return

            const offset = this.isMobile ? 15 : 30
            const containerRect = container.getBoundingClientRect()
            const elRect = el.getBoundingClientRect()

            const leftDelta = elRect.left - containerRect.left - offset
            const rightDelta = elRect.right - containerRect.right
            if (leftDelta >= 0 && rightDelta <= 0) return

            const targetLeft = container.scrollLeft + leftDelta
            if (typeof container.scrollTo === 'function') {
                container.scrollTo({ left: targetLeft, behavior: 'smooth' })
            } else {
                container.scrollLeft = targetLeft
            }

            this.$nextTick(() => this.updateArrows())
        },

        setActive(id) {
            this.active = id
            this.localRecordFile = null
            this.$nextTick(() => {
                this.scrollActiveToStart(id)
            })
            this.getDetail()
        },

        async getDetail() {
            try {
                this.detailLoading = true
                const { data } = await this.$http.get(`/meetings/sections/${this.active}/`)
                if (data) this.detail = data
            } catch (error) {
                errorHandler({ error, show: false })
            } finally {
                this.detailLoading = false
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.records_wrapper{
    margin-left: -15px;
    margin-right: -15px;
    position: relative;
}

.records_list{
    display: -webkit-box;
    margin-bottom: 0;
    overflow-x: scroll;
    padding-left: 15px;
    padding-right: 15px;
    width: 100%;
    -ms-overflow-style: none;
    scrollbar-width: none;
    -webkit-overflow-scrolling: touch;

    &::-webkit-scrollbar{
        display: none;
    }

    &__item{
        cursor: pointer;
        max-width: 200px;
        border: 1px solid #f0f1f6;
        border-radius: 8px;
        padding: 6px 10px;
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
        display: flex;
        background: #f0f1f6;
        align-items: center;

        &:not(:last-child){
            margin-right: 10px;
        }

        &.active{
            border-color: var(--blue);
            background: var(--blue);
            color: #fff;
        }

        &:hover{
            border-color: var(--blue);
        }

        .session_label{
            opacity: 0.8;
            margin-right: 5px;
        }

        .session_name{
            font-weight: 600;
        }
    }
}

.scroll_arrow{
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    z-index: 10;

    &.left{
        left: -10px;
    }

    &.right{
        right: -10px;
    }
}
</style>