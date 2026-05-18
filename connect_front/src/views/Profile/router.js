const routes = [
    {
        name: 'profile',
        path: 'profile',
        isHidden: true,
        component: () => import(`@/views/Profile/Page`)
    }
]

export default routes
