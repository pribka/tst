<template>
    <DrawerTemplate
        v-model="visible"
        :width="windowWidth > 1350 ? 1350 : '100%'"
        @afterVisibleChange="afterVisibleChange"
        destroyOnClose
        class="my_plan_drawer intents_detail_drawer"
        :titleTruncate="false"
        @close="visible = false">
        <template #title>
            <div class="ai_drawer_title title flex items-center">
                <img src="@/assets/svg/ai_icons.svg" class="mr-2" />
                {{ $t('workplan.ai_recommendations') }}
            </div>
        </template>
        <div ref="bodyRef">
            <DetailSummary :storeKey="storeKey" />

            <a-empty v-if="empty" :description="$t('workplan.intents_none')" />
            <CardLoading v-if="loading" />
            <IntentCard 
                v-for="(item, index) in list" 
                :key="item.id" 
                :createdHandler="createdHandler"
                :toggleCollapse="toggleCollapse"
                :index="index"
                :intentEditField="intentEditField"
                :intentChangeField="intentChangeField"
                :intentDelete="intentDelete"
                :item="item" />
            <transition name="slide-up-fade">
                <div 
                    v-if="backTopTopVisible"
                    class="back_top">
                    <a-button
                        shape="circle"
                        flaticon
                        size="large"
                        icon="fi-rr-angle-small-up"
                        @click="parentTopScroll()" />
                </div>
            </transition>
            <div class="drawer_dummy" />
        </div>
    </DrawerTemplate>
</template>

<script>
import { mapState } from 'vuex'
import { errorHandler } from '@/utils/index.js'
import eventBus from "@/utils/eventBus"
import { dateFormat } from '../../utils.js'
export default {
    props: {
        storeKey: {
            type: String,
            required: true
        },
        intentsStatReload: {
            type: Function,
            default: () => {}
        },
        reloadOnKeyData: {
            type: Function,
            default: () => {}
        }
    },
    components: {
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue'),
        IntentCard: () => import('./IntentCard.vue'),
        CardLoading: () => import('./CardLoading.vue'),
        DetailSummary: () => import('./DetailSummary.vue')
    },
    computed: {
        ...mapState({ 
            windowWidth: state => state.windowWidth,
            isMobile: state => state.isMobile
        }),
        mainDate: {
            get() {
                return this.$store.state.workplan.mainDate?.[this.storeKey] || []
            },
            set(value) {
                this.$store.commit('workplan/CHANGE_FIELD', {
                    value,
                    field: 'mainDate',
                    storeKey: this.storeKey
                })
            }
        },
        project() {
            return this.$store.state.workplan.project?.[this.storeKey] || null
        },
        workgroup() {
            return this.$store.state.workplan.workgroup?.[this.storeKey] || null
        },
        user() {
            return this.$store.state.workplan.user?.[this.storeKey] || null
        },
    },
    data() {
        return {
            scrollListener: null,
            scrollParent: null,
            backTopTopVisible: false,
            visible: false,
            loading: false,
            list: [],
            empty: false,
            selectSession: null,
            update: {
                task: false,
                event: false,
                meeting: false
            }
        }
    },
    methods: {
        attachScrollListener() {
            const sp = this.getScrollParent(this.$el) || window
            this.scrollParent = sp
            if (!sp) return

            this.scrollListener = () => {
                this.handleScroll()
            }

            try {
                sp.addEventListener('scroll', this.scrollListener, { passive: true })
            } catch (e) {
                sp.addEventListener('scroll', this.scrollListener)
            }

            this.handleScroll()
        },
        detachScrollListener() {
            if (!this.scrollParent || !this.scrollListener) return

            try {
                this.scrollParent.removeEventListener('scroll', this.scrollListener, { passive: true })
            } catch (e) {
                this.scrollParent.removeEventListener('scroll', this.scrollListener)
            }

            this.scrollListener = null
        },
        handleScroll() {
            const sp = this.scrollParent || this.getScrollParent(this.$el) || window

            if (sp === window) {
                const rect = this.$el.getBoundingClientRect()
                const scrolled = window.pageYOffset || document.documentElement.scrollTop || 0
                const topOffset = scrolled + rect.top
                this.backTopTopVisible = scrolled - topOffset > 100
            } else {
                this.backTopTopVisible = (sp.scrollTop || 0) > 100
            }
        },
        getScrollParent(startElm = this.$el) {
            const el = startElm && (startElm.$el ? startElm.$el : startElm)
            if (!el) return window
            let wrap = null
            if (typeof el.closest === 'function') {
                wrap = el.closest('.drawer_wrap, .ant-drawer-wrapper, .ant-drawer') || document.querySelector('.drawer_wrap') || document.querySelector('.ant-drawer-wrapper')
            }
            if (wrap) {
                const inner = wrap.querySelector('.drawer_body') || wrap.querySelector('.ant-drawer-body .drawer_body') || wrap.querySelector('.ant-drawer-body')
                if (inner) return inner
            }
            let elm = el
            while (elm) {
                if (elm === window || elm === document) return window
                if (elm.nodeType === 1) {
                    const cls = (elm.className || '')
                    if (cls.indexOf('drawer_body') > -1 || cls.indexOf('ant-drawer-body') > -1) return elm
                    try {
                        const style = getComputedStyle(elm)
                        if (['scroll', 'auto'].indexOf(style.overflowY) > -1) return elm
                    } catch (e) {}
                    if (elm.tagName === 'BODY') return window
                }
                elm = elm.parentNode
            }
            return window
        },
        parentTopScroll() {
            const bodyRef = this.$refs.bodyRef
            const targetEl = bodyRef && bodyRef.$el ? bodyRef.$el : bodyRef || this.$el
            const candidate = this.scrollParent || this.getScrollParent(targetEl)
            let scrollEl = candidate
            if (candidate && candidate.nodeType === 1) {
                const inner = candidate.querySelector && (candidate.querySelector('.drawer_body') || candidate.querySelector('.ant-drawer-body .drawer_body'))
                if (inner) scrollEl = inner
            }
            if (!scrollEl) return
            if (scrollEl === window) {
                window.scrollTo({ top: 0, behavior: 'smooth' })
                return
            }
            if (typeof scrollEl.scrollTo === 'function') {
                scrollEl.scrollTo({ top: 0, behavior: 'smooth' })
                return
            }
            scrollEl.scrollTop = 0
        },
        intentEditField({ widgetKey, index, listIndex, intentIndex, messageIndex, value, useRepr }) {
            const targetListIndex = typeof listIndex === 'number' ? listIndex : index
            if(this.list[targetListIndex]?.intents?.[intentIndex]?.resolutions?.[widgetKey])
                this.$set(this.list[targetListIndex].intents[intentIndex].resolutions[widgetKey], 'value', value)
        },
        intentChangeField({ intentId, value, field, listIndex }) {
            const index = this.list[listIndex].intents.findIndex(f => f.id === intentId)
            if(index !== -1)
                this.$set(this.list[listIndex].intents[index], field, value)
            this.intentsStatReload()
        },
        intentDelete({ intentId, listIndex }) {
            const index = this.list[listIndex].intents.findIndex(f => f.id === intentId)
            if(index !== -1)
                this.$set(this.list[listIndex].intents[index], 'is_active', false)
            this.intentsStatReload()
        },
        createdHandler({ data, code }) {
            if(typeof this.update[code] === 'boolean')
                this.update[code] = true
        },
        toggleCollapse(index) {
            this.$set(this.list[index], 'collapse', !this.list[index].collapse)
        },
        drawerOpen() {
            this.visible = true
        },
        clearData() {
            this.empty = false
            this.list = []
            this.selectSession = null
            this.update = {
                task: false,
                event: false,
                meeting: false
            }
        },
        afterVisibleChange(vis) {
            if(vis) {
                this.getData()
                this.$nextTick(() => {
                    this.attachScrollListener()
                })
            } else {
                this.reloadOnKeyData(this.update)
                this.clearData()
                this.detachScrollListener()
            }
        },
        async getData() {
            try {
                this.loading = true

                const params = {
                    start: dateFormat(this.mainDate[0]),
                    end: dateFormat(this.mainDate[1])
                }
                if(this.project)
                    params.project = this.project
                if(this.workgroup)
                    params.workgroup = this.workgroup
                if(this.user?.length)
                    params.user = this.user.map(user => user.id).join(',')
                const { data } = await this.$http.get('/meetings/sections/my_day_intents/', { params })
                if (data?.length) {
                    let list = data
                    if (this.selectSession) {
                        const index = list.findIndex(i => i.id === this.selectSession)
                        if (index > -1) {
                            const [selected] = list.splice(index, 1)
                            list.unshift(selected)
                        }
                    }
                    this.list = list.map((item, index) => ({
                        ...item,
                        collapse: index === 0 ? true : false
                    }))
                } else {
                    this.empty = true
                }
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                this.loading = false
            }
        }
    },
    mounted() {
        eventBus.$on('open_ai_intents', session_id => {
            this.selectSession = session_id
            this.visible = true
        })
    },
    beforeDestroy() {
        eventBus.$off('open_ai_intents')
        this.detachScrollListener()
    }
}
</script>

<style lang="scss" scoped>
.ai_drawer_title{
    img{
        max-width: 26px;
    }
}
.drawer_dummy{
    min-height: 30px;
}
.back_top{
    position: sticky;
    bottom: 40px;
    height: 0px;
    z-index: 100;
    display: flex;
    justify-content: flex-end;
    &::v-deep{
        .ant-btn{
            --alpha: 1;
            backdrop-filter: blur(calc(7px * (2 - var(--alpha))));
            background: rgba(255, 255, 255, 0.8);
            box-shadow: 0 0 0 1px #e6e6e8;
            border: initial!important;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
        }
    }
}
.slide-up-fade-enter-active {
  transition: all .2s ease;
}
.slide-up-fade-leave-active {
  transition: all .1s cubic-bezier(1.0, 0.5, 0.8, 1.0);
}
.slide-up-fade-enter, .slide-up-fade-leave-to {
  transform: translateY(10px);
  opacity: 0;
}
</style>

<style lang="scss">
.intents_detail_drawer{
    &.drawer_wrap.ant-drawer .ant-drawer-body .drawer_body.padding{
        padding-top: 5px;
    }
}
</style>
