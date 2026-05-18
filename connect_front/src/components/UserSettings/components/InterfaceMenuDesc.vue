<template>
    <div class="menu_select">
        <div class="menu_select__label">
            {{ $t('menu_modules') }}
        </div>
        <a-alert :message="$t('menu_sort_alert')" banner :show-icon="false" />
        <a-alert 
            v-if="routerEnabled <= 1" 
            :message="$t('min_one_module')" 
            class="mt-2" 
            banner 
            :show-icon="false"/>
        <div class="menu_list">
            <draggable 
                v-model="routersList"
                :forceFallback="true"
                ghost-class="ghost"
                draggable=".a_i"
                group="setting_menu"
                handle=".handle"
                @start="dragging = true"
                @end="dragging = false">
                <div 
                    v-for="route in routersList" 
                    :key="route.name" 
                    class="menu_list__item a_i">
                    <div class="label" @click="changeRouteShow(!route.isShow, route)">
                        <div class="icon">
                            <i class="fi" :class="route.icon" />
                        </div>
                        {{ route.title }}
                    </div>
                    <div>
                        <a-button 
                            type="ui" 
                            ghost 
                            shape="circle"
                            class="handle cursor-move mr-3" 
                            flaticon 
                            icon="fi-rr-arrows-alt" 
                            :aria-label="$t('move')"/>
                        <a-switch 
                            :checked="route.isShow" 
                            :disabled="(route.isShow) ? routerEnabled > 1 ? false : true : false"
                            @change="changeRouteShow($event, route)"
                            :aria-label="route.isShow ? $t('visible') : $t('hidden')"/>
                    </div>
                </div>
            </draggable>
        </div>
    </div>
</template>

<script>
import draggable from "vuedraggable"
import { mapState } from 'vuex'
export default {
    components: {
        draggable
    },
    computed: {
        ...mapState({
            routers: state => state.navigation.routerList
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
            return [...this.routers].filter(f => f.isShow).length
        }
    },
    data() {
        return {
            dragging: false,
        }
    },
    methods: {
        async changeRouteShow(value, route) {
            try {
                await this.$store.commit('navigation/CHANGE_ROUTE_SHOW', {value, route})
                await this.$store.dispatch('navigation/changeRouterList', this.routers)
                if(this.$route.name === route.name && this.routers.length) {
                    const rFilter = [...this.routers].filter(f => f.isShow)
                    if(rFilter?.length) {
                        this.$router.push({ name: rFilter[0].name })
                    }
                }
            } catch(e) {
                console.log(e)
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
        padding: 15px 0;
        justify-content: space-between;
        &:not(:last-child){
            border-bottom: 1px solid var(--border2);
        }
        .label{
            font-size: 16px;
            cursor: pointer;
            font-weight: 300;
            -webkit-touch-callout: none; /* iOS Safari */
            -webkit-user-select: none;   /* Chrome/Safari/Opera */
            -khtml-user-select: none;    /* Konqueror */
            -moz-user-select: none;      /* Firefox */
            -ms-user-select: none;       /* Internet Explorer/Edge */
            user-select: none;  
            display: flex;
            align-items: center;
            .icon{
                margin-right: 10px;
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