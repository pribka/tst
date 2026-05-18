<template>
    <div ref="timeline">
        <PageFilter 
            model="change_history.ChangeHistoryModel"
            :key="page_name"
            size="large"
            class="mb-3"
            :placement="filterPlacement"
            :filterPrefix="filterPrefix"
            :modelLabel="modelLabel"
            :popoverMaxWidth="600"
            :getPopupContainer="getPopupContainer"
            :page_name="page_name" />
        <div v-if="empty" class="mt-4">
            <a-empty :description="$t('history.noData')" />
        </div>
        <div 
            v-for="(group, index) in sortedList" 
            :key="index" 
            class="timeline"
            :class="index + 1 === sortedList.length && 'last'">
            <GroupLabel :group="group" />
            <transition-group name="timeline_list" tag="div">
                <div 
                    v-for="(item, index) in group.data" 
                    :key="item.id" 
                    class="timeline__item">
                    <div class="timeline_tail" :class="index + 1 === group.data.length && 'last'" />
                    <div class="timeline_crc">
                        <template v-if="item.author">
                            <Profiler 
                                :user="item.author"
                                showAvatar
                                :avatarSize="20"
                                :getPopupContainer="getPopupContainer"
                                :showUserName="false" />
                        </template>
                        <template v-else>
                            <a-avatar :size="20" icon="setting" />
                        </template>
                    </div>
                    <div class="timeline_content">
                        <template v-if="item.author">
                            <Profiler 
                                :user="item.author" 
                                class="ml-1"
                                :showAvatar="false"
                                :getPopupContainer="getPopupContainer" />
                        </template>
                        <template v-else>
                            {{ $t('history.connect') }}
                        </template>
                        <div class="flex mt-2">
                            <div>
                                <div class="timeline_wrapper">
                                    <div v-if="item.action" class="timeline_wrapper__item">
                                        <span class="item_label">{{ $t('history.action') }}:</span><span class="item_value">{{ item.action.name }}</span>
                                    </div>
                                    <div v-if="item.object_property" class="timeline_wrapper__item">
                                        <span class="item_label">{{ $t('history.property') }}:</span><span class="item_value">{{ item.object_property.name }}</span>
                                    </div>
                                    <div v-if="item.description" class="timeline_wrapper__item">
                                        <span class="item_label">{{ $t('history.description') }}:</span><div class="item_value" v-html="item.description" />
                                    </div>
                                    <div v-if="item.before" class="timeline_wrapper__item">
                                        <div class="item_label">{{ $t('history.was') }}:</div>
                                        <div v-if="isDate(item.before)" class="item_value">{{ $moment(item.before).format('DD.MM.YYYY HH:mm') }}</div>
                                        <div v-else class="item_value" v-html="item.before" />
                                    </div>
                                    <div v-if="item.after" class="timeline_wrapper__item">
                                        <div class="item_label">{{ $t('history.became') }}:</div>
                                        <div v-if="isDate(item.after)" class="item_value">{{ $moment(item.after).format('DD.MM.YYYY HH:mm') }}</div>
                                        <div v-else class="item_value" v-html="item.after" />
                                    </div>
                                </div>
                                <div class="flex items-center mt-2 pl-3 pr-3">
                                    <div class="text-xs cursor-pointer blue_color" @click="openDetail(item.id)">
                                        {{ $t('history.moreDetails') }}
                                    </div>
                                    <div class="text-xs gray ml-5">
                                        {{ $moment(item.action_date).format('HH:mm') }}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </transition-group>
        </div>
        <infinite-loading 
            ref="histofy_infinity"
            @infinite="getHistory"
            v-bind:distance="10">
            <div 
                slot="spinner"
                class="flex items-center justify-center mt-3">
                <a-spin />
            </div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
        <a-modal 
            v-model="visible" 
            title=""
            :width="modalWidth"
            :dialog-style="{ top: isMobile ? '0px' : '20px' }"
            class="comment_modal"
            ref="commentModal"
            :afterClose="afterClose">
            <div v-if="modalLoading" class="flex justify-center">
                <a-spin />
            </div>
            <template v-else>
                <div v-if="detail" class="detail_wrapper">
                    <div class="detail_wrapper__item">
                        <span class="item_label">{{ $t('history.date') }}:</span><span class="item_value">{{ $moment(detail.action_date).format('DD.MM.YYYY HH:mm') }}</span>
                    </div>
                    <div v-if="detail.action" class="detail_wrapper__item">
                        <span class="item_label">{{ $t('history.action') }}:</span><span class="item_value">{{ detail.action.name }}</span>
                    </div>
                    <div v-if="detail.object_property" class="detail_wrapper__item">
                        <span class="item_label">{{ $t('history.property') }}:</span><span class="item_value">{{ detail.object_property.name }}</span>
                    </div>
                    <div v-if="detail.description" class="detail_wrapper__item">
                        <span class="item_label">{{ $t('history.description') }}:</span><div class="item_value" v-html="detail.description" />
                    </div>
                    <div v-if="detail.before" class="detail_wrapper__item">
                        <div class="item_label">{{ $t('history.was') }}:</div>
                        <div v-if="isDate(detail.before)" class="item_value">{{ $moment(detail.before).format('DD.MM.YYYY HH:mm') }}</div>
                        <template v-else>
                            <template v-if="checkTextLength(detail.before_clean)">
                                <div class="text_wrapper" :class="open1 && 'show'">
                                    <TextViewer 
                                        :body="detail.before"/>
                                </div>
                                <div class="text-xs cursor-pointer blue_color mt-2" @click="open1 = !open1">
                                    {{ open1 ? $t('history.collapse') : $t('history.expand') }}
                                </div>
                            </template>
                            <TextViewer 
                                v-else
                                :body="detail.before"/>
                        </template>
                    </div>
                    <div v-if="detail.after" class="detail_wrapper__item">
                        <div class="item_label">{{ $t('history.became') }}:</div>
                        <div v-if="isDate(detail.after)" class="item_value">{{ $moment(detail.after).format('DD.MM.YYYY HH:mm') }}</div>
                        <template v-else>
                            <template v-if="checkTextLength(detail.after_clean)">
                                <div class="text_wrapper" :class="open2 && 'show'">
                                    <TextViewer 
                                        :body="detail.after"/>
                                </div>
                                <div class="text-xs cursor-pointer blue_color mt-2" @click="open2 = !open2">
                                    {{ open2 ? $t('history.collapse') : $t('history.expand') }}
                                </div>
                            </template>
                            <TextViewer 
                                v-else
                                :body="detail.after"/>
                        </template>
                    </div>
                </div>
            </template>
            <template #footer>
                <a-button type="ui" ghost @click="visible = false">
                    {{ $t('history.close') }}
                </a-button>
            </template>
        </a-modal>
    </div>
</template>

<script>
const ISO_8601_FULL = /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d+)?(([+-]\d\d:\d\d)|Z)?$/i
import eventBus from '@/utils/eventBus'
import { socketEmitJoin, socketEmitLeave } from '@/utils/socketUtils.js'
import { errorHandler } from '@/utils/index.js'
export default {
    components: {
        GroupLabel: () => import('./GroupLabel.vue'),
        InfiniteLoading: () => import('vue-infinite-loading'),
        TextViewer: () => import('@apps/CKEditor/TextViewer.vue'),
        PageFilter: () => import('@/components/PageFilter')
    },
    props: {
        page_size: {
            type: Number,
            default: 15
        },
        related_object: {
            type: [String, Number],
            required: true
        },
        injectContainer: {
            type: Boolean,
            default: false
        },
        injectContainerSelector: {
            type: Function,
            default: () => document.body
        },
        filterPrefix: {
            type: String,
            default: ''
        },
        modelLabel: {
            type: String,
            required: true
        },
        filterPlacement: {
            type: String,
            default: 'bottomLeft'
        },
        popoverMaxWidth: {
            type: [Boolean,Number],
            default: false
        }
    },
    computed: {
        windowWidth() {
            return this.$store.state.windowWidth
        },
        modalWidth() {
            if(this.windowWidth > 700)
                return 700
            else
                return this.windowWidth
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        sortedList() {
            const res = [...this.history.results].map(item => {
                return {
                    ...item,
                    key: this.$moment(item.action_date).format('YYYY-MM-DD'),
                    auid: item.author?.id ? item.author?.id : ''
                }
            }).reduce((accumulator, currentValue, currentIndex, array, key = currentValue.key) => {
                const keyObjectPosition = accumulator.findIndex((item) => item.key === key)
                if (keyObjectPosition >= 0) {
                    accumulator[keyObjectPosition].data.push(currentValue)
                    return accumulator    
                } else {
                    return accumulator.concat({ data: [currentValue], key: key })
                }
            }, [])
            return res
        }
    },
    data() {
        return {
            page_name: `history_${this.related_object}`,
            loading: false,
            modalLoading: false,
            visible: false,
            detail: null,
            page: 0,
            slice_count: 0,
            empty: false,
            open1: false,
            open2: false,
            history: {
                results: [],
                count: 0,
                next: true
            }
        }
    },
    sockets: {
        create_change_history({ data }) {
            this.pushNewHistory(data)
        }
    },
    methods: {
        pushNewHistory(data) {
            this.history.results.unshift({
                ...data,
                action_date: this.$moment().add(-1, 'seconds').format()
            })
            this.slice_count += 1
            this.history.count += 1
        },
        checkTextLength(text) {
            if(text.length > 230)
                return true
            else
                return false
        },
        async openDetail(id) {
            try {
                this.visible = true
                this.modalLoading = true

                const { data } = await this.$http.get(`/change_history/${id}/`)
                if(data) {
                    this.detail = data
                }
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                this.modalLoading = false
            }
        },
        afterClose() {
            this.detail = null
            this.open1 = false
            this.open2 = false
        },
        async getHistory($state) {
            if(!this.loading && this.history.next) {
                try {
                    this.loading = true
                    this.page += 1

                    const params = {
                        page: this.page,
                        page_size: this.page_size,
                        page_name: this.page_name
                    }

                    if(this.slice_count)
                        params.slice_count = this.slice_count

                    if(this.related_object)
                        params.related_object = this.related_object

                    const { data } = await this.$http.get('/change_history/', { params })
                    
                    if(data) {
                        this.history.count = data.count
                        this.history.next = data.next
                    }

                    if(data?.results?.length)
                        this.history.results = this.history.results.concat(data.results)


                    if(this.page === 1 && !this.history.results.length) {
                        this.empty = true
                    }
                        
                    if(this.history.next)
                        $state.loaded()
                    else
                        $state.complete()
                } catch(error) {
                    errorHandler({error, show: false})
                } finally {
                    this.loading = false
                }
            } else {
                $state.complete()
            }
        },
        isDate(value) {
            if(ISO_8601_FULL.test(value) ) {
                return true
            } else {
                return false
            }
        },
        getPopupContainer() {
            if(this.injectContainer) {
                return this.injectContainerSelector()
            } else
                return this.$refs.timeline 
        },
        reload() {
            this.$nextTick(() => {
                this.page = 0
                this.empty = false
                this.history = {
                    results: [],
                    count: 0,
                    next: true
                }
                if(this.$refs.histofy_infinity)
                    this.$refs.histofy_infinity.stateChanger.reset()
            })
        }
    },
    mounted() {
        eventBus.$on(`update_filter_change_history.ChangeHistoryModel`, () => {
            this.reload()
        })
        socketEmitJoin(`detail_${this.related_object}`)
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_change_history.ChangeHistoryModel`)
        socketEmitLeave(`detail_${this.related_object}`)
    }
}
</script>

<style lang="scss" scoped>
.detail_wrapper{
    &__item{
        word-wrap: break-word;
        &:not(:last-child){
            margin-bottom: 5px;
        }
        .item_label{
            margin-right: 5px;
            color: var(--gray);
            font-weight: 300;
        }
    }
    .text_wrapper{
        &:not(.show){
            height: 150px;
            overflow: hidden;
            position: relative;
            &::after{
                content: "";
                position: absolute;
                bottom: 0;
                left: 0;
                width: 100%;
                height: 50px;
                background: linear-gradient(to bottom,  rgba(255,255,255,0) 0%,rgba(255,255,255,1) 84%,rgba(255,255,255,1) 100%); /* W3C, IE10+, FF16+, Chrome26+, Opera12+, Safari7+ */
            }
        }
    }
}
.timeline{
    box-sizing: border-box;
    color: rgba(0,0,0,.65);
    font-size: 14px;
    font-variant: tabular-nums;
    line-height: 1.5;
    font-feature-settings: "tnum";
    margin: 0;
    padding: 0;
    list-style: none;
    .timeline_list-enter-active, .timeline_list-leave-active {
        transition: all 0.3s;
    }
    .timeline_list-enter, .timeline_list-leave-to {
        opacity: 0;
        transform: translateY(30px);
    }
    &.last{
        .timeline__item{
            &:last-child{
                .timeline_tail{
                    display: none;
                }
            }
        }
    }
    &__item{
        position: relative;
        margin: 0;
        font-size: 14px;
        list-style: none;
        padding: 0 0 20px;
        .timeline_tail{
            position: absolute;
            top: 10px;
            left: 4px;
            height: calc(100% - 10px);
            border-left: 2px dashed #e8e8e8;
            &.last{
                height: calc(100% + 36px);
            }
        }
        .timeline_crc{
            position: absolute;
            width: 20px;
            height: 20px;
            left: -4px;
            top: -6px;
        }
        .timeline_content{
            position: relative;
            top: -6px;
            margin: 0 0 0 18px;
            word-break: break-word;
        }
    }
}
.timeline_wrapper{
    background: #eff2f5;
    border-radius: var(--borderRadius);
    padding: 10px 13px;
    position: relative;
    &__item{
        word-wrap: break-word;
        &:not(:last-child){
            margin-bottom: 5px;
        }
        .item_label{
            margin-right: 5px;
            color: var(--gray);
            font-weight: 300;
        }
    }
}
</style>