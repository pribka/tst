import { i18n } from '@/config/i18n-setup'

export default [
    {
        name: 'reports-dashboards',
        path: 'dashboards',
        isShow: false,
        isHidden: true,
        component: () => import(`../views/ReportsDashboard.vue`),
        meta: {
            navWidget: "NavPage",
            get title() {
                return i18n.t('dashbord_label')
            },
            icon: 'fi-rr-users',
            hideSidebar: true,
            isShow: false,
            hideMobile: false
        }
    },
    {
        name: 'reports-templates',
        path: 'templates',
        isShow: false,
        isHidden: true,
        component: () => import(`../views/ReportTemplates.vue`),
        meta: {
            navWidget: "NavPage",
            get title() {
                return i18n.t('report_label')
            },
            icon: 'fi-rr-comment-alt-middle',
            hideSidebar: true,
            isShow: false,
            hideMobile: false
        }
    },
]