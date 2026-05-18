<template>
    <div>
        <a-empty v-if="empty && !loading" class="mt-2 mb-2">
            <span slot="description">
                <div>{{ $t('team.invitations_list_empty') }}</div>
                <a-button type="primary" ghost class="mt-3" @click="inviteHandler()">
                    {{ $t('team.invite_user') }}
                </a-button>
            </span>
        </a-empty>
        <div v-for="item in list" :key="item.id" class="invite_card">
            <div class="invite_card__item">
                E-mail: <a :href="`mailto:${item.email}`">{{ item.email }}</a>
            </div>
            <div class="invite_card__item">
                {{ $t('team.invitation_date') }} {{ $moment(item.created_at).format('DD.MM.YYYY HH:mm') }}
            </div>
            <div v-if="item.workgroup" class="invite_card__item">
                {{ $t('team.group') }} 123
            </div>
            <div class="invite_card__item">
                {{ $t('team.sending_status') }} <a-tag :color="item.is_sent ? 'green' : 'red'">{{ item.is_sent ? $t('team.sent') : $t('team.not_sent') }}</a-tag>
            </div>
            <div class="invite_card__item">
                {{ $t('team.registered') }} <a-tag :color="item.is_accepted ? 'green' : 'red'">{{ item.is_accepted ? $t('team.yes') : $t('team.no') }}</a-tag>
            </div>
        </div>
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
            empty: false
        }
    },
    methods: {
        inviteHandler() {
            eventBus.$emit('open_invite', this.org.id)
            this.closeDrawer()
        },
        async getList($state = null) {
            if(!this.loading && this.scrollStatus) {
                try {
                    this.loading = true
                    this.page = this.page+1
                    let params = {
                        page_size: 15,
                        page: this.page
                    }

                    const { data } = await this.$http.get(`/users/my_organizations/${this.org.id}/email_invite/`, { params })
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