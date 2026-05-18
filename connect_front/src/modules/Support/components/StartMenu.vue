<template>
    <div class="sup_menu">
        <div class="sup_menu__item" @click="portalNews()">
            <div class="item_wrapper">
                <i class="fi fi-rr-megaphone"></i>
                <div class="text">
                    <div class="text_t">{{ $t('support.newsFeed') }}</div>
                    <div class="sup">{{ $t('support.gos24Info', { app_name: appName }) }}</div>
                </div>
            </div>
            <a-badge :count="unreadCount" :number-style="{ backgroundColor: '#52c41a' }" />
        </div>
        <div class="sup_menu__item" @click="supportBase()">
            <div class="item_wrapper">
                <i class="fi fi-rr-messages-question"></i>
                <div class="text">
                    <div class="text_t">{{ $t('support.knowledgeBase') }}</div>
                    <div class="sup">{{ $t('support.instructions') }}</div>
                </div>
            </div>
        </div>
        <!--<div class="sup_menu__item" @click="supportChat()">
            <div class="item_wrapper">
                <i class="fi fi-rr-paper-plane"></i>
                <div class="text">
                    <div class="text_t">{{ $t('support.techSupportChat') }}</div>
                    <div class="sup">{{ $t('support.contactTechSupport') }}</div>
                </div>
            </div>
        </div>-->
    </div>
</template>

<script>
export default {
    props: {
        closePopup: {
            type: Function,
            default: () => {}
        },
        unreadCount: {
            type: [String, Number],
            default: 0
        }
    },
    data() {
        return {
            appName: process.env.VUE_APP_NAME || 'Gos24.КОННЕКТ'
        }
    },
    methods: {
        portalNews() {
            const query = {...this.$route.query, newList: 'true'}
            this.$router.push({ query })
            this.closePopup()
        },
        supportBase() {
            const query = {...this.$route.query}
            query.help = true
            if(query.newList)
                delete query.newList
            this.$router.push({ query })
            this.closePopup()
        },
        supportChat() {
            this.$router.push({ name: 'chat' })
            this.closePopup()
        }
    }
}
</script>

<style lang="scss" scoped>
.sup_menu{
    &__item{
        cursor: pointer;
        display: flex;
        padding: 10px 15px;
        align-items: center;
        justify-content: space-between;
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
        user-select: none;
        .item_wrapper{
            display: flex;
            align-items: center;
        }
        i{
            margin-right: 15px;
            font-size: 24px;
            color: var(--blue);
        }
        .text_t{
            color: #000000;
            font-size: 16px;
        }
        .sup{
            color: var(--gray);
            font-weight: 300;
        }
        &:hover{
            background: var(--primaryHover);
        }
    }
}
</style>
