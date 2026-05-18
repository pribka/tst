<template>
    <a-drawer
        :title="$t('wgr.invite_participants')"
        :visible="visible"
        class="meeting_user_drawer"
        @close="close()"
        destroyOnClose
        :width="400"
        placement="right">
        <div class="drawer_search">
            <a-input-search 
                :loading="loading"
                v-model="search"
                @input="onSearch"
                :placeholder="$t('wgr.search')" />
        </div>
        <div class="drawer_body">
            <a-empty 
                v-if="!loading && !userDrawer.next && !userDrawer.results.length"
                class="mt-4"
                :description="$t('wgr.users_not_fount')" />
            <div class="user_list">
                <UserCard 
                    v-for="user in userDrawer.results" 
                    :key="user.id"
                    :user="user"
                    :currentUser="user" />
            </div>
            <infinite-loading
                v-if="userDrawer.next"
                @infinite="getUserDrawer"
                :identifier="infinityId"
                v-bind:distance="10">
                <div slot="spinner"><a-spin /></div>
                <div slot="no-more"></div>
                <div slot="no-results"></div>
            </infinite-loading>
        </div>
        <div class="drawer_footer">
            <a-button 
                type="primary"
                :loading="btnLoading"
                @click="close()">
                {{ $t('wgr.select') }}
            </a-button>
        </div>
    </a-drawer>
</template>

<script>
import { mapState } from "vuex"
import InfiniteLoading from 'vue-infinite-loading'
import UserCard from './UserCard.vue'
let timer;
export default {
    components: {
        InfiniteLoading,
        UserCard
    },
    props: {
        value: [Array],
        visible: {
            type: Boolean,
            default: false
        },
        drawerClose: {
            type: Function,
            default: () => {}
        },
        partisipants: {
            type: Array,
            default: () => []
        }
    },
    computed: {
        ...mapState({
            userDrawer: state => state.workgroups.userDrawer,
            currentUser: state => state.user.user
        })
    },
    data() {
        return {
            loading: false,
            btnLoading: false,
            selectedUsers: [],
            searchLoading: false,
            search: '',
            infinityId: 'default'
        }
    },
    methods: {
        close(update = false) {
            this.$store.commit('workgroups/CLEAR_USER_LIST')
            this.selectedUsers = []
            this.search = ''
            this.infinityId = 'default'
            this.drawerClose(update)
        },
        onSearch() {
            clearTimeout(timer)
            timer = setTimeout(() => {
                this.$store.commit('workgroups/CLEAR_USER_LIST')
                if(this.search?.length)
                    this.infinityId = this.search
                else
                    this.infinityId = 'default'
            }, 800)
        },
        async getUserDrawer($state) {
            if(!this.loading && this.userDrawer.next) {
                try {
                    this.loading = true
                    await this.$store.dispatch('workgroups/getUserDrawer', {
                        search: this.search
                    })
                    if(this.userDrawer.next)
                        $state.loaded()
                    else
                        $state.complete()
                } catch (e) {
                    console.log(e)
                } finally {
                    this.loading = false
                }
            }
        },
        selectUser(user) {
            
        }
    }
}
</script>

<style lang="scss">
.meeting_user_drawer{
    .user_list{
        .user_card{
            &:not(:last-child){
                border-bottom: 1px solid #e8e8e8;
            }
        }
    }
    .ant-drawer-wrapper-body,
    .ant-drawer-content{
        overflow: hidden;
    }
    .ant-drawer-header{
        padding-left: 20px;
        padding-right: 20px;
    }
    .drawer_search{
        height: 40px;
        border-bottom: 1px solid var(--border2);
        input{
            border: 0px;
            height: 39px;
            border-radius: 0px;
            padding-left: 20px;
            padding-right: 20px;
        }
    }
    .ant-drawer-body{
        height: calc(100% - 40px);
        padding: 0px;
        .drawer_body{
            height: calc(100% - 80px);
            overflow-y: scroll;
        }
        .drawer_footer{
            display: flex;
            align-items: center;
            height: 40px;
            border-top: 1px solid var(--border2);
            padding-left: 20px;
            padding-right: 20px;
        }
    }
}
</style>