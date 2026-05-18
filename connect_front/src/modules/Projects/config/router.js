import { i18n } from '@/config/i18n-setup'

export default [
    {
        name: 'projects-list',
        path: 'list',
        isShow: false,
        isHidden: true,
        component: () => import(`../views/List.vue`),
        meta: {
            navWidget: "NavPage",
            get title() {
                return i18n.t('project.project_list')
            },
            icon: 'fi-rr-money-check',
            hideSidebar: true,
            isShow: false,
            hideMobile: false
        }
    },
    /*{
        name: 'projects-gant',
        path: 'gantt',
        isShow: false,
        isHidden: true,
        component: () => import(`../views/Gantt.vue`),
        meta: {
            navWidget: "NavPage",
            get title() {
                return i18n.t('project.project_gant')
            },
            icon: 'fi-rr-stats',
            hideSidebar: true,
            isShow: false,
            hideMobile: true
        }
    },*/
    {
        name: 'projects-sprints',
        path: 'sprints',
        isShow: false,
        isHidden: true,
        component: () => import(`../views/Sprints.vue`),
        meta: {
            navWidget: "NavPage",
            get title() {
                return i18n.t('project.sprints')
            },
            icon: 'fi-rr-play-pause',
            hideSidebar: true,
            isShow: false,
            hideMobile: true
        }
    }
]