const routes = [
    {
        path: 'login',
        name: 'login',
        component: () => import(`@/views/Authorization/Auth`)
    },
    {
        path: 'registration',
        name: 'registration',
        component: { render: h => h() }
    },
    {
        path: 'forgot-password',
        name: 'forgotPassword',
        component: { render: h => h() }
    },
    {
        path: 'reset-password/:id',
        name: 'resetPassword',
        component: { render: h => h() }
    },
    {
        path: 'forgot-password/forgot-email',
        name: 'forgotPasswordEmail',
        component: { render: h => h() }
    },
    {
        path: 'forgot-password/forgot-phone',
        name: 'forgotPasswordPhone',
        component: { render: h => h() }
    },
    {
        path: 'join-user',
        name: 'joinUser',
        component: { render: h => h() }
    }
]

export default routes
