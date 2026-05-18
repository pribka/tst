import { i18n } from '@/config/i18n-setup'

export default [
    {
        name: 'full_invest_project',
        path: 'invest-project',
        isHidden: true,
        component: () => import('../layouts/ProjectLayout.vue'),
        redirect: { name: 'full_invest_project' },
        isShow: false,
        hideMobile: false,
        children: [
            {
                name: 'full_invest_project_info',
                path: ':id/info',
                component: () => import(`../views/InvestProject`),
                isHidden: true,
                isShow: false,
                hideMobile: false,
                meta: {
                    navWidget: "NavPage",
                    title: i18n.t('invest.investProjectTitle'),
                    icon: 'fi-rr-shopping-cart',
                    hideSidebar: true,
                    isShow: false,
                    hideMobile: false
                }
            },
            {
                name: 'full_invest_project_documents',
                path: ':id/documents',
                component: () => import(`../views/InvestDocuments`),
                isHidden: true,
                isShow: false,
                hideMobile: false,
                meta: {
                    navWidget: "NavPage",
                    title: i18n.t('invest.investProjectTitle'),
                    icon: 'fi-rr-shopping-cart',
                    hideSidebar: true,
                    isShow: false,
                    hideMobile: false
                }
            },
            {
                name: 'full_invest_project_timeline',
                path: ':id/timeline',
                component: () => import(`../views/InvestTimeline`),
                isHidden: true,
                isShow: false,
                hideMobile: false,
                meta: {
                    navWidget: "NavPage",
                    title: i18n.t('invest.investProjectTitle'),
                    icon: 'fi-rr-shopping-cart',
                    hideSidebar: true,
                    isShow: false,
                    hideMobile: false
                }
            }
        ],
        meta: {
            navWidget: "NavPage",
            title: i18n.t('invest.investProjectTitle'),
            icon: 'fi-rr-shopping-cart',
            hideSidebar: true,
            isShow: false
        }
    }
]