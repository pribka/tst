import { v4 as uuidv4, validate as uuidValidate } from 'uuid'

export default [
    {
        name: 'chat-contact',
        path: '/',
        isShow: false,
        isHidden: true,
        component: () => import(`../components/MobileChat/Main.vue`),
        meta: {
            title: "Чат",
            isShow: false
        }
    },
    {
        name: 'chat-body',
        path: ':id',
        isShow: false,
        isHidden: true,
        component: () => import(`../components/MobileChat/Chat.vue`),
        meta: {
            title: "Чат",
            isShow: false
        },
        beforeEnter: (to, from, next) => {
            const { params } = to
            if (uuidValidate(params.id)) {
                return next()
            } else {
                return next({ name: 'chat-contact' })
            }
        }
    }
]