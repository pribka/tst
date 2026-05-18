<template>
    <div class="bell action_btn" @click="pushRoute" >
        <a-badge :count="totalUnreadCount" style="max-width: 32px;" :offset="[0, 9]" class="cursor-pointer">
            <a-button 
                type="link" 
                v-tippy
                :content="$t('noty.notificationList')"
                class="text-current">
                <i class="fi fi-rr-bell" />
            </a-button>
        </a-badge>
    </div>
</template>
<script>
import { mapActions } from 'vuex'
export default {
    name: "NotificationBell",
    computed:{
        totalUnreadCount(){
            const unreadCount = Number(this.$store.state.notifications.unreadCount) || 0
            const unreadMentionsCount = Number(this.$store.state.notifications.unreadMentionsCount) || 0
            return unreadCount + unreadMentionsCount
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    methods: {
        ...mapActions({
            getUnreadCount: 'notifications/getUnreadCount'
        }),
        pushRoute() {
            this.$store.commit('notifications/SET_DRAWER_VISIBLE', true)
        }
    },
    mounted() {
        if(this.isMobile) {
            window.addEventListener("focus", () => {
                this.getUnreadCount()
            })
        }
    }
}
</script>

<style lang="scss">
.n_popover{
    &.ant-popover{
        z-index: 800;
    }
    .ant-popover-inner{
        .ant-popover-inner-content{
            padding: 0
        }
    }
}
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
 .popver_content  {
        width: 380px !important;
        .empty_notify{
            text-align: center;
            padding: 20px 0px;
            i{
                font-size: 44px;
                opacity: 0.7;
            }
            p{
                margin-bottom: 0px;
                margin-top: 10px;
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

.nav_drop_menu{
    border: 1px solid var(--borderColor);
    min-width: 300px;
    max-width: 300px;
    box-shadow: 0 3px 6px -4px rgba(0, 0, 0, 0.012), 0 6px 16px 0 rgba(0, 0, 0, 0.08), 0 9px 28px 8px rgba(0, 0, 0, 0.05);
}
.nav_dropdown{
    .drop_header{
        border-bottom: 1px solid var(--borderColor);
    }
    .drop_body{
       max-height: 280px;
        .desc{
            color: var(--text);
        }
        .notify_date{
            font-size: 12px;
         
        }
        li{
            transition: background-color .15s ease;
            &:not(:last-child){
                border-bottom: 1px solid var(--borderColor);
            }
            &:hover{
                background-color: #f5f5f5;
            }
        }
    }
    .drop_footer{
        border-top: 1px solid var(--borderColor);
        transition: opacity .30s ease;
        &:hover{
            opacity: 0.8;
        }
    }
}
</style>
