<template>
    <a-popover 
        v-model="visible" 
        :title="viewCountText" 
        trigger="click"
        :getPopupContainer="getPopupContainer"
        overlayClassName="views_popup"
        transitionName=""
        @visibleChange="visibleChange">
        <slot />
        <template #content>
            <div class="user_list">
                <div v-for="user in list.results" :key="user.id" class="flex items-center truncate user_item" :title="user.full_name">
                    <div class="mr-2">
                        <a-avatar
                            :size="22" 
                            :key="user.id"
                            avResize
                            :src="user.avatar && user.avatar.path ? user.avatar.path : ''"
                            icon="user" />
                    </div>
                    <div class="truncate">
                        {{ user.full_name }}
                    </div>
                </div>
                <infinite-loading 
                    v-if="visible && list.next"
                    ref="users_infinity"
                    @infinite="getList"
                    :identifier="infiniteId"
                    v-bind:distance="10">
                    <div 
                        slot="spinner"
                        class="flex items-center justify-center inf_spinner">
                        <a-spin size="small" />
                    </div>
                    <div slot="no-more"></div>
                    <div slot="no-results"></div>
                </infinite-loading>
            </div>
            <div class="footer_content">
                <a-button type="ui_ghost" size="small" block @click="visible = false">
                    {{ $t('close') }}
                </a-button>
            </div>
        </template>
    </a-popover>
</template>

<script>
import { declOfNum } from '@/utils/utils.js'
import { errorHandler } from '@/utils/index.js'
import { mapState } from 'vuex'
export default {
    props: {
        item: {
            type: Object,
            required: true
        },
        getPopupContainer: {
            type: Function,
            default: () => document.body
        }
    },
    components: {
        InfiniteLoading: () => import('vue-infinite-loading'),
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        viewCount() {
            const count = this.item.viewer_count - 1
            if(count < 0)
                return 0
            return count
        },
        viewCountText() {
            return `${this.viewCount} ${declOfNum(this.viewCount, [this.$t('comment.view1'), this.$t('comment.view2'), this.$t('comment.view3')])}`
        },
        isMobile() {
            return this.$store.state.isMobile
        },
    },
    data() {
        return {
            visible: false,
            infiniteId: Date.now(),
            page: 0,
            loading: false,
            list: {
                next: true,
                count: 0,
                results: []
            }
        }
    },
    methods: {
        visibleChange(vis) {
            if(!vis)
                this.clearList()
        },
        clearList() {
            if (this.$refs.users_infinity) {
                this.$refs.users_infinity.stateChanger.complete()
            }

            this.infiniteId = Date.now()
            this.page = 0
            this.list = {
                next: true,
                count: 0,
                results: []
            }
        },
        openPopup() {
            this.visible = true
        },
        async getList($state) {
            if(!this.loading && this.list.next) {
                try {
                    this.loading = true
                    this.page += 1
                    const { data } = await this.$http.get('/viewers/', {
                        params: {
                            related_object: this.item.id,
                            page: this.page,
                            page_size: 15
                        }
                    })

                    if(data) {
                        this.list.count = data.count
                        this.list.next = data.next
                    }

                    if (data?.results?.length) {
                        const filtered = data.results.filter(u => u.id !== this.user.id)
                        this.list.results = this.list.results.concat(filtered)
                    }

                    if(this.list.next)
                        $state.loaded()
                    else
                        $state.complete()
                } catch(error) {
                    errorHandler({error, show: false})
                } finally {
                    this.loading = false
                }
            }
        },
    }
}
</script>

<style lang="scss" scoped>
.user_item{
    &:not(:first-child){
        margin-top: 15px;
    }
}
.user_list{
    max-width: 270px;
    min-width: 270px;
    padding: 12px 16px;
    overflow-y: auto;
    max-height: 220px;
}
.footer_content{
    padding: 8px 16px;
}
</style>

<style lang="scss">
.views_popup{
    .ant-popover-arrow{
        display: none;
    }
    .ant-popover-title{
        border-bottom: 0px;
    }
    &.ant-popover-placement-top, 
    &.ant-popover-placement-topLeft, 
    &.ant-popover-placement-topRight{
        padding-bottom: 0px;
    }
    &.ant-popover-placement-bottom, 
    &.ant-popover-placement-bottomLeft, 
    &.ant-popover-placement-bottomRight{
        padding-top: 0px;
    }
    .ant-popover-inner-content{
        padding: 0px;
    }
}
</style>