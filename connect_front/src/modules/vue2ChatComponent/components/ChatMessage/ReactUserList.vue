<template>
    <div class="user_list">
        <a-spin size="small" :spinning="loading" class="w-full">
            <div v-for="user in list" :key="user.id" class="user_list__item">
                <Profiler 
                    :avatarSize="22"
                    nameClass="text-sm"
                    hideSupportTag
                    :user="user" />
            </div>
        </a-spin>
        <infinite-loading ref="userInfinite" @infinite="getList" v-bind:distance="10">
            <div slot="spinner"><a-spin v-if="page !== 1" size="small" /></div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
    </div>
</template>

<script>
import axios from 'axios'
import { errorHandler } from '@/utils/index.js'
export default {
    components: {
        InfiniteLoading: () => import('vue-infinite-loading')
    },
    props: {
        messageItem: {
            type: Object,
            required: true
        },
        reaction: {
            type: Object,
            required: true
        },
        rebuildPopover: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
            cancelSource: null,
            reactLoading: false,
            loading: false,
            scrollStatus: true,
            page: 0,
            list: []
        }
    },
    created() {
        this.getList()
    },
    methods: {
        reloadList() {
            this.list = []
            this.page = 0
            this.scrollStatus = true
            this.getList()
        },
        async getList($state = null) {
            if(!this.loading && this.scrollStatus) {
                try {
                    const axiosSource = axios.CancelToken.source()
                    this.cancelSource = { cancel: axiosSource.cancel }
                    this.loading = true
                    this.page = this.page + 1
                    const params = {
                        page_size: 15,
                        page: this.page,
                        reaction: this.reaction.reaction.id
                    }
                    const { data } = await this.$http.get(`/reactions/related_object/${this.messageItem.message_uid}/users/`, { params, cancelToken: axiosSource.token })
                    if(data && data.results && data.results.length) this.list.push(...data.results)
                    this.rebuildPopover()
                    if(!data.next) {
                        if($state) 
                            $state.complete()
                        this.scrollStatus = false
                    } else {
                        if($state) 
                            $state.loaded()
                    }
                } catch(error) {
                    errorHandler({error, show: false})
                } finally {
                    this.cancelSource = null
                    this.loading = false
                }
            } else {
                if($state) 
                    $state.complete()
            }
        },
    }
}
</script>

<style lang="scss" scoped>
.user_list{
    max-height: 150px;
    overflow-y: auto;
    max-width: 350px;
    &__item{
        &:not(:last-child){
            margin-bottom: 10px;
        }
    }
}
</style>