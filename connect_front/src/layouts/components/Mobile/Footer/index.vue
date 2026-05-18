<template>
    <div>
        <div class="tab_bar">
            <nav class="footer_nav">
                <div class="container m_wrap">
                    <div class="row">
                        <div class="col-12">
                            <ul>
                                <MenuItem 
                                    v-for="link in routersList"
                                    :key="link.name"
                                    :link=link />
                                <li class="truncate footer_item">
                                    <router-link 
                                        class="link"
                                        :to="{name: 'menu'}">
                                        <div class="icon">
                                            <i class="fi fi-rr-apps"></i>
                                        </div>
                                        <div class="label truncate">
                                            {{ $t('menu') }}
                                        </div>
                                    </router-link>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </nav>
        </div>
        <div class="footer_sh"></div>
        <footer class="clearfix footer"></footer>
    </div>
</template>

<script>
export default {
    components: {
        MenuItem: () => import('./MenuItem.vue')
    },
    computed: {
        routersList() {
            return [...this.$store.state.navigation.routerList]
                .filter(f => f.isShowMobile && f.isFooter)
                .sort((a, b) => {
                    const aOrder = typeof a.mobileOrder === 'number' ? a.mobileOrder : 0
                    const bOrder = typeof b.mobileOrder === 'number' ? b.mobileOrder : 0
                    return aOrder - bOrder
                })
        }
    }
}
</script>


<style scoped lang="scss">
.footer_sh{
    --safe-area-inset-bottom: env(safe-area-inset-bottom);
    position: fixed;
    bottom: calc(0px + var(--safe-area-inset-bottom));
    left: 0;
    width: 100%;
    z-index: 4;
    min-height: 40px;
    background: linear-gradient(to bottom,  rgba(247,249,252,0) 0%,rgba(247,249,252,1) 100%,rgba(247,249,252,1) 50%);
}
.footer{
    --safe-area-inset-bottom: env(safe-area-inset-bottom);
    padding-bottom: calc(var(--footerHeight) + var(--safe-area-inset-bottom));
    min-height: 70.3px;
}
.tab_bar {
  z-index: 800;
  -webkit-tap-highlight-color: rgba(0,0,0,0);
  position: relative;
  height: auto;
}
.footer_nav{
    --alpha: 1;
    --safe-area-inset-bottom: env(safe-area-inset-bottom);
    -webkit-backdrop-filter: blur(calc(7px*(2 - var(--alpha))));
    backdrop-filter: blur(calc(7px * (2 - var(--alpha))));
    border-radius: 50px;
    padding: 5px 8px;
    display: flex;
    align-items: center;
    position: fixed;
    bottom: calc(10px + var(--safe-area-inset-bottom));
    left: 15px;
    right: 15px;
    box-shadow: 0 0 0 1px #e6e6e8;
    z-index: 5;
    min-height: var(--footerHeight);
    text-align: center;
    background: rgba(255,255,255,0.8);
    box-sizing: border-box;
    will-change: transform;
    transform: translateZ(0);
    transition: transform 0.2s linear, height 0.12s, background-color 0.3s ease-in-out;
    &::v-deep{
        .footer_item {
            list-style: none;
            position: relative;
            width: 100%;
            -webkit-touch-callout: none; /* iOS Safari */
            -webkit-user-select: none;   /* Chrome/Safari/Opera */
            -khtml-user-select: none;    /* Konqueror */
            -moz-user-select: none;      /* Firefox */
            -ms-user-select: none;       /* Internet Explorer/Edge */
            user-select: none;  
            .link_badge{
                position: absolute;
                top: -5px;
                right: -13px;
                .ant-badge-count{
                    line-height: 16px;
                    min-width: 16px;
                    height: 16px;
                    font-size: 10px;
                    padding: 0 5px;
                    &.ant-badge-multiple-words{
                        padding: 0 5px;
                    }
                }
            }
            .icon{
                display: flex;
                justify-content: center;
                align-items: center;
                position: relative;
                i{
                    font-size: 1.3rem;
                    line-height: 1;
                }
            }
            .label {
                font-size: 11px;
                width: 100%;
                margin-top: 2px;
                font-weight: 300;
                color: var(--footerLink);
                transition: color .3s ease-in-out;
            }
            .link {
                color: var(--text);
                display: flex;
                justify-content: center;
                flex-wrap: wrap;
                padding-bottom: 5px;
                padding-top: 5px;
                position: relative;
            }
            .router-link-exact-active {
                color: var(--blue);
            }
        }
    }
};
.row {
    display: flex;
    flex-wrap: wrap;
}
.col-12{
    flex: 0 0 100%;
    max-width: 100%;
}
.tab_bar .footer_nav ul {
    padding: 0;
    margin: 0;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
}
</style>
