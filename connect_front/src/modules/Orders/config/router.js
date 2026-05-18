export default [
    {
        name: 'create_order',
        path: 'order/create',
        component: () => import(`../views/CreateOrder`),
        isHidden: true,
        meta: {
            navWidget: "NavPage",
            title: "Оформление заказа",
            icon: 'fi-rr-shopping-cart',
            hideSidebar: true
        }
    },
    {
        name: 'create_return_order',
        path: 'order/create-return',
        component: () => import(`../views/returnOrder`),
        isHidden: true,
        meta: {
            navWidget: "NavPage",
            title: "Оформление возврата",
            icon: 'fi-rr-shopping-cart',
            hideSidebar: true
        }
    }
]