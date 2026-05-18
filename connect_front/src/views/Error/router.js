const routes = [
    {
        path: '/404',
        name: 'page_404',
        component: () => import('./Error404.vue')
    }
]

export default routes
