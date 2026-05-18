<template>
    <div class="mobile_interface">
        <div class="label">
            {{ $t('mobile_modules') }}
        </div>
        <a-alert :message="$t('drag_icons_alert')" style="margin-bottom: 15px;" banner :show-icon="false" />
        <div class="flex">
            <div class="mobile_app">
                <div class="mobile_app__header">
                    <a-skeleton :paragraph="{ rows: 0 }" />
                </div>
                <div class="mobile_app__content">
                    <a-skeleton avatar class="mb-6" :paragraph="{ rows: 4 }" />
                    <a-skeleton avatar :paragraph="{ rows: 4 }" />
                </div>
                <div class="mobile_app__footer">
                    <draggable 
                        v-model="footerRoute"
                        :forceFallback="true"
                        ghost-class="ghost"
                        draggable=".f_a_i"
                        class="f_menu_list"
                        group="mobile_menu"
                        @start="dragging = true"
                        @end="dragging = false"
                        @change="changeFooter">
                        <div
                            v-for="route in footerRoute"
                            :key="route.name" 
                            class="f_menu_list__item f_a_i cursor-move"
                            @click="deleteFooterMenu(route)">
                            <div class="wrp">
                                <div class="f_icon">
                                    <i class="fi" :class="route.icon" />
                                </div>
                                <div class="f_item_label">
                                    {{ route.title }}
                                </div>
                            </div>
                        </div>
                        <template slot="footer">
                            <div class="f_menu_list__item">
                                <div class="wrp">
                                    <div class="f_icon">
                                        <i class="fi fi-rr-apps" />
                                    </div>
                                    <div class="f_item_label">
                                        {{ $t('menu') }}
                                    </div>
                                </div>
                            </div>
                        </template>
                    </draggable>
                </div>
            </div>
            <div class="pl-8">
                <div class="mobule_list">
                    <div class="mobule_list__label">
                        {{ $t('active_modules') }}
                    </div>
                    <draggable 
                        v-model="mainMenu"
                        :forceFallback="true"
                        ghost-class="ghost"
                        draggable=".a_i"
                        class="menu_list"
                        group="mobile_menu"
                        @start="dragging = true"
                        @end="dragging = false">
                        <div 
                            v-for="route in mainMenu"
                            class="menu_list__item a_i" 
                            :key="route.name">
                            <div class="icon">
                                <i class="fi" :class="route.icon" />
                            </div>
                            <div class="item_label">
                                {{ route.title }}
                            </div>
                        </div>
                    </draggable>
                </div>
                <div class="mobule_list">
                    <div class="mobule_list__label">
                        {{ $t('deactivated_modules') }}
                    </div>
                    <draggable 
                        v-model="deactivatedMenu"
                        :forceFallback="true"
                        ghost-class="ghost"
                        draggable=".a_i"
                        class="menu_list"
                        group="mobile_menu"
                        @start="dragging = true"
                        @end="dragging = false"
                        @change="changeDeactivate">
                        <div 
                            v-for="route in deactivatedMenu"
                            class="menu_list__item a_i" 
                            :key="route.name">
                            <div class="icon">
                                <i class="fi" :class="route.icon" />
                            </div>
                            <div class="item_label">
                                {{ route.title }}
                            </div>
                        </div>
                    </draggable>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import draggable from "vuedraggable"
export default {
    components: {
        draggable
    },
    computed: {
        routers() {
            return [...this.$store.state.navigation.routerMobile]
        },
        footerRoute: {
            get() {
                return this.routers.filter(f => f.isFooter && f.isShowMobile)
            },
            set(value) {
                if(value.length === this.footerRoute.length) {
                    this.$store.commit('navigation/CHANGE_MOBILE_ROUTER_LIST', [...value, ...this.mainMenu, ...this.deactivatedMenu])
                    this.$store.dispatch('navigation/changeMobileRouteList')
                }
            }
        },
        mainMenu: {
            get() {
                return this.routers.filter(f => !f.isFooter && f.isShowMobile)
            },
            set(value) {
                if(value.length === this.mainMenu.length) {
                    this.$store.commit('navigation/CHANGE_MOBILE_ROUTER_LIST', [...this.footerRoute, ...value, ...this.deactivatedMenu])
                    this.$store.dispatch('navigation/changeMobileRouteList')
                }
            }
        },
        deactivatedMenu: {
            get() {
                return this.routers.filter(f => !f.isShowMobile)
            },
            set(value) {
                if(value.length === this.deactivatedMenu.length) {
                    this.$store.commit('navigation/CHANGE_MOBILE_ROUTER_LIST', [...this.footerRoute, ...this.mainMenu, ...value])
                    this.$store.dispatch('navigation/changeMobileRouteList')
                }
            }
        }
    },
    data() {
        return {
            dragging: false
        }
    },
    methods: {
        deleteFooterMenu(route) {
            this.$store.commit('navigation/DELETE_ROUTE_MOBILE', route)
            this.$store.dispatch('navigation/changeMobileRouteList')
        },
        changeFooter(e) {
            this.$store.commit('navigation/CHANGE_ROUTE_MOBILE_FOOTER', e)
            this.$store.dispatch('navigation/changeMobileRouteList')
        },
        changeDeactivate(e) {
            this.$store.commit('navigation/CHANGE_ROUTE_MOBILE_DEACTIVATE', e)
            this.$store.dispatch('navigation/changeMobileRouteList')
        }
    }
}
</script>

<style lang="scss" scoped>
.mobule_list{
    &__label{
        margin-bottom: 10px;
        font-weight: 600;
    }
    &:not(:last-child){
        border-bottom: 1px solid var(--border2);
        padding-bottom: 15px;
        margin-bottom: 15px;
    }
    .menu_list{
        min-height: 60px;
    }
}
.mobile_interface{
    .label{
        margin-bottom: 10px;
        font-size: 16px;
    }
    .menu_list{
        display: flex;
        flex-wrap: wrap;
        align-content: flex-start;
        gap: 15px;
        flex-direction: row;
        &__item{
            cursor: move;
            text-align: center;
            width: 75px;
            -webkit-touch-callout: none; /* iOS Safari */
            -webkit-user-select: none;   /* Chrome/Safari/Opera */
            -khtml-user-select: none;    /* Konqueror */
            -moz-user-select: none;      /* Firefox */
            -ms-user-select: none;       /* Internet Explorer/Edge */
            user-select: none;  
            .icon{
                background: #eff2f5;
                border-radius: var(--borderRadius);
                width: 70px;
                height: 70px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 20px;
                i{
                    color: #7d93a9;
                }
            }
        }
        .item_label{
            font-size: 13px;
            text-align: center;
            max-width: 68px;
            display: -webkit-box;
            overflow: hidden;
            -webkit-box-orient: vertical;
            -webkit-line-clamp: 2;
            word-break: break-word;
            line-height: 16px;
            margin-top: 5px;
        }
    }
}
.mobile_app{
    border: 5px solid #e6e9ec;
    height: 560px;
    min-width: 370px;
    border-radius: 20px;
    display: flex;
    flex-direction: column;
    &__header{
        background: #ffffff;
        height: 50px;
        width: 100%;
        border-radius: 15px 15px 0 0;
        overflow: hidden;
        padding-left: 12px;
        padding-right: 12px;
        &::v-deep{
            .ant-skeleton-content{
                .ant-skeleton-title{
                    border-radius: var(--borderRadius);
                    background: #e0e0e0;
                }
            }
        }
    }
    &__content{
        background: #eff2f5;
        flex-grow: 1;
        width: 100%;
        overflow: hidden;
        padding-top: 30px;
        padding-left: 12px;
        padding-right: 12px;
        &::v-deep{
            .ant-skeleton-header{
                .ant-skeleton-avatar{
                    background: #e0e0e0;
                }
            }
            .ant-skeleton-content{
                .ant-skeleton-title{
                    border-radius: var(--borderRadius);
                    background: #e0e0e0;
                }
                .ant-skeleton-paragraph{
                    li{
                        border-radius: var(--borderRadius);
                        background: #e0e0e0;
                    }
                }
            }
        }
    }
    &__footer{
        background: #ffffff;
        height: 60px;
        width: 100%;
        border-radius: 0 0 20px 20px;
        padding: 0;
        margin: 0;
        display: flex;
        align-items: center;
        width: 100%;
        .f_menu_list{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            width: 100%;
            padding: 0;
            margin: 0;
            &__item{
                list-style: none;
                position: relative;
                width: 100%;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                .wrp{
                    color: #354052;
                    display: flex;
                    justify-content: center;
                    flex-wrap: wrap;
                    padding-bottom: 5px;
                    padding-top: 5px;
                    position: relative;
                    .f_icon{
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        position: relative;
                        i{
                            font-size: 1.3rem;
                            line-height: 1;
                        }
                    }
                    .f_item_label{
                        font-size: 11px;
                        width: 100%;
                        margin-top: 2px;
                        font-weight: 300;
                        text-align: center;
                    }
                }
            }
        }
    }
}
</style>