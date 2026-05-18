<template>
    <div class="menu_page" :class="{ manage_mode: isManageMode }">
        <div class="flex items-center mb-2 justify-between">
            <h1 class="page_title" style="margin-bottom: 0px;">
                {{ $t('menu') }}
            </h1>
            <a-button
                type="ui"
                ghost
                shape="circle"
                flaticon
                class="settings_btn"
                icon="fi-rr-settings"
                :class="{ active: isManageMode }"
                :aria-label="$t('setting')"
                @click="toggleManageMode" />
        </div>
        <div v-if="isManageMode" class="edit_hint">
            {{ $t('menu_footer_fixed') }} {{ maxFooterItems }}.
        </div>
        <div class="menu_wrap" :class="isManageMode && dragging && 'dragging'">
            <draggable
                v-if="isManageMode"
                ref="menuDraggable"
                v-model="editMenuRoutes"
                :forceFallback="true"
                ghost-class="ghost"
                tag="menu"
                class="drag_menu"
                draggable=".drag_item"
                :group="'mobile_menu_manage'"
                :options="{ delay: 180, delayOnTouchOnly: true, touchStartThreshold: 5 }"
                @start="dragging = true"
                @end="dragging = false"
                @change="onMenuChange">
                <li
                    v-for="link in editMenuRoutes"
                    :key="link.name"
                    class="drag_item edit_item"
                    :class="{ inactive_item: !link.isShowMobile }">
                    <div class="truncate flex items-center item_wrap">
                        <div class="item_main truncate flex items-center">
                            <div class="icon flex items-center mr-3">
                                <i class="fi" :class="link.icon" />
                            </div>
                            <div class="label truncate">
                                {{ link.title }}
                            </div>
                        </div>
                        <div class="item_switch" @click.stop>
                            <a-switch
                                :checked="link.isShowMobile"
                                :disabled="link.isShowMobile && routerEnabled <= 1"
                                @change="changeRouteShowMobile($event, link)" />
                        </div>
                    </div>
                </li>
            </draggable>
            <menu v-else class="drag_menu">
                <li
                    v-for="link in visibleMenuRoutes"
                    :key="link.name"
                    class="menu_item">
                    <router-link
                        :to="{ name: link.name }"
                        class="truncate flex items-center">
                        <div class="icon flex items-center mr-3">
                            <i class="fi" :class="link.icon" />
                        </div>
                        <div class="label truncate">
                            {{ link.title }}
                        </div>
                    </router-link>
                </li>
            </menu>
        </div>
        <div v-if="isManageMode" class="footer_edit_sh"></div>
        <div v-if="isManageMode" class="tab_bar footer_edit_zone" :class="dragging && 'dragging'">
            <draggable
                ref="footerDraggable"
                v-model="editFooterRoutes"
                :forceFallback="true"
                ghost-class="ghost"
                tag="ul"
                class="footer_edit_list"
                draggable=".drag_item"
                :group="'mobile_menu_manage'"
                :options="{ delay: 180, delayOnTouchOnly: true, touchStartThreshold: 5 }"
                @start="dragging = true"
                @end="dragging = false"
                @change="onFooterChange">
                <li
                    v-for="link in editFooterRoutes"
                    :key="link.name"
                    class="drag_item footer_item_preview">
                    <div class="icon">
                        <i class="fi" :class="link.icon" />
                    </div>
                    <div class="label truncate">
                        {{ link.title }}
                    </div>
                </li>
                <template #footer>
                    <li class="menu_item_static footer_item_preview">
                        <div class="icon">
                            <i class="fi fi-rr-apps" />
                        </div>
                        <div class="label truncate">
                            {{ $t('menu') }}
                        </div>
                    </li>
                </template>
            </draggable>
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
            return [...this.$store.state.navigation.routerList]
        },
        visibleMenuRoutes() {
            return this.routers
                .filter(route => !route.isFooter && route.isShowMobile)
                .sort((a, b) => this.getMobileOrder(a) - this.getMobileOrder(b))
        },
        routerEnabled() {
            if(this.isManageMode)
                return [...this.editFooterRoutes, ...this.editMenuRoutes].filter(route => route.isShowMobile).length
            return this.routers.filter(route => route.isShowMobile).length
        }
    },
    data() {
        return {
            dragging: false,
            isManageMode: false,
            maxFooterItems: 5,
            editMenuRoutes: [],
            editFooterRoutes: []
        }
    },
    created() {
        this.syncLocalRoutes()
    },
    beforeDestroy() {
        this.$store.commit('SHOW_FOOTER', true)
    },
    beforeRouteLeave(to, from, next) {
        this.$store.commit('SHOW_FOOTER', true)
        next()
    },
    watch: {
        routers: {
            deep: true,
            handler() {
                if(!this.dragging)
                    this.syncLocalRoutes()
            }
        }
    },
    methods: {
        getDescOrder(route) {
            return typeof route?.descOrder === 'number' ? route.descOrder : 0
        },
        getMobileOrder(route) {
            return typeof route?.mobileOrder === 'number' ? route.mobileOrder : 0
        },
        syncLocalRoutes() {
            const ordered = [...this.routers]
                .sort((a, b) => this.getMobileOrder(a) - this.getMobileOrder(b))
                .map(route => ({
                    ...route,
                    isFooter: route.isFooter && route.isShowMobile
                }))

            this.editFooterRoutes = ordered
                .filter(route => route.isFooter && route.isShowMobile)
                .sort((a, b) => this.getMobileOrder(a) - this.getMobileOrder(b))

            const footerNames = new Set(this.editFooterRoutes.map(route => route.name))
            this.editMenuRoutes = ordered.filter(route => !footerNames.has(route.name))
        },
        toggleManageMode() {
            this.isManageMode = !this.isManageMode
            this.$store.commit('SHOW_FOOTER', !this.isManageMode)
            if(this.isManageMode)
                this.syncLocalRoutes()
        },
        onMenuChange(event) {
            if(event?.added?.element) {
                event.added.element.isFooter = false
            }
            this.persistRoutes()
        },
        onFooterChange(event) {
            if(event?.added?.element && this.editFooterRoutes.length > this.maxFooterItems) {
                this.$message.warning(`В подвал можно добавить только ${this.maxFooterItems} модулей`)
                this.syncLocalRoutes()
                return
            }
            if(event?.added?.element) {
                event.added.element.isFooter = true
                event.added.element.isShowMobile = true
            }
            if(event?.removed?.element) {
                event.removed.element.isFooter = false
            }
            this.persistRoutes()
        },
        async changeRouteShowMobile(value, route) {
            if(route.isShowMobile === value)
                return
            if(route.isShowMobile && !value && this.routerEnabled <= 1)
                return

            route.isShowMobile = value
            if(!value) {
                route.isFooter = false
                this.editFooterRoutes = this.editFooterRoutes.filter(item => item.name !== route.name)
            }

            await this.persistRoutes()

            if(this.$route.name === route.name && !value) {
                const firstVisible = [...this.editFooterRoutes, ...this.editMenuRoutes].find(item => item.isShowMobile)
                if(firstVisible)
                    this.$router.push({ name: firstVisible.name })
            }
        },
        async persistRoutes() {
            const footerRoutes = this.editFooterRoutes.map(route => ({
                ...route,
                isFooter: true,
                isShowMobile: true
            }))
            const menuRoutes = this.editMenuRoutes.map(route => ({
                ...route,
                isFooter: false
            }))
            let menuOrder = 1
            let footerOrder = 1
            const nextMobileStateByName = [...menuRoutes, ...footerRoutes].reduce((acc, route) => {
                if(route.isFooter) {
                    acc[route.name] = {
                        isFooter: true,
                        isShowMobile: true,
                        mobileOrder: footerOrder
                    }
                    footerOrder++
                    return acc
                }

                acc[route.name] = {
                    isFooter: false,
                    isShowMobile: route.isShowMobile,
                    mobileOrder: menuOrder
                }
                menuOrder++
                return acc
            }, {})

            // Keep desktop order stable: update only mobile-related flags in-place.
            const nextRoutes = this.routers.map(route => {
                const mobileState = nextMobileStateByName[route.name]
                if(!mobileState)
                    return route
                return {
                    ...route,
                    ...mobileState
                }
            })

            await this.$store.dispatch('navigation/changeRouterList', nextRoutes)
        }
    }
}
</script>

<style lang="scss" scoped>
.menu_page{
    padding: 15px;
    .edit_hint{
        margin-bottom: 12px;
        color: #7d93a9;
        font-size: 13px;
    }
    .settings_btn{
        &.active{
            color: var(--blue);
        }
    }
    .menu_wrap{
        background: #fff;
        border-radius: var(--borderRadius);
        margin-bottom: 12px;
        .drag_menu{
            padding: 0px;
            margin: 0px;
            .menu_item{
                list-style: none;
            }
            li{
                list-style: none;
                -webkit-touch-callout: none; /* iOS Safari */
                -webkit-user-select: none;   /* Chrome/Safari/Opera */
                -khtml-user-select: none;    /* Konqueror */
                -moz-user-select: none;      /* Firefox */
                -ms-user-select: none;       /* Internet Explorer/Edge */
                user-select: none;  
                &:not(:last-child){
                    border-bottom: 1px solid var(--borderColor);
                }
                .label{
                    font-size: 20px;
                    font-weight: 300;
                }
                .icon{
                    font-size: 22px;
                    animation-delay: -0.65; 
                    animation-duration: .20s 
                }
                a{
                    color: #354052;
                    padding: 15px;
                    font-weight: 300;
                }
            }
            .edit_item{
                .item_wrap{
                    padding: 15px;
                    justify-content: space-between;
                    color: #354052;
                    font-weight: 300;
                    .item_main{
                        min-width: 0;
                    }
                    .item_switch{
                        margin-left: 10px;
                        flex-shrink: 0;
                    }
                }
                &.inactive_item{
                    .item_main{
                        opacity: 0.45;
                    }
                }
            }
            .menu_item_static{
                color: #b0bac7;
                padding: 15px;
            }
        }
        &.dragging{
            li{
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
    .footer_edit_zone{
        --safe-area-inset-bottom: env(safe-area-inset-bottom);
        position: fixed;
        left: 15px;
        right: 15px;
        bottom: calc(10px + var(--safe-area-inset-bottom));
        z-index: 900;
        border-radius: 50px;
        padding: 5px 8px;
        box-shadow: 0 0 0 1px #e6e6e8;
        background: rgba(255,255,255,0.8);
        -webkit-backdrop-filter: blur(7px);
        backdrop-filter: blur(7px);
        .footer_edit_list{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            width: 100%;
            min-height: var(--footerHeight);
            padding: 0;
            margin: 0;
            .footer_item_preview{
                list-style: none;
                width: 20%;
                text-align: center;
                color: var(--text);
                padding: 5px 0;
                .icon{
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    i{
                        font-size: 1.3rem;
                        line-height: 1;
                    }
                }
                .label{
                    font-size: 11px;
                    width: 100%;
                    margin-top: 2px;
                    font-weight: 300;
                    color: var(--footerLink);
                }
            }
            .menu_item_static{
                color: var(--blue);
                width: 20%;
            }
        }
    }
    .footer_edit_sh{
        --safe-area-inset-bottom: env(safe-area-inset-bottom);
        position: fixed;
        bottom: calc(0px + var(--safe-area-inset-bottom));
        left: 0;
        width: 100%;
        z-index: 850;
        min-height: 40px;
        background: linear-gradient(to bottom,  rgba(247,249,252,0) 0%,rgba(247,249,252,1) 100%,rgba(247,249,252,1) 50%);
    }
    &.manage_mode{
        padding-bottom: 120px;
    }
}
</style>
