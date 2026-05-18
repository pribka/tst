<template>
    <a-drawer
        ref="drawerTemplate"
        :visible="value"
        :zIndex="zIndex"
        :title="' '"
        :getContainer="getContainer"
        :placement="drawerPlacement"
        class="drawer_wrap"
        :width="drawerWidth"
        :maskClosable="maskClosable"
        :mask="mask"
        :push="drawerPush"
        :height="drawerHeight"
        :wrapClassName="wrapClassName"
        :destroyOnClose="destroyOnClose"
        :forceRender="forceRender"
        :afterVisibleChange="afterVisibleChange"
        @close="handlerClose">
        <div v-if="showHeader" class="drawer_header">
            <div class="w-full flex items-center" :class="titleTruncate && 'truncate'">
                <template v-if="loading">
                    <a-skeleton 
                        active 
                        :paragraph="{ rows: 0 }"
                        block />
                </template>
                <template v-else>
                    <template v-if="$slots.title">
                        <!-- Если нужно кастомизировать заголовок драйвера вместо title используем слот #title -->
                        <slot name="title" />
                    </template>
                    <div v-else class="title truncate">
                        {{ title }}
                    </div>
                </template>
            </div>
            <div class="flex items-center gap-2 ml-2">
                <template v-if="$slots.rightHeader">
                    <slot name="rightHeader" />
                </template>
                <a-button 
                    v-if="!isMobile && useShare && shareObject"
                    @click="shareHandler()"
                    type="ui"
                    shape="circle"
                    ghost
                    v-tippy
                    content="Поделиться"
                    icon="fi-rr-share" 
                    flaticon />
                <template v-if="!isMobile && link">
                    <!--<a-button 
                        v-if="usePrint"
                        @click="contentPrint()"
                        type="ui"
                        shape="circle"
                        ghost
                        v-tippy
                        content="Печать"
                        icon="fi-rr-print" 
                        flaticon />-->
                    <a-button 
                        v-if="useCopyLink"
                        @click="copyLink()"
                        type="ui"
                        shape="circle"
                        ghost
                        v-tippy
                        :content="$t('copy_link')"
                        icon="fi-rr-link-alt" 
                        flaticon />
                    <a-button 
                        v-if="useOpenLink"
                        @click="openLink()"
                        type="ui"
                        shape="circle"
                        ghost
                        v-tippy
                        :content="$t('open_new_window')"
                        icon="fi-rr-arrow-up-right-from-square" 
                        flaticon />
                </template>
                <a-button 
                    @click="handlerClose"
                    type="ui"
                    shape="circle"
                    ghost
                    icon="fi-rr-cross-small" 
                    flaticon />
            </div>

            <!-- <div class="flex items-center pl-2">
                <div v-if="$slots.header || $slots.actions || edit || openA || share || deleteA" class="mr-2 flex items-center">
                    Шапка драйвера (Правая часть)
                    <slot v-if="$slots.header" name="header" />
                    <Actions 
                        v-if="$slots.actions || edit || openA || share || deleteA" 
                        :edit="edit" 
                        :deleteA="deleteA"
                        :deleteContent="deleteContent"
                        :deleteHandler="deleteHandler"
                        :shareHandler="shareHandler"
                        :open="openA"
                        :openHandler="openHandler"
                        :share="share"
                        :editHandler="editHandler" 
                        :buttonType="actionsButtonType"
                        rootClass="ml-2">
                        <template #menu>
                            <slot name="actions" />
                        </template>
                    </Actions>
                </div>
                <a-button type="text" shape="circle" @click="handlerClose()">
                    <template #icon>
                        <i class="fi fi-rr-cross"></i>
                    </template>
                </a-button>
            </div> -->
        </div>
        <div 
            v-if="$slots.tabs || (useDrawerTabs && drawerTabsList.length)" 
            :class="!isMobile && 'menu_pd'"
            class="drawer_menu select-none">
            <!-- 
                useDrawerTabs - Активирует табы в драйвере
                drawerTabs - Передаем массив табов в драйвер
            -->
            <div v-if="loading" class="h-full flex items-center" style="padding-left: 15px;padding-right: 15px;">
                <a-skeleton 
                    active 
                    :paragraph="{ rows: 0 }"
                    block />
            </div>
            <slot name="tabs" v-else>
                <a-menu 
                    v-model="currentMenu" 
                    mode="horizontal" 
                    @click="menuClick">
                    <a-menu-item v-for="tab in drawerTabsList" :key="tab.key">
                        {{ tab.title }}
                    </a-menu-item>
                </a-menu>
            </slot>
        </div>
        <div 
            ref="bodyRef"
            class="drawer_body" 
            :style="bodyStyle"
            :class="[!disabledBodyPadding && 'padding', tabFill && 'body_fill', xHidden && 'overflow-x-hidden']">
            <div v-if="$slots.body_header" class="mb-4">
                <slot name="body_header" />
            </div>
            <template v-if="$slots.aside">
                <a-row :gutter="rowGutter" class="drawer_row">
                    <a-col 
                        :sm="24" 
                        class="drawer_col"
                        :lg="showTabAside ? contentColSize.lg : 24"
                        :xl="showTabAside ? contentColSize.xl : 24"
                        :xxl="showTabAside ? contentColSize.xxl : 24">
                        <template v-if="loading">
                            <a-skeleton 
                                active 
                                :paragraph="{rows: 8}"  />
                        </template>
                        <template v-else>
                            <!-- Содержимое драйвера -->
                            <template v-if="useDrawerTabs && drawerTabsList.length">
                                <template v-for="menu in drawerTabsList">
                                    <slot 
                                        v-if="currentMenuActive === menu.key"
                                        :name="`body_${menu.key}`" />
                                </template>
                            </template>
                            <slot v-else name="default" />
                        </template>
                    </a-col>
                    <a-col 
                        v-if="showTabAside"
                        :sm="24"
                        class="drawer_col"
                        :lg="asideColSize.lg"
                        :xl="asideColSize.xl"
                        :xxl="asideColSize.xxl">
                        <DrawerAside>
                            <template v-if="loading">
                                <a-skeleton 
                                    active 
                                    :paragraph="{rows: 8}"  />
                            </template>
                            <slot v-else name="aside" />
                        </DrawerAside>
                        <DrawerAside v-if="$slots.aside_bottom">
                            <template v-if="loading">
                                <a-skeleton 
                                    active 
                                    :paragraph="{rows: 8}"  />
                            </template>
                            <slot v-else name="aside_bottom" />
                        </DrawerAside>
                    </a-col>
                </a-row>
            </template>
            <template v-else>
                <template v-if="loading">
                    <a-skeleton 
                        active 
                        :paragraph="{rows: 6}"  />
                </template>
                <template v-else>
                    <!-- Содержимое драйвера -->
                    <template v-if="useDrawerTabs && drawerTabsList.length">
                        <template v-for="menu in drawerTabsList">
                            <slot 
                                v-if="currentMenuActive === menu.key"
                                :name="`body_${menu.key}`" />
                        </template>
                    </template>
                    <slot v-else name="default" />
                </template>
            </template>
        </div>
        <div 
            v-if="$slots.footer" 
            class="drawer_footer">
            <!-- Подвал драйвера -->
            <template v-if="loading">
                <a-skeleton 
                    active 
                    :paragraph="{ rows: 0 }"
                    block />
            </template>
            <slot v-else name="footer" />
        </div>
    </a-drawer>
</template>

<script>
// import { useStore } from 'vuex'
// import Actions from '@/components/Actions/index.vue'
// import { closeRouteDrawer, openRoute, useCurrentRoute } from '@/utils/routersUtils.js'
// import { useThemeStore } from '@/stores/theme.js'
// import { buttonType } from '@model/index.js'
import { v1 as uuidv1 } from 'uuid'
export default {
    components: {
        DrawerAside: () => import('@apps/UIModules/DrawerAside')
    },
    props: {
        value: { // v-model на visible
            type: Boolean,
            required: true
        },
        link: {
            type: Object,
            default: () => null
        },
        useCopyLink: {
            type: Boolean,
            default: false
        },
        useOpenLink: {
            type: Boolean,
            default: false
        },
        useShare: {
            type: Boolean,
            default: false
        },
        shareObject: {
            type: Object,
            default: () => null
        },
        usePrint: {
            type: Boolean,
            default: false
        },
        hardZIndex: {
            type: Number,
            default: null,
        },
        wrapClassName: {
            type: String,
            default: ''
        },
        titleTruncate: {
            type: Boolean,
            default: true
        },
        visibleChange: {
            type: Function,
            default: () => {}
        },
        title: { // Заголовок драйвера
            type: [String, Number],
            default: ''
        },
        placement: { // Положение драйвера
            type: String,
            default: ''
        },
        width: { // Ширина драйвера (Автоматический подстраиваеться если ширина меньше указанной)
            type: [Number, String],
            default: 400
        },
        loading: { // Передаем комманду для показа предзагрузчика в контентной части драйвера
            type: Boolean,
            default: false
        },
        disabledBodyPadding: { // Выключает падинги в контентной части драйвера
            type: Boolean,
            default: false
        },
        showHeader: {
            type: Boolean,
            default: true
        },
        bodyStyle: {
            type: String,
            default: ""
        },
        share: { // Показать кнопку поделиться в меню
            type: Boolean,
            default: false
        },
        edit: { // Показать кнопку редактирования в меню
            type: Boolean,
            default: false
        },
        deleteA: { // Показать кнопку удаления в меню
            type: Boolean,
            default: false
        },
        open: { // Показать кнопку открытия в меню
            type: Boolean,
            default: false
        },
        editHandler: { // функция для кнопки редактирования
            type: Function,
            default: () => {}
        },
        deleteHandler: { // функция для кнопки удаления
            type: Function,
            default: () => {}
        },
        openHandler: { // функция для кнопки открытия
            type: Function,
            default: () => {}
        },
        deleteContent: { // какой текст будет показан в модалке для удаления
            type: [String, Number],
            default: 'Вы действительно хотите удалить элемент?'
        },
        mask: { // Включить/Выключить маску драйвера
            type: Boolean,
            default: true
        },
        maskClosable: { // Сделать маску кликабельной для закрытия драйвера
            type: Boolean,
            default: true
        },
        forceRender: { // Рендерить драйвер всегда
            type: Boolean,
            default: true
        },
        destroyOnClose: { // удалить из DOM при закрытии
            type: Boolean,
            default: true
        },
        drawerTabs: { // Тут передаем массив табов по первому примеру https://antdv.com/components/menu, children так же работает для выпадающего меню
            type: Array,
            default: () => []
        },
        useDrawerTabs: { // Если хотим активировать табы передаем true
            type: Boolean,
            default: false
        },
        push: {
            type: [Number, Boolean],
            default: 180
        },
        rowGutter: {
            type: Number,
            default: 20
        },
        actionsButtonType: {
            type: String,
            default: 'drawer',
            validator(value, props) {
                return ['full', 'default', 'drawer'].includes(value)
            }
        },
        xHidden: {
            type: Boolean,
            default: false
        },
        contentColSize: {
            type: Object,
            default: () => ({
                lg: 16,
                xl: 16,
                xxl: 16
            })
        },
        asideColSize: {
            type: Object,
            default: () => ({
                lg: 8,
                xl: 8,
                xxl: 8
            })
        },
        height: {
            type: String,
            default: ""
        },
        getContainer: {
            type: Function,
            default: () => document.body
        },
    },
    data() {
        return {
            drawerTemplate: null,
            drawerUid: uuidv1(),
            currentMenu: [],
        }
    },
    watch: {
        drawerTabsList(tbList) {
            if(tbList.length && !this.currentMenu.length)
                this.currentMenu = [this.drawerTabsList[0].key]
        }
    },
    computed: {
        drawerHeight() {
            if(this.height)
                return this.height
            return this.isMobile ? '100%' : ''
        },
        drawerPlacement() {
            if(this.placement)
                return this.placement
            if(this.isMobile)
                return 'bottom'
            return 'right'
        },
        zIndex() {
            if (this.hardZIndex) { return this.hardZIndex }

            const openDrawers = this.$store.state.openDrawers
            const currentDrawer = openDrawers.find(drawer => drawer.uid === this.drawerUid)
            return currentDrawer?.zIndex || openDrawers?.[openDrawers.length-1]?.zIndex + 100 || 1000
        },
        windowWidth() { 
            return this.$store.state.windowWidth
        },
        currentMenuActive() { 
            return this.currentMenu?.[0] || null 
        },
        showTabAside() {
            const find = this.drawerTabsList.find(f => f.key === this.currentMenuActive)
            if(find)
                return find.showAside
            return true
        },
        tabFill() {
            const find = this.drawerTabsList.find(f => f.key === this.currentMenuActive)
            if(find)
                return find.tabFill
            return false
        },
        drawerWidth() {
            return this.windowWidth < this.width ? '100%' : this.width
        },
        drawerPush() {
            if(this.isMobile)
                return false
            return {
                distance: this.push
            }
        },
        isMobile() { 
            return this.$store.state.isMobile
        },
        drawerTabsList() {
            return this.drawerTabs.map(tab => {
                return {
                    ...tab,
                    showAside: typeof tab.showAside === 'boolean' ? tab.showAside : true,
                    tabFill: typeof tab.tabFill === 'boolean' ? tab.tabFill : false,
                }
            }) || []
        }
    },
    methods: {
        shareHandler() {
            const shareUrl = this.generateUrl()
            this.$store.commit("share/SET_SHARE_PARAMS", {
                ...this.shareObject,
                shareUrl
            })
        },
        generateUrl() {
            const params = new URLSearchParams()
            for (const [key, value] of Object.entries(this.link)) {
                params.append(key, value)
            }

            return `${window.location.origin}/?${params.toString()}`
        },
        openLink() {
            const link = this.generateUrl()
            window.open(link, '_blank')
        },
        copyLink() {
            const link = this.generateUrl()
            navigator.clipboard.writeText(link)
                .then(() => {
                    this.$message.success(this.$t('link_succes_copy'))
                })
                .catch(error => {
                    console.error(error)
                    this.$message.error(this.$t('copy_link_error'))
                })
        },
        getZIndex() {
            return this.zIndex
        },
        closeDrawer ()  {
            if(this.useDrawerTabs) {
                this.currentMenu = []
            }
        },
        
        menuClick ({key, keyPath}) {
            this.currentMenu = keyPath
            
            // Передаем события клика по табу драйвера с ключем активного таба
            this.$emit('tabChange', key)
        },
        
        afterVisibleChange (visible)  {
            if(visible) {
                this.$store.commit('PUSH_OPEN_DRAWERS', this.drawerUid)
            } else {
                this.closeDrawer()
                this.$store.commit('REMOVE_OPEN_DRAWERS', this.drawerUid)
            }

            this.$nextTick(() => {
                this.$emit('afterVisibleChange', visible)
            })
        },
        
        // Функция закрытия драйвера, в дочернем компоненте вызываеться через ref: drawerForm.handlerClose()
        handlerClose () {
            this.$emit('close')
            // this.$emit('input', false)
        },
        openDrawer () {
            this.$emit('input', true)
        }
    },
}
</script>

<style lang="scss" scoped>
.drawer_menu{
    position: relative;
    z-index: 10;
    border-bottom: 1px solid #e5e5e5;
    &.menu_pd{
        padding-left: 15px;
        padding-right: 15px;
        @media (min-width: 992px) {
            padding-left: 30px;
            padding-right: 30px;
        }
    }
    &.use_shadow{
        &:deep() {
            .ant-menu{
                box-shadow: 0 8px 15px rgba(0, 0, 0, 0.04);
            }
        }
        
    }
    &::v-deep{
        .page_switch{
            border-bottom: 0px;
            .ant-menu{
                height: 100%;
                &.ant-menu-horizontal{
                    line-height: 32px;
                    border-bottom: 0px;
                }
            }
            .ant-menu-submenu{
                .ant-menu-submenu-title{
                    padding: 0px;
                }
            }
            .ant-menu-item,
            .ant-menu-submenu{
                margin-right: 15px;
                .ant-badge-count{
                    min-width: 14px;
                    height: 14px;
                    line-height: 14px;
                    top: -3px;
                    right: -3px;
                    font-size: 10px;
                    .ant-scroll-number-only{
                        height: 14px;
                    }
                    .ant-scroll-number-only-unit{
                        height: 14px;
                    }
                }
            }
            .ant-menu-item{
                padding: 0px;
                min-height: 32px;
            }
            .ant-menu-item > div{
                min-height: 32px;
            }
        }
        .ant-tabs{
            .ant-tabs-tab{
                .ant-badge-count{
                    min-width: 16px;
                    height: 15px;
                    font-size: 10px;
                    line-height: 15px;
                    .ant-scroll-number-only{
                        height: 15px;
                    }
                    .ant-scroll-number-only-unit{
                        height: 15px;
                    }
                }
            }
        }
    }
}
</style>

<style lang="scss">
.drawer_wrap{
    &.ant-drawer{
        .ant-drawer-mask{
            background-color: rgba(42, 43, 46, 0.6);
        }
        .ant-drawer-header{
            display: none;
        }
        .ant-drawer-content-wrapper{
            box-shadow: initial;
            @media (min-width: 992px) {
                padding: 15px;
            }
        }
        .ant-drawer-content{
            overflow: hidden;
            -webkit-overflow-scrolling: touch;
            min-height: 0;
            @media (min-width: 992px) {
                border-radius: 16px;
            }
        }
        .ant-drawer-wrapper-body{
            overflow: hidden;
        }
        .ant-drawer-body{
            height: 100%;
            overflow: hidden;
            padding: 0px;
            display: flex;
            min-height: 0;
            flex-direction: column;
            .drawer_footer{
                display: flex;
                align-items: center;
                padding-left: 15px;
                padding-right: 15px;
                padding-bottom: 10px;
                padding-top: 10px;
                @media (min-width: 992px) {
                    padding-left: 30px;
                    padding-right: 30px;
                    padding-bottom: 10px;
                }
            }
            .drawer_header{
                display: flex;
                align-items: center;
                justify-content: space-between;
                flex-shrink: 0;
                height: 50px;
                padding: 8px 15px;
                @media (min-width: 992px) {
                    padding: 8px 30px;
                }
                // border-bottom: 1px solid #e8e8e8;
                .text-base,
                .drawer_title,
                .title{
                    font-size: 18px;
                    font-weight: 500;
                    color: #000;
                }
            }
            .drawer_body{
                position: relative;
                flex: 1 1 auto;
                flex-grow: 1;
                min-height: 0;
                max-height: 100%;
                overflow: auto;
                -webkit-overflow-scrolling: touch;
                touch-action: pan-y;
                overscroll-behavior: contain;
                transform: translateZ(0);
                will-change: scroll-position;
                @media (min-width: 768px) {
                    overflow-y: auto;
                    overflow-x: hidden;
                }
                &.body_fill{
                    overflow: hidden;
                }
                &.padding{
                    padding: 15px;
                    @media (min-width: 992px) {
                        padding: 20px 30px;
                    }
                }
                .drawer_col{
                    @media (max-width: 991.98px) {
                        &:not(:last-child){
                            margin-bottom: 15px;
                        }
                    }
                    @media (min-width: 992px) {
                        height: 100%;
                        position: initial;
                    }
                }
                .drawer_row{
                    @media (min-width: 992px) {
                        height: 100%;
                    }
                }
                .drawer_aside{
                    padding: 20px;
                    background: #F8F9FD;
                    border-radius: 12px;
                    color: #000;
                }
               .body_tab{
                    .ant-tabs-bar{
                        display: none;
                    }
                }
                .kanban-main{
                    .kanban-col{
                        background: #f7f9fc;
                        .kanban-card{
                            background: #fff;
                        }
                    }
                }
            }
        }
    }
}
.drawer_menu {
    .ant-tabs-bar {
        margin: 0;
        border: 0;
    }
}
</style>
