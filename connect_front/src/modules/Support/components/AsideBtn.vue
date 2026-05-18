<template>
    <div class="a_m__b--i a_i">
        <a-popover 
            v-model="visible"
            :title="$t('support.helpAndSupport')" 
            overlayClassName="support_popup"
            placement="rightTop"
            trigger="click">
            <template slot="content">
                <StartMenu 
                    :closePopup="closePopup" 
                    :unreadCount="unreadCount" />
            </template>
            <div class="relative i_w">
                <div class="i_w__c">
                    <div class="icon">
                        <i class="fi fi-rr-info" />
                    </div>
                    <div v-if="isHovered" class="name">
                        {{ $t('support.documentation') }}
                    </div>
                </div>
            </div>
        </a-popover>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'
export default {
    components: {
        StartMenu: () => import('./StartMenu.vue')
    },
    props: {
        isHovered: {
            type: Boolean,
            default: true
        }
    },
    data() {
        return {
            visible: false,
            unreadCount: 0
        }
    },
    created() {
        this.getNewsCount()
    },
    methods: {
        closePopup() {
            this.visible = false
        },
        async getNewsCount() {
            try {
                const { data } = await this.$http.get('/news/news/unread_count/')
                if(data?.unread_count) {
                    this.unreadCount = data.unread_count
                }
            } catch(error) {
                errorHandler({ error, show: false })
            }
        },
        changeCount() {
            if(this.unreadCount > 0) {
                this.unreadCount -= 1
            } else {
                this.unreadCount = 0
            }
        }
    },
    mounted() {
        eventBus.$on('read_news_count', () => {
            this.changeCount()
        })
    },
    beforeDestroy() {
        eventBus.$off('read_news_count')
    }
}
</script>

<style lang="scss" scoped>
.action_btn{
    &::v-deep{
        .ant-badge-count{
            min-width: 15px;
            height: 15px;
            line-height: 15px;
            top: 9px;
            right: 3px;
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
        .ant-badge-count{
            font-size: 10px !important;
            min-width: 17px;
            height: 17px;
            padding: 0 6px;
            line-height: 17px;
        }   
    }
}
</style>

<style lang="scss">
.support_popup{
    .ant-popover-inner-content{
        padding: 0px;
    }
}
</style>
