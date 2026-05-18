<template>
    <a-drawer
        :title="$t('project.invite_participants')"
        :visible="visible"
        class="group_user_drawer"
        @close="close()"
        destroyOnClose
        :width="isMobile ? windowWidth : 400"
        :zIndex="1010"
        placement="right">
        <div class="drawer_search">
            <a-input-search 
                :loading="loading"
                v-model="search"
                @input="onSearch"
                :placeholder="$t('project.search')" />
        </div>
        <div class="drawer_body">
            <a-empty 
                v-if="!loading && !userDrawer.next && !userDrawer.results.length"
                class="mt-4"
                :description="$t('project.users_not_fount')" />
            <div class="user_list">
                <UserCard 
                    v-for="user in userDrawer.results" 
                    :key="user.id"
                    :selectUser="selectUser"
                    :selectedUsers="selectedUsers"
                    :user="user"
                    :partisipants="partisipants"
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
                type="ui"
                block
                ghost
                :loading="btnLoading"
                @click="save()">
                {{ $t('project.save') }}
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
        visible: {
            type: Boolean,
            default: false
        },
        drawerClose: {
            type: Function,
            default: () => {}
        },
        id: {
            type: [String, Number],
            default: null
        },
        partisipants: {
            type: Array,
            default: () => []
        }
    },
    computed: {
        ...mapState({
            userDrawer: state => state.projects.userDrawer,
            currentUser: state => state.user.user,
            windowWidth: state => state.windowWidth,
            isMobile: state => state.isMobile
        }),
        
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
            this.$store.commit('projects/CLEAR_USER_LIST')
            this.selectedUsers = []
            this.search = ''
            this.infinityId = 'default'
            this.drawerClose(update)
        },
        onSearch() {
            clearTimeout(timer)
            timer = setTimeout(() => {
                this.$store.commit('projects/CLEAR_USER_LIST')
                if(this.search?.length)
                    this.infinityId = this.search
                else
                    this.infinityId = 'default'
            }, 800)
        },
        async save() {
            if(this.selectedUsers.length) {
                try {
                    this.btnLoading = true
                    const queryData = this.selectedUsers.map(user => user.id)
                    await this.$http.post(`/work_groups/workgroups/${this.id}/send_invitations/`, {
                        profile_id: queryData
                    })
                    this.$message.success(this.$t('project.successful'))
                    this.selectedUsers = []
                    this.close(true)
                } catch(e) {
                    console.log(e)
                } finally {
                    this.btnLoading = false
                }
            } else {
                this.selectedUsers = []
                this.close()
            }
        },
        async getUserDrawer($state) {
            if(!this.loading && this.userDrawer.next) {
                try {
                    this.loading = true
                    await this.$store.dispatch('projects/getUserDrawer', {
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
            const find = this.partisipants.find(f => f.id === user.id)
            if(!find) {
                const index = this.selectedUsers.findIndex(f => f.id === user.id)
                if(index !== -1)
                    this.selectedUsers.splice(index, 1)
                else
                    this.selectedUsers.push(user)
            }
        }
    }
}
</script>

<style lang="scss">
.group_user_drawer{
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
        padding-left: 15px;
        padding-right: 15px;
    }
    .drawer_search{
        height: 40px;
        border-bottom: 1px solid var(--border2);
        input{
            border: 0px;
            height: 39px;
            border-radius: 0px;
            padding-left: 15px;
            padding-right: 15px;
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
            padding-left: 15px;
            padding-right: 15px;
        }
    }
}
</style>