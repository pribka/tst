export default [
    {
        name: 'business_processes_main',
        path: '/',
        component: () => import(`../views/MainView`),
        meta: {
            navWidget: "NavPage",
            title: "Бизнес-Процесс"
        },
    },
    {
        name: 'business_processes_list',
        path: ':processId',
        component: () => import(`../views/DetailList`),
        meta: {
            navWidget: "NavPage",
            title: "Бизнес-Процесс"
        }
    }
]