export default [
    {
        name: 'moderation-list',
        path: 'moderation-list',
        isShow: false,
        isHidden: true,
        component: () => import(`../views/Moderation.vue`),
        meta: {
            navWidget: "NavPage",
            get title() {
                return 'Модерация'
            },
            icon: 'fi-rr-comment-alt-dots',
            hideSidebar: true,
            isShow: false,
            hideMobile: false
        }
    },
    {
        name: 'moderation-new-clients',
        path: 'moderation-new-clients',
        isShow: false,
        isHidden: true,
        component: () => import(`../views/NewClients.vue`),
        meta: {
            navWidget: "NavPage",
            get title() {
                return 'Новые пользователи'
            },
            icon: 'fi-rr-id-card-clip-alt',
            hideSidebar: true,
            isShow: false,
            hideMobile: false
        }
    }
]
