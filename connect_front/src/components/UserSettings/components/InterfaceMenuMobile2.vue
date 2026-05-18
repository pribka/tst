<template>
    <div class="menu_select">
        <div class="menu_select__label">
            Модули меню
        </div>
        <a-alert message="Перетаскивайте ярлыки модулей на необходимые позиции" banner :show-icon="false" />
        <a-alert v-if="routerEnabled <= 1" message="Минимум должен быть 1 модуль" class="mt-2" banner :show-icon="false" />
        <div class="menu_list">
            <draggable 
                v-model="routersList"
                :forceFallback="true"
                ghost-class="ghost"
                draggable=".a_i"
                :options="{delay: 300}"
                group="setting_menu">
                <div 
                    v-for="route in routersList" 
                    :key="route.name" 
                    class="menu_list__item a_i">
                    <div class="label" @click="changeRouteShow(!route.isShowMobile, route)">
                        <div class="icon">
                            <i class="fi" :class="route.icon" />
                        </div>
                        {{ route.title }}
                    </div>
                    <div style="text-align: right;">
                        <div class="mb-2">
                            <a-switch 
                                :checked="route.isShowMobile" 
                                checked-children="Скрыть" 
                                un-checked-children="Показать"
                                :disabled="(route.isShowMobile) ? routerEnabled > 1 ? false : true : false"
                                @change="changeRouteShow($event, route)" />
                        </div>
                        <div>
                            <a-switch 
                                :checked="route.isFooter" 
                                checked-children="Открепить" 
                                un-checked-children="Закрепить"
                                @change="changeRouteShowFooter($event, route)" />
                        </div>
                    </div>
                </div>
            </draggable>
        </div>
    </div>
</template>

<script>
import draggable from "vuedraggable"
import { mapState } from 'vuex'
import { langList, loadLanguageAsync, loadedLanguages } from '@/config/i18n-setup'
import { clearGlobalConfigCache } from '@/utils/configCache'
export default {
    components: {
        draggable
    },
    computed: {
        ...mapState({
            routers: state => state.navigation.routerList,
            user: state => state.user.user
        }),
        routersList: {
            get() {
                return this.routers
            },
            set(val) {
                this.$store.dispatch('navigation/changeRouterList', val)
            }
        },
        routerEnabled() {
            return [...this.routers].filter(f => f.isShowMobile).length
        },
        routerFooter() {
            return [...this.routers].filter(f => f.isFooter).length
        }
    },
    data() {
        return {
            langList,
            loadedLanguages,
            langLoading: false
        }
    },
    methods: {
        async changeRouteShow(value, route) {
            try {
                await this.$store.commit('navigation/CHANGE_ROUTE_SHOW', {value, route})
                await this.$store.dispatch('navigation/changeRouterList', this.routers)
                if(this.$route.name === route.name && this.routers.length) {
                    const rFilter = [...this.routers].filter(f => f.isShowMobile)
                    if(rFilter?.length) {
                        this.$router.push({ name: rFilter[0].name })
                    }
                }
            } catch(e) {
                console.log(e)
            }
        },
        async changeRouteShowFooter(value, route) {
            if(this.routerFooter >= 4 && value) {
                this.$message.warning('В подвале можно закрепить только 4 модуля')
            } else {
                try {
                    await this.$store.commit('navigation/CHANGE_ROUTE_FOOTER_SHOW', {value, route})
                    await this.$store.dispatch('navigation/changeRouterList', this.routers)
                } catch(e) {
                    console.log(e)
                }
            }
        },
        async changeLang(language) {
            try {
                this.langLoading = true
                const { data } = await this.$http.put('/users/update_profile/', {
                    language
                })
                if(data) {
                    await clearGlobalConfigCache().catch(() => null)
                    location.reload()
                }
                //localStorage.setItem('lang', lang)
                //location.reload()
            } catch(e) {
                console.log(e)
            } finally {
                this.langLoading = false
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.menu_list{
    &__item{
        display: flex;
        align-items: center;
        padding: 10px 0;
        justify-content: space-between;
        -webkit-touch-callout: none; /* iOS Safari */
        -webkit-user-select: none;   /* Chrome/Safari/Opera */
        -khtml-user-select: none;    /* Konqueror */
        -moz-user-select: none;      /* Firefox */
        -ms-user-select: none;       /* Internet Explorer/Edge */
        user-select: none;  
        &:not(:last-child){
            border-bottom: 1px solid var(--border2);
        }
        .label{
            font-size: 16px;
            cursor: pointer;
            font-weight: 300;
            display: flex;
            align-items: center;
            .icon{
                margin-right: 10px;
                animation-delay: -0.65; 
                animation-duration: .20s 
            }
        }
    }
}
.menu_select{
    &__label{
        margin-bottom: 10px;
        font-size: 16px;
    }
    &::v-deep{
        .ant-radio-group{
            .ant-radio-wrapper{
                border: 1px solid var(--border2);
                border-radius: var(--borderRadius);
                text-align: center;
                padding-left: 50px;
                padding-right: 50px;
                transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
                background: #ffffff;
                &:not(:last-child){
                    margin-right: 15px;
                }
                &:hover{
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
                }
                .ant-radio{
                    display: none;
                }
                &.ant-radio-wrapper-checked{
                    border-color: var(--blue);
                    background: #eff2f5;
                }
                img{
                    max-width: 110px;
                }
                .r_label{
                    margin-top: 10px;
                    color: var(--gray);
                    font-weight: 300;
                    color: #000000;
                }
            }
        }
    }
}
</style>
