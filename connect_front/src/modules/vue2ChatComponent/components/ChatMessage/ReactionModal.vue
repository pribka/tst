<template>
    <a-modal
        :title="$t('chat.reactions')"
        :visible="visible"
        @cancel="visible = false">
        <div class="user_list pt-4">
            <div v-for="item in workList" :key="item.id" class="user_list__item flex items-center justify-between truncate">
                <Profiler 
                    :avatarSize="28"
                    nameClass="text-sm truncate"
                    class="truncate"
                    hideSupportTag
                    :user="item.user" />
                <div class="ml-3" style="font-size: 26px;">
                    {{ item.reaction.icon }}
                </div>
            </div>
        </div>
        <infinite-loading ref="userInfinite" @infinite="getWorkList" v-bind:distance="10">
            <div slot="spinner"><a-spin v-if="page !== 1" size="small" /></div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
        <template #footer>
            <a-button type="ui_ghost" @click="visible = false" size="large" block>
                {{ $t('close') }}
            </a-button>
        </template>
    </a-modal>
</template>

<script>
export default {
    components: {
        InfiniteLoading: () => import('vue-infinite-loading')
    },
    props: {
        messageItem: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            visible: false,
            scrollStatus: true,
            page: 0,
            loading: false,
            workList: []
        }
    },
    methods: {
        openModal() {
            this.visible = true
        },
        async getWorkList($state = null) {
            if(!this.loading && this.scrollStatus && this.visible) {
                try {
                    this.loading = true
                    this.page = this.page + 1
                    let params = {
                        page_size: 15,
                        page: this.page
                    }
                    const { data } = await this.$http.get(`/reactions/related_object/${this.messageItem.message_uid}/users/`, { params })
                    if(data?.results?.length) this.workList.push(...data.results)
                    if(!data.next) {
                        if($state) $state.complete()
                        this.scrollStatus = false
                    } else {
                        if($state) $state.loaded()
                    }
                } finally {
                    this.loading = false
                }
            } else {
                if($state) $state.complete()
            }
        },
    }
}
</script>

<style lang="scss" scoped>
.user_list{
    &__item{
        &:not(:last-child){
            margin-bottom: 10px;
        }
    }
}
</style>