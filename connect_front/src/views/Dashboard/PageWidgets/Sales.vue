<template>
    <div class="sales_shell">
        <div class="sales_shell__top">
            <div>
                <div class="sales_shell__title">
                    Продажи
                </div>
                <div class="sales_shell__crumb">
                    Продажи / <b>{{ activeTitle }}</b>
                </div>
            </div>
            <div class="sales_shell__actions" data-guide-id="sales-quick-create">
                <button type="button" @click="goTo('sales-leads')">
                    + Лид
                </button>
                <button type="button" @click="goTo('sales-interest')">
                    + Интерес
                </button>
                <button type="button" @click="goTo('sales-orders')">
                    + Заказ
                </button>
            </div>
        </div>
        <div class="sales_shell__nav" data-guide-id="sales-main-nav">
            <button
                v-for="route in pageRoutes"
                :key="route.name"
                type="button"
                class="sales_shell__nav_item"
                :class="{ 'sales_shell__nav_item--active': route.name === activeRouteName }"
                @click="changePage(route.name)">
                {{ route.title }}
            </button>
        </div>
        <div class="sales_shell__body">
            <router-view />
        </div>
        <SalesWorkspaceGuide floating />
    </div>
</template>

<script>
export default {
    name: 'SalesPage',
    components: {
        SalesWorkspaceGuide: () => import('@/views/Dashboard/PageWidgets/SalesWorkspaceGuide.vue')
    },
    computed: {
        salesRoute() {
            return this.$store.state.navigation.routerApp.find(route => route.name === 'sales')
        },
        pageRoutes() {
            return (this.salesRoute?.children || []).filter(route => route.isShow !== false)
        },
        activeRouteName() {
            return this.$route.name === 'sales'
                ? 'sales-dashboard'
                : this.$route.name
        },
        activeTitle() {
            const activeRoute = this.pageRoutes.find(route => route.name === this.activeRouteName)
            return activeRoute?.title || 'Рабочий стол'
        }
    },
    methods: {
        goTo(name) {
            if (name && name !== this.$route.name) {
                this.$router.push({ name })
            }
        },
        changePage(name) {
            if (name && name !== this.$route.name) {
                this.$router.push({ name })
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.sales_shell {
    height: 100%;
    display: flex;
    flex-direction: column;
    min-height: 0;
    background: #eeedea;
}

.sales_shell__top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    min-height: 40px;
    padding: 7px 16px;
    border-bottom: 1px solid #e0dfd8;
    background: #fff;
    flex-wrap: wrap;
}

.sales_shell__title {
    font-size: 13px;
    font-weight: 600;
    color: #e67e2e;
    white-space: nowrap;
}

.sales_shell__crumb {
    margin-top: 1px;
    font-size: 11px;
    color: #666660;
    white-space: nowrap;
}

.sales_shell__crumb b {
    color: #1a1a1a;
    font-weight: 500;
}

.sales_shell__actions {
    display: flex;
    align-items: center;
    gap: 5px;
}

.sales_shell__actions button {
    min-height: 28px;
    padding: 0 10px;
    border: 1px solid #cccbc3;
    border-radius: 6px;
    background: #fff;
    color: #1a1a1a;
    font: inherit;
    font-size: 11px;
    cursor: pointer;
}

.sales_shell__actions button:last-child {
    background: #e67e2e;
    border-color: #e67e2e;
    color: #fff;
}

.sales_shell__nav {
    display: flex;
    align-items: center;
    gap: 0;
    padding: 0 15px;
    border-bottom: 1px solid #e0dfd8;
    background: #fff;
    overflow-x: auto;
}

.sales_shell__nav_item {
    min-height: 34px;
    padding: 0 11px;
    border: 0;
    border-bottom: 2px solid transparent;
    background: transparent;
    color: #666660;
    font: inherit;
    font-size: 12px;
    white-space: nowrap;
    cursor: pointer;
}

.sales_shell__nav_item:hover {
    color: #1a1a1a;
}

.sales_shell__nav_item--active {
    border-bottom-color: #e67e2e;
    color: #e67e2e;
    font-weight: 500;
}

.sales_shell__body {
    flex: 1;
    min-height: 0;
    overflow: hidden;
}

@media (max-width: 767px) {
    .sales_shell__top {
        align-items: flex-start;
        flex-direction: column;
    }

    .sales_shell__actions {
        width: 100%;
        overflow-x: auto;
    }
}
</style>
