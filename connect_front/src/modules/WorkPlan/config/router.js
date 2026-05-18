import { i18n } from '@/config/i18n-setup'

export default [
    {
        name: 'workplan-consolidation',
        path: 'consolidation',
        isShow: false,
        isHidden: true,
        component: () => import('../views/Consolidation'),
        meta: {
            navWidget: "NavPage",
            get title() {
                return i18n.t('workplan.consolidation_page_title')
            },
            hideSidebar: true,
            isShow: false,
            hideMobile: false
        }
    },
    {
        name: 'workplan-employees',
        path: 'employees',
        isShow: false,
        isHidden: true,
        component: () => import('../views/Employees'),
        meta: {
            navWidget: "NavPage",
            get title() {
                return i18n.t('workplan.employees_page_title')
            },
            hideSidebar: true,
            isShow: false,
            hideMobile: false
        }
    }
]
