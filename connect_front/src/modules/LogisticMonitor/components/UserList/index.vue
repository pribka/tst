<template>
    <div class="h-full m_user_list">
        <div class="pb-3 flex items-center top_actions">
            <PageFilter 
                class="w-full"
                model="users.ProfileModel"
                :key="page_name"
                size="large"
                :page_name="page_name" />
        </div>
        <a-spin
            :spinning="loading" 
            class="w-full">
            <UserCard 
                v-for="user in logisticUsers" 
                :key="user.id" 
                :ref="`us_log_${user.id}`"
                :openTask="openTask"
                :onDropInTimer="onDropInTimer"
                :user="user" />
        </a-spin>
    </div>
</template>

<script>
import UserCard from './UserCard.vue'
import { mapState } from 'vuex'
import PageFilter from '@/components/PageFilter'
import eventBus from '@/utils/eventBus'
let dropTimer;
let timerId;
export default {
    props: {
        openTask: {
            type: Function,
            default: () => {}
        },
        scrollTop: {
            type: Function,
            default: () => {}
        }
    },
    components: {
        UserCard,
        PageFilter
    },
    computed: {
        ...mapState({
            logisticUsers: state => state.monitor.logisticUsers,
            loading: state => state.monitor.userListLoader,
            listRequest: state => state.monitor.userListRequest,
            userLocation: state => state.monitor.userLocation
        })
    },
    data() {
        return {
            page_name: 'user_monitor'
        }
    },
    created() {
        this.getUserList()
    },
    sockets: {
        monitor(data) {
            this.$store.commit('monitor/SET_USER_LOCATIONS', data)
        }
    },
    methods: {
        onDropInTimer(data) {
            if(timerId && timerId === data.id) {
                // this.$refs[`log_card_${data.id}`][0].getDeliveryPoints()
            } else {
                timerId = data.id
                clearTimeout(dropTimer)
                dropTimer = setTimeout(() => {
                    this.$refs[`us_log_${data.id}`][0].getDeliveryPoints()
                }, 700)
            }
        },
        async getUserList(topScroll = false) {
            try {
                await this.$store.dispatch('monitor/getUserList', {
                    page_name: this.page_name
                })
                this.$socket.client.emit('logistic_join')

                if(topScroll) {
                    this.scrollTop('tab_users')
                }
            } catch(e) {
                console.log(e)
            }
        },
        checkRequest() {
            if(this.listRequest) {
                this.listRequest.cancel()
                this.$store.commit('monitor/SET_USER_LIST_REQUEST', null)
            }
        }
    },
    mounted() {
        eventBus.$on(`update_filter_users.ProfileModel`, () => {
            this.$store.commit('monitor/FILTER_HANDLER')
            eventBus.$emit('TOGGLE_TASK_DRAWER_logistic')
            this.checkRequest()
            this.getUserList(true)
        })
    },
    beforeDestroy() {
        eventBus.$off('update_filter_users.ProfileModel')
        this.$socket.client.emit('logistic_leave')
        this.$store.commit('monitor/CLEAR_USER_LOCATION')
        this.checkRequest()
    }
}
</script>

<style lang="scss" scoped>
.m_user_list{
    .top_actions{
        background: rgba(255, 255, 255, 0.95);
        margin-left: -15px;
        margin-right: -15px;
        padding-left: 15px;
        padding-right: 15px;
        padding-top: 15px;
        margin-top: -15px;
        position: sticky;
        top: 0;
        z-index: 5;
    }
}
</style>