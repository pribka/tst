<template>
    <a-drawer
        :title="$t('team.invitations')"
        :visible="visible"
        class="my_i_drawer"
        @close="visible = false"
        destroyOnClose
        :width="drawerWidth"
        :afterVisibleChange="afterVisibleChange"
        placement="right">
        <a-spin :spinning="inviteLoading">
            <a-empty v-if="empty && !loading" class="mt-2 mb-2">
                <span slot="description">
                    <div>{{ $t('team.invitations_list_empty') }}</div>
                </span>
            </a-empty>
            <div v-for="item in list" :key="item.id" class="invite_card">
                <div v-if="item.contractor_owner" class="invite_card__item font-semibold flex items-center">
                    <a-avatar 
                        :size="22"
                        :src="item.contractor_owner.logo"
                        icon="fi-rr-users-alt" 
                        flaticon /> 
                    <span class="ml-1">{{ item.contractor_owner.name }} {{ $t('team.invites_you') }}</span>
                </div>
                <div v-if="item.contractor" class="invite_card__item flex items-center">
                    <span class="mr-1">{{ $t('team.organization_label') }} </span>
                    <a-avatar 
                        :size="22"
                        :src="item.contractor.logo"
                        icon="fi-rr-users-alt" 
                        flaticon /> 
                    <span class="ml-1">{{ item.contractor.name }}</span>
                </div>
                <div v-if="item.relation_type" class="invite_card__item">
                    {{ $t('team.connection_type') }} {{ item.relation_type.name }}
                </div>
                <div class="invite_card__item">
                    {{ $t('team.status') }} <a-tag :color="item.status.color">{{ item.status.name }}</a-tag>
                </div>
                <div v-if="item.status && item.status.code === 'new'" class="grid grid-cols-2 gap-1">
                    <a-button block type="primary" ghost @click="inviteAccept(item.id)">
                        {{ $t('team.accept') }}
                    </a-button>
                    <a-button block type="danger" ghost @click="inviteReject(item.id)">
                        {{ $t('team.decline') }}
                    </a-button>
                </div>
            </div>
        </a-spin>
        <Loader
            class="chat__active-chats"
            rowClass="px-2 lg:px-4 py-3"
            v-if="loading && page === 1"
            titleFull
            hideParagraph
            :skeletonRow="7" />
        <infinite-loading ref="userInfinite" @infinite="getList" v-bind:distance="10">
            <div slot="spinner"><a-spin v-if="page !== 1" /></div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
    </a-drawer>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    name: "MyInviteDrawer",
    components: {
        InfiniteLoading: () => import('vue-infinite-loading'),
        Loader: () => import('./InviteDrawer/Loader.vue')
    },
    computed: {
        windowWidth() {
            return this.$store.state.windowWidth
        },
        drawerWidth() {
            if(this.windowWidth > 600)
                return 600
            else {
                return '100%'
            }
        }
    },
    created() {
        eventBus.$on('open_my_invites', () => {
            this.visible = true
        })
    },
    data() {
        return {
            visible: false,
            loading: false,
            inviteLoading: false,
            page: 0,
            list: [],
            scrollStatus: true,
            empty: false
        }
    },
    methods: {
        async inviteAccept(id) {
            try {
                this.inviteLoading = true
                const { data } = await this.$http.post('/contractor_invites/accept/', {
                    id
                })
                if(data) {
                    this.$message.info(this.$t('team.invitation_accepted'))
                    const index = this.list.findIndex(f => f.id === id)
                    if(index !== -1)
                        this.$set(this.list, index, data)
                }
            } catch(error) {
                console.log(error)
                if(error.message)
                    this.$message.error(error.message)
                else
                    this.$message.error(this.$t('team.error'))
            } finally {
                this.inviteLoading = false
            }
        },
        async inviteReject(id) {
            try {
                this.inviteLoading = true
                const { data } = await this.$http.post('/contractor_invites/reject/', {
                    id
                })
                if(data) {
                    this.$message.info(this.$t('team.invitation_rejected'))
                    const index = this.list.findIndex(f => f.id === id)
                    if(index !== -1)
                        this.$set(this.list, index, data)
                }
            } catch(error) {
                console.log(error)
                if(error.message)
                    this.$message.error(error.message)
                else
                    this.$message.error(this.$t('team.error'))
            } finally {
                this.inviteLoading = false
            }
        },
        afterVisibleChange(vis) {
            if(!vis) {
                this.page = 0
                this.list = []
                this.scrollStatus = true
            }
        },
        async getList($state = null) {
            if(!this.loading && this.scrollStatus && this.visible) {
                try {
                    this.loading = true
                    this.page = this.page+1
                    let params = {
                        page_size: 15,
                        page: this.page
                    }

                    const { data } = await this.$http.get('/contractor_invites/for_me/', { params })
                    if(data?.results?.length)
                        this.list = this.list.concat(data.results)
                    else {
                        if(this.page === 1) {
                            this.empty = true
                        }
                    }
                    if(!data.next) {
                        if($state)
                            $state.complete()
                        this.scrollStatus = false
                    } else {
                        if($state)
                            $state.loaded()
                    }
                } catch(e) {

                } finally {
                    this.loading = false
                }
            } else {
                if($state)
                    $state.complete()
            }
        }
    },
    beforeDestroy() {
        eventBus.$off('open_my_invites')
    }
}
</script>

<style lang="scss" scoped>
.my_i_drawer{
    &::v-deep{
        .ant-drawer-content,
        .ant-drawer-wrapper-body{
            overflow: hidden;
        }
        .ant-drawer-body{
            overflow-y: auto;
            height: calc(100% - 40px);
            padding: 0px;
        }
    }
}
.invite_card{
    padding: 10px 15px;
    &:not(:last-child){
        border-bottom: 1px solid var(--border2);
    }
    &__item{
        &:not(:last-child){
            margin-bottom: 10px;
        }
    }
}
</style>