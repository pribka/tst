<template>
    <a-modal
        :title="viewCountText"
        :visible="visible"
        @afterVisibleChange="afterVisibleChange"
        @cancel="visible = false">
        <div class="user_list">
            <div v-for="user in list.results" :key="user.id" class="flex items-center truncate user_item" :title="user.full_name">
                <div class="mr-2">
                    <a-avatar
                        :size="28"
                        :key="user.id"
                        avResize
                        :src="user.avatar && user.avatar.path ? user.avatar.path : ''"
                        icon="user" />
                </div>
                <div class="truncate">
                    {{ user.full_name }}
                </div>
            </div>
        </div>
        <infinite-loading
            v-if="visible"
            ref="users_infinity"
            :identifier="infiniteId"
            @infinite="getList"
            v-bind:distance="10">
            <div
                slot="spinner"
                class="flex items-center justify-center inf_spinner">
                <a-spin size="small" />
            </div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
        <template #footer>
            <a-button type="ui_ghost" block @click="visible = false">
                {{ $t('close') }}
            </a-button>
        </template>
    </a-modal>
</template>

<script>
import { declOfNum } from '@/utils/utils.js'
import { errorHandler } from '@/utils/index.js'
import { mapState } from 'vuex'

export default {
    components: {
        InfiniteLoading: () => import('vue-infinite-loading'),
    },
    props: {
        messageUid: {
            type: String,
            required: true
        },
        viewCount: {
            type: Number,
            default: 0
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        viewCountText() {
            if (!this.viewCount)
                return this.$t('comment.no_view')
            return `${this.viewCount} ${declOfNum(this.viewCount, [this.$t('comment.view1'), this.$t('comment.view2'), this.$t('comment.view3')])}`
        }
    },
    data() {
        return {
            infiniteId: Date.now(),
            page: 0,
            loading: false,
            visible: false,
            list: {
                next: true,
                count: 0,
                results: []
            }
        }
    },
    methods: {
        async getList($state) {
            if(!this.loading && this.list.next) {
                try {
                    this.loading = true
                    this.page += 1
                    const { data } = await this.$http.get(`/chat/message/${this.messageUid}/viewers/`, {
                        params: {
                            page: this.page,
                            page_size: 15
                        }
                    })

                    if(data) {
                        this.list.count = data.count
                        this.list.next = data.next
                        const filteredResults = (data.results || []).filter(user => user.id !== this.user?.id)
                        this.list.results = this.list.results.concat(filteredResults)
                    }

                    if(this.list.next)
                        $state.loaded()
                    else
                        $state.complete()
                } catch(error) {
                    errorHandler({ error, show: false })
                    $state.complete()
                } finally {
                    this.loading = false
                }
            } else if ($state) {
                $state.complete()
            }
        },
        afterVisibleChange(vis) {
            if(!vis)
                this.clearList()
        },
        clearList() {
            this.infiniteId = Date.now()
            this.page = 0
            this.list = {
                next: true,
                count: 0,
                results: []
            }
        },
        openModal() {
            this.visible = true
        }
    }
}
</script>

<style lang="scss" scoped>
.user_list{
    min-height: 50px;
    margin-top: 20px;
}
.user_item{
    &:not(:last-child){
        margin-bottom: 8px;
    }
}

@media (max-width: 864px) {
    .user_item{
        &:not(:last-child){
            margin-bottom: 15px;
        }
    }
}
</style>
