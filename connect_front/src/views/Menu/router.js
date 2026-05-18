const routes = [
    {
        name: 'menu',
        path: 'menu',
        isHidden: true,
        component: () => import(`@/views/Menu/Page`),
    },
]

export default routes
