export default [
    {
        name: 'notifications',
        path: 'notifications',
        component: () => import(`../views/List`),
        meta: {
            navWidget: "NavPage",
            title: "Список уведомлений"
        }
    }
]