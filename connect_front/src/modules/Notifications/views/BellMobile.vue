<template>
    <div class="bell action_btn cursor-pointer" @click="pushRoute">
        <a-badge :count="totalUnreadCount" style="max-width: 32px;" :offset="[0, 9]">
            <a-button type="link" class="text-current">
                <i class="fi fi-rr-bell"></i>
            </a-button>
        </a-badge>
    </div>
</template>
<script>
import { mapState, mapActions } from 'vuex'
export default {
    name: "NotificationBell",
    computed:{
        totalUnreadCount(){
            const unreadCount = Number(this.$store.state.notifications.unreadCount) || 0
            const unreadMentionsCount = Number(this.$store.state.notifications.unreadMentionsCount) || 0
            return unreadCount + unreadMentionsCount
        },
        ...mapState({
            user: "user"
        })
    },
    methods: {
        ...mapActions({
            getUnreadCount: 'notifications/getUnreadCount'
        }),
        pushRoute(){
            if(this.$route.name !== 'notifications')
                this.$router.push({name: 'notifications'})
        }
    },
    mounted() {
        window.addEventListener("focus", () => {
            this.getUnreadCount()
        })
    }
}
</script>

<style lang="scss">
.notify_badge{
    .ant-badge-count{
        min-width: 15px;
        height: 15px;
        line-height: 15px;
        top: 7px;
        right: 6px;
        font-size: 10px;
        &.ant-badge-multiple-words{
            padding: 0 4px;
        }
        .ant-scroll-number-only{
            height: 15px;
            p{
                height: 15px;
            }
        }
    }
}
.bell .ant-badge-count{
    font-size: 10px !important;
    min-width: 17px;
    height: 17px;
    padding: 0 6px;
    line-height: 17px;
}    
</style>
