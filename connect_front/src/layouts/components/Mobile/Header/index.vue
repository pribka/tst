<template>
    <header class="header">
        <div class="container">
            <div class="header_inner">
                <div class="flex items-center">
                    <router-link
                        v-if="logo"
                        :to="{name: frontPage}"
                        class="logo header__item">
                        <img
                            :data-src="logo"
                            class="lazyload">
                    </router-link>
                </div>
                <div class="flex items-center">
                    <div class="actions_block">
                        <component 
                            v-if="aiName"
                            :is="aiButton"
                            class="action_btn" />
                        <component :is="cart" />
                        <component :is="notification" />
                        <transition name="slowfade" appear :duration="{ enter: 600, leave: 300 }">
                            <component :is="workPlan2" />
                        </transition>
                        <a-avatar
                            v-if="user"
                            @click="pushProfile"
                            avResize
                            shape="square"
                            :key="user.avatar ? user.avatar.path : false"
                            class="cursor-pointer header__item"
                            :size="35"
                            :src="user.avatar && user.avatar.path">
                            <i class="fi fi-rr-user" />
                        </a-avatar>
                    </div>
                </div>
            </div>
        </div>
    </header>
</template>

<script>
import mixins from './mixins'
import { mapState } from 'vuex'
export default {
    mixins: [
        mixins
    ],
    props: {
        config: {
            type: Object,
            default: () => {}
        },
        user: {
            type: Object,
            default: () => {}
        },
    },
    computed: {
        ...mapState({
            routers: state => state.navigation.routerList
        }),
        aiName() {
            return this.config?.AISettings?.name
        },
        logo() {
            if(this.config?.header_setting?.logo)
                return this.config.header_setting.logo
            else
                return null
        },
        logoMini() {
            if(this.config?.header_setting?.logo_mini)
                return this.config.header_setting.logo_mini
            else
                return this.logo
        },
        frontPage() {
            if(this.routers?.length) {
                const footerRouter = [...this.$store.state.navigation.routerList].filter(f => f.isShowMobile && f.isFooter)
                if(footerRouter.length) {
                    return footerRouter[0].name
                } else {
                    return this.routers.filter(f => f.isShowMobile)[0].name
                }
            } else
                return ''
        }
    },
    methods: {
        pushProfile() {
            if(this.$route.name !== 'profile')
                this.$router.push({ name: 'profile' })
        }
    },
}
</script>

<style scoped lang="scss">
.slowfade-enter-active,
.slowfade-leave-active {
  transition: opacity .4s ease, transform .4s ease;
}

.slowfade-enter,
.slowfade-leave-to {
  opacity: 0;
  transform: translateX(8px);
}
.logo{
    display: block;
    img{
        max-height: 49px;
    }
}
.header {
    --alpha: 1;
    -webkit-backdrop-filter: blur(calc(7px*(2 - var(--alpha))));
    backdrop-filter: blur(calc(7px * (2 - var(--alpha))));
    position: fixed;
    top: 0;
    left: 0;
    z-index: 600;
    display: flex;
    height: var(--headerHeight);
    min-height: var(--headerHeight);
    width: 100%;
    align-items: center;
    background-color: rgba(247, 249, 252, 0.8);
    -webkit-backface-visibility: hidden;
    backface-visibility: hidden;
    transform: translateZ(0)
}
.is-ios .header {
    position: sticky;
    top: 0;
    padding-top: env(safe-area-inset-top);
    will-change: transform
}
.contaier {
    height: 100%;
    max-width: 900px;
}
.header_inner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0px 10px;
    height: 100%;

}
.header__item + .header__item {
    margin-left: 0.8rem;
}
.icon {
    display: flex;
    justify-content: center;
    align-items: center;

    height: 35px;
    width: 35px;
    
    color: var(--text);

    border-radius: 50%;
    background-color: var(--iconBG);
}
.logo-img {
    max-width: 35px;
}

.fi {
    font-size: 1.2rem;
    vertical-align: middle;
}
.ant-avatar{
    background-color: #ffffff!important;
    color: var(--text)!important;
    border-radius: 8px;
    &::v-deep{
        img{
            border-radius: 8px;
        }
    }
}
.actions_block{
    display: flex;
    align-items: center;
    .action_btn{
        &:not(:last-child){
            margin-right: 15px;
        }
    }
    &::v-deep{
        .ant-btn{
            width: 35px;
            height: 35px;
            border-radius: 8px;
            background: #fff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
        }
    }
}
</style>