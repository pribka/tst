<template>
    <div>
        <a-spin v-if="loading"/>
        <a-drawer
            :title="$t('meeting.addParticipant')"
            :visible="visible"
            class="meeting_user_drawer"
            @close="close()"
            :zIndex="1060"
            destroyOnClose
            :width="drawerWidth"
            placement="right">
            <div class="drawer_search">
                <a-input-search 
                    :loading="loading"
                    v-model="search"
                    @input="onSearch"
                    :placeholder="$t('meeting.search')" />
            </div>
            <div class="drawer_body mt_scroll">
                <RecycleScroller
                    :items="userDrawer.results"
                    size-field="height"
                    :buffer="200"
                    emitUpdate
                    :item-size="49"
                    key-field="id">
                    <template #before>
                        <OldSelected 
                            ref="meetingOldSelector"
                            multiple
                            :itemSelect="selectUser"
                            :checkSelected="checkSelected"
                            :getPopupContainer="getPopupContainer" />
                    </template>
                    <template #default="{ item }">
                        <UserCard 
                            :selectUser="selectUser"
                            :selected="selected"
                            :user="item" />
                    </template>
                    <template #after>
                        <infinite-loading
                            v-if="userDrawer.next"
                            @infinite="getUserDrawer"
                            :identifier="infinityId"
                            v-bind:distance="10">
                            <div slot="spinner"><a-spin /></div>
                            <div slot="no-more"></div>
                            <div slot="no-results"></div>
                        </infinite-loading>
                    </template>
                </RecycleScroller>
            </div>
            <div class="drawer_footer">
                <a-button 
                    type="ui" 
                    ghost
                    block
                    @click="close()">
                    {{ $t('meeting.close') }}
                </a-button>
            </div>
        </a-drawer>
    </div>
</template>

<script>
import { mapState } from "vuex"
import InfiniteLoading from 'vue-infinite-loading'
import { RecycleScroller } from 'vue-virtual-scroller'
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css'
let timer;
export default {
    name: "MeetingUserDrawer",
    components: {
        InfiniteLoading,
        UserCard: () => import('./UserCard.vue'),
        OldSelected: () => import('@apps/DrawerSelect/OldSelected.vue'),
        RecycleScroller
    },
    props: {
        value: [Array],
        deleted: [Array],
        visible: {
            type: Boolean,
            default: false
        },
        drawerClose: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        ...mapState({
            userDrawer: state => state.meeting.userDrawer,
            windowWidth: state => state.windowWidth
        }),
        drawerWidth() {
            if(this.windowWidth > 500)
                return 400
            else {
                return '100%'
            }
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    data() {
        return {
            loading: false,
            search: '',
            selected: this.value,
        
            infinityId: 'default'
        }
    },
    
    methods: {
        getPopupContainer() {
            return document.querySelector('.mt_scroll')
        },
        close() {
            this.$store.commit('meeting/CLEAR_USER_LIST')
            this.search = ''
            this.infinityId = 'default'
            this.drawerClose()
        },
        onSearch() {
            clearTimeout(timer)
            timer = setTimeout(() => {
                this.$store.commit('meeting/CLEAR_USER_LIST')
                if(this.search?.length)
                    this.infinityId = this.search
                else
                    this.infinityId = 'default'
            }, 800)
        },
        checkSelected(user) {
            const index = this.selected.findIndex(u => u.id === user.id)
            if(index !== -1)
                return true
            else
                return false
        },
        async getUserDrawer($state) {
            if(!this.loading && this.userDrawer.next) {
                try {
                    this.loading = true
                    await this.$store.dispatch('meeting/getUserDrawer', {
                        search: this.search
                    })
                    if(this.userDrawer.next)
                        $state.loaded()
                    else
                        $state.complete()
                    this.selected = this.value
                } catch (e) {
                    console.log(e)
                } finally {
                    this.loading = false
                }
            }
        },
        selectUser(user) {
            let users = this.value
            let deleted = this.deleted
         

            const index = users.findIndex(f => f.id === user.id)

            if(index !== -1) {
                users.splice(index, 1)
            
                if(!users[index]?.added){ 
                    deleted.push(user)
                    this.$emit('deleted', deleted)
                }

                this.$emit('input', users)
             
            } else {
                
                users.push({
                    ...user,
                    is_moderator: false,
                    added: true,
                })

                const index = deleted.findIndex(f => f.id === user.id)
                if(index !== -1) deleted.splice(index, 1)

                // console.log("FIND NONE", users)
                
                this.$emit('deleted', deleted)
                this.$emit('input', users)
            }
            this.selected = users

            this.$refs.meetingOldSelector.saveSelect(user)
        }
    }
}
/*
.user_list{
        .user_card{
            &:not(:last-child){
                border-bottom: 1px solid #e8e8e8;
            }
        }
    }
    */
</script>

<style lang="scss" scoped>
.meeting_user_drawer{
    &::v-deep{
        .ant-drawer-wrapper-body,
        .ant-drawer-content{
            overflow: hidden;
        }
        .ant-drawer-header{
            padding-left: 20px;
            padding-right: 20px;
        }
        .ant-drawer-body{
            height: calc(100% - 40px);
            padding: 0px;
            .drawer_body{
                height: calc(100% - 80px);
                overflow: hidden;
                .vue-recycle-scroller{
                    overflow-y: auto;
                    height: 100%;
                    .vue-recycle-scroller__item-view{
                        &:not(:last-child){
                            .user_card{
                                border-bottom: 1px solid #e8e8e8;
                            }
                        }
                    }
                }
            }
            .drawer_footer{
                display: flex;
                align-items: center;
                height: 40px;
                border-top: 1px solid #e8e8e8;
                padding-left: 20px;
                padding-right: 20px;
            }
        }
    }
    .drawer_search{
        height: 40px;
        border-bottom: 1px solid var(--border2);
        &::v-deep{
            input{
                border: 0px;
                height: 39px;
                border-radius: 0px;
                padding-left: 20px;
                padding-right: 20px;
            }
        }
    }
}
</style>