<template>
    <div class="a_m" :class="{ manage_mode: isMenuManageMode, is_tablet: isTablet }">
        <div class="l_b flex items-center">
            <a-button 
                type="link" 
                flaticon 
                class="mr-2 sidebar_menu"
                icon="fi-rr-menu-burger"
                @click="$store.commit('TOGGLE_MINI_MENU')" />
            <router-link
                v-if="logo"
                :to="{name: frontPage}"
                class="logo">
                <img
                    :data-src="logo"
                    class="lazyload">
            </router-link>
            <a-button
                type="link"
                flaticon
                size="small"
                v-tippy
                content="Настройка пунктов меню"
                class="settings_btn settings_btn_animate"
                icon="fi-rr-settings"
                :aria-label="$t('setting')"
                @click="toggleManageMode" />
        </div>
        <div class="menu_list" :class="[!isTop && 'top_a', !isBottom && 'bottom_a', dragging && 'dragging']">
            <vueScroll :ops="ops" @handle-scroll="onScroll">
                <draggable
                    v-if="isMenuManageMode"
                    v-model="routersList"
                    :forceFallback="false"
                    ghost-class="ghost"
                    draggable=".menu_manage_item"
                    group="aside_menu"
                    class="menu_list_items"
                    @start="dragging = true"
                    @end="dragging = false">
                    <div v-for="item in routersList" :key="item.name" class="menu_manage_item">
                        <MenuItem
                            :item="item"
                            :disableNavigation="true"
                            class="cursor-move"
                            :skipHoverMeta="true" />
                        <div class="menu_switch" @click.stop>
                            <a-switch
                                :checked="item.isShow"
                                size="small"
                                :disabled="item.isShow && routerEnabled <= 1"
                                @change="changeRouteShow($event, item)" />
                        </div>
                    </div>
                </draggable>
                <div v-else class="menu_list_items">
                    <div v-for="item in routersList" :key="item.name" class="menu_manage_item">
                        <MenuItem :item="item" />
                    </div>
                </div>
            </vueScroll>
        </div>
        <div class="f_b">
            <div v-if="user && user.support_chat" class="a_m__b--i a_i">
                <router-link :to="{ name: 'chat', query: { chat_id: user.support_chat } }" class="relative i_w">
                    <div class="i_w__c">
                        <div class="icon">
                            <i class="fi fi-rr-headset" />
                        </div>
                        <div class="name">{{ $t('support_label') }}</div>
                    </div>
                </router-link>
            </div>
            <div v-if="config && config?.header_setting && config.header_setting.support" class="relative i_w">
                <div class="i_w__c" @click="openNewsFeed()">
                    <div class="icon">
                        <i class="fi fi-rr-megaphone" />
                    </div>
                    <div class="name">
                        {{ $t('support.newsFeed') }}
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import mixins from '../mixins.js'
import { mapState } from 'vuex'
export default {
    components: {
        MenuItem: () => import('./MenuItem.vue'),
        vueScroll: () => import('vuescroll')
    },
    mixins: [mixins],
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        routersList: {
            get() {
                const list = [...this.routers].sort((a, b) => {
                    const aOrder = typeof a.descOrder === 'number' ? a.descOrder : 0
                    const bOrder = typeof b.descOrder === 'number' ? b.descOrder : 0
                    return aOrder - bOrder
                })
                if(this.isMenuManageMode)
                    return list
                return list.filter(f => f.isShow)
            },
            set(val) {
                const nextVisibleRoutes = val.map((route, index) => ({
                    ...route,
                    descOrder: index
                }))
                if(this.isMenuManageMode) {
                    this.$store.dispatch('navigation/changeRouterList', nextVisibleRoutes)
                    return
                }

                const hiddenRoutes = this.routers
                    .filter(route => !route.isShow)
                    .sort((a, b) => {
                        const aOrder = typeof a.descOrder === 'number' ? a.descOrder : 0
                        const bOrder = typeof b.descOrder === 'number' ? b.descOrder : 0
                        return aOrder - bOrder
                    })
                    .map((route, index) => ({
                        ...route,
                        descOrder: nextVisibleRoutes.length + index
                    }))

                this.$store.dispatch('navigation/changeRouterList', [...nextVisibleRoutes, ...hiddenRoutes])
            }
        },
        routerEnabled() {
            return this.routers.filter(f => f.isShow).length
        },
        logo() {
            if(this.config?.header_setting?.logo)
                return this.config.header_setting.logo
            else
                return null
        }
    },
    data() {
        return {
            isMenuManageMode: false
        }
    },
    methods: {
        toggleManageMode() {
            this.isMenuManageMode = !this.isMenuManageMode
        },
        async changeRouteShow(value, route) {
            try {
                await this.$store.commit('navigation/CHANGE_ROUTE_SHOW', {value, route})
                await this.$store.dispatch('navigation/changeRouterList', this.routers)

                if(this.$route.name === route.name && !value) {
                    const firstVisibleRoute = this.routers.find(f => f.isShow)
                    if(firstVisibleRoute)
                        this.$router.push({ name: firstVisibleRoute.name })
                }
            } catch(e) {
                console.log(e)
            }
        }
    }
}
</script>

<style lang="scss" scoped>
@mixin itemList {
    .icon{
        font-size: 15px;
        margin-bottom: 2px;
        display: flex;
        align-items: center;
        justify-content: center;
        .fi{
            margin-right: 8px;
            width: 20px;
            height: 20px;
            line-height: 20px;
            font-size: 14px;
        }
    }
    .name{
        word-wrap: break-word;
        font-weight: 400;
        text-align: left;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        font-size: 0.835rem;
    }
    .i_w{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 2px 12px 2px 12px;
        cursor: pointer;
        color: #fff;
        &__c{
            display: flex;
            align-items: center;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            width: 100%;
            padding: 8px 14px;
            transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
            border-radius: var(--borderRadius);
            &:hover{
                background: rgba(223, 237, 255, 0.1);
            }
        }
        &__r{
            padding-left: 8px;
        }
    }
}
.menu_list_items{
    padding-bottom: 10px;
}
.sidebar_menu{
    color: #fff;
}
.settings_btn{
    margin-left: auto;
    color: #fff;
    opacity: 0;
    pointer-events: none;
    transition: opacity .2s ease;
    &:hover{
        opacity: 1!important;
    }
}
.menu_manage_item{
    position: relative;
}
.menu_switch{
    position: absolute;
    right: 20px;
    top: 50%;
    transform: translateY(-50%);
    z-index: 2;
}
.menu_list{
    flex-grow: 1;
    overflow: hidden;
    position: relative;
    &.dragging{
        &::v-deep{
            .menu_item{
                .icon{
                    animation-delay: -0.65s;
                    animation-duration: .20s;
                }
                &:nth-child(2n) {
                    .icon{
                        animation-name: JiggleEffect;
                        animation-iteration-count: infinite;
                        transform-origin: 50% 10%;
                        -webkit-transition: all .2s ease-in-out;
                    }
                }
                &:nth-child(2n-1) {
                    .icon{
                        animation-name: JiggleEffect2;
                        animation-iteration-count: infinite;
                        animation-direction: alternate;
                        transform-origin: 30% 5%;
                    }
                }
            }
        }
    }
    &.bottom_a{
        &::after{
            content: "";
            position: absolute;
            bottom: 0;
            left: 0;
            z-index: 10;
            width: 100%;
            height: 40px;
            background: linear-gradient(to bottom,  rgba(62,62,79,0) 0%,rgba(62,62,79,1) 100%); 
            pointer-events: none;
        }
    }
    &.top_a{
        &::before{
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            z-index: 10;
            width: 100%;
            height: 40px;
            background: linear-gradient(to bottom,  rgba(62,62,79,1) 0%,rgba(62,62,79,0) 99%,rgba(62,62,79,0) 100%);
            pointer-events: none;
        }
    }
    &::v-deep{
        .menu_item{
            &__wrapper{
                padding: 10px 14px;
            }
        }
        .menu_group_item{
            .menu_item{
                &__wrapper{
                    padding: 9px 10px;
                }
                &:hover,
                &.router-link-active{
                    .menu_item__wrapper{
                        background: #e6efe3;
                    }
                }
            }
        }
    }
}
.f_b{
    padding: 15px 0;
    .i_w{
        cursor: pointer;
    }
    &::v-deep{
        @include itemList;
    }
}
.l_b{
    padding: 10px 16px 10px 16px;
    min-height: 56px;
}
.a_m{
    background: #3e3e4f;
    width: 250px;
    position: absolute;
    top: 0;
    height: 100%;
    z-index: 50;
    left: 0;
    display: flex;
    flex-direction: column;
    transition: width .2s ease;
    &:hover{
        .settings_btn{
            opacity: 0.6;
            pointer-events: auto;
        }
    }
    &.manage_mode{
        width: 300px;
        .settings_btn{
            opacity: 1;
            pointer-events: auto;
        }
    }
    &.is_tablet{
        .settings_btn{
            opacity: 0.6;
            pointer-events: auto;
        }
    }
    &__b{
        flex-grow: 1;
        overflow: hidden;
        -webkit-overflow-scrolling: touch;
        -ms-overflow-style: none;
        scrollbar-width: none;
        &::-webkit-scrollbar{
            display: none;
        }
        &::-webkit-scrollbar-thumb{
            display: none;
        }
        &::v-deep{
            .__rail-is-vertical{
                background: transparent!important;
                .__bar-is-vertical{
                    border: 0px!important;
                }
            }
        }
    }
}
</style>
