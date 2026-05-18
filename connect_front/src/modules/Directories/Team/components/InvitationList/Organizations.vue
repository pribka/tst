<template>
    <div>
        <a-empty v-if="empty && !loading" class="mt-2 mb-2">
            <span slot="description">
                <div>{{ $t('team.invitations_list_empty') }}</div>
                <a-button type="primary" ghost class="mt-3" @click="inviteHandler()">
                    {{ $t('team.invite_organization') }}
                </a-button>
            </span>
        </a-empty>
        <a-spin :spinning="spinLoading">
            <div v-for="item in list" :key="item.id" class="invite_card">
                <div v-if="item.contractor" class="invite_card__item flex items-center">
                    <span class="mr-1">{{ $t('team.organization_label') }} </span>
                    <a-avatar 
                        :size="22"
                        :src="item.contractor.logo"
                        icon="picture" /> 
                    <span class="ml-1">{{ item.contractor.name }}</span>
                </div>
                <div v-if="item.relation_type" class="invite_card__item">
                    {{ $t('team.connection_type') }} {{ item.relation_type.name }}
                </div>
                <div class="invite_card__item">
                    {{ $t('team.status') }} <a-tag :color="item.status.color">{{ item.status.name }}</a-tag>
                </div>
                <div v-if="item.status && item.status.code === 'new'">
                    <a-button type="danger" block ghost @click="inviteDelete(item.id)">
                        {{ $t('team.cancel') }}
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
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    props: {
        org: {
            type: [Object],
            required: true
        },
        closeDrawer: {
            type: Function,
            default: () => {}
        }
    },
    components: {
        InfiniteLoading: () => import('vue-infinite-loading'),
        Loader: () => import('../InviteDrawer/Loader.vue')
    },
    data() {
        return {
            loading: false,
            page: 0,
            list: [],
            scrollStatus: true,
            spinLoading: false,
            empty: false
        }
    },
    methods: {
        async inviteDelete(id) {
            try {
                this.spinLoading = true
                const { data } = await this.$http.post('/contractor_invites/delete/', {
                    id
                })
                if(data === 'ok') {
                    this.$message.info(this.$t('team.invitation_cancelled'))
                    const index = this.list.findIndex(f => f.id === id)
                    if(index !== -1) {
                        this.$set(this.list[index], 'status', {
                            code: 'deleted',
                            name: this.$t('team.cancelled'),
                            color: 'purple'
                        })
                    }
                }
            } catch(error) {
                console.log(error)
                if(error.message) {
                    this.$message.error(error.message)
                } else {
                    this.$message.error(this.$t('team.error'))
                }
            } finally {
                this.spinLoading = false
            }
        },
        inviteHandler() {
            eventBus.$emit('invite_organization', this.org)
            this.closeDrawer()
        },
        async getList($state = null) {
            if(!this.loading && this.scrollStatus) {
                try {
                    this.loading = true
                    this.page = this.page+1
                    let params = {
                        page_size: 15,
                        page: this.page,
                        contractor_owner: this.org.id
                    }

                    const { data } = await this.$http.get(`/contractor_invites/my/`, { params })
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
    }
}
</script>

<style lang="scss" scoped>
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