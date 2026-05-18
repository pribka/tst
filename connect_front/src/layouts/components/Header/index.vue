<template>
    <header :class="advanceMenu && 'sidebar_hide'">
        <div class="left_block flex items-center">
            <!--<div class="head_logo ml-2">
                <router-link
                    v-if="logo"
                    :to="{name: frontPage}"
                    class="logo">
                    <img
                        :data-src="logo"
                        class="lazyload">
                </router-link>
            </div>-->
            <AddButton />
            <a-button 
                v-if="user && user.has_demo_data"
                class="ml-5 delete_demo" 
                type="danger" 
                flaticon 
                icon="fi-rr-trash"
                @click="deleteDemoData()">
                {{ $t('delete_demodata') }}
            </a-button>
        </div>
        <div class="actions_block">
            <HeaderGlobalTimer />
            <component 
                v-if="aiName"
                :is="aiButton" />
            <component :is="calendar" />
            <!--<component :is="returnWidget" />-->
            <!--<ShowSnowBtn />-->
            <component :is="support" />
            <LangBtn />
            <component :is="cart" />
            <component :is="notification" />
            <transition name="slowfade" appear :duration="{ enter: 600, leave: 300 }">
                <component :is="workPlan" />
            </transition>
            <UserNav />
        </div>
    </header>
</template>

<script>
import {mapState} from 'vuex'
import mixins from './mixins'
import 'lazysizes'
export default {
    mixins: [
        mixins
    ],
    components: {
        UserNav: () => import('./UserNav.vue'),
        Bell: () => import('@apps/Notifications/views/Bell'),
        AddButton: () => import('./AddButton.vue'),
        LangBtn: () => import('./LangBtn.vue'),
        HeaderGlobalTimer: () => import('./GlobalTimer.vue')
        //ShowSnowBtn: () => import('./ShowSnowBtn.vue')
    },
    computed: {
        ...mapState({
            advanceMenu: state => state.navigation.advanceMenu,
            config: state => state.config.config,
            asideType: state => state.asideType,
            routers: state => state.navigation.routerList,
            user: state => state.user.user
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
        frontPage() {
            if(this.routers?.length) {
                return this.routers[0].name
            } else
                return ''
        }
    }
}
</script>

<style lang="scss" scoped>
/* Плавное появление/исчезновение */
.delete_demo{
    background: #fdd5d5;
    color: #FF5C5C;
    border-color: #fdd5d5;
}
.slowfade-enter-active,
.slowfade-leave-active {
  transition: opacity .4s ease, transform .4s ease;
}

.slowfade-enter,
.slowfade-leave-to {
  opacity: 0;
  transform: translateX(8px);
}
header{
    background: #f7f9fc;
    height: var(--headerHeight);
    border-bottom: 1px solid var(--border2);
    padding: 5px 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    z-index: 10;
    min-height: 50px;
    max-height: 50px;
    margin: var(--wrapperMargin);
    .head_logo{
        img{
            max-width: 160px;
            max-height: 45px;
            opacity: 0;
            transition: opacity .1s ease-in-out;
            min-width: 70px;
            &.lazyloaded{
                opacity: 1;
            }
        }
    }
    .left_block{
        .menu_btn{
            width: 35px;
            height: 35px;
            border-radius: 50%;
            background: #eff2f5;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            margin-right: 15px;
        }
    }
    &.sidebar_hide{
        left: 75px;
    }
    .actions_block{
        display: flex;
        align-items: center;
        @media (max-width: 1440px) {
            ::v-deep .nav_calendar{
                margin-right: 15px;
            }
        }
        .action_btn{
            &:not(:last-child){
                margin-right: 10px;
            }
            &::v-deep{
                .ant-btn{
                    width: 30px;
                    height: 30px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 18px;
                }
            }
        }
    }
}
</style>
