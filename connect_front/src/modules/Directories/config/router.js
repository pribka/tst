import { i18n } from '@/config/i18n-setup'

export default [
    {
        name: 'directories-team',
        path: 'team',
        isShow: false,
        isHidden: true,
        component: () => import(`../Team`),
        meta: {
            navWidget: "NavPage",
            get title() {
                return 'Структура'
            },
            icon: 'fi-rr-building',
            hideSidebar: true,
            isShow: false,
            hideMobile: false
        }
    },
    {
        name: 'directories-clients',
        path: 'clients',
        isShow: false,
        isHidden: true,
        component: () => import(`../views/Clients`),
        props: {
            initPageModel: 'help_desk.CustomerCardModel',
            initPageName: 'list_help_desk.CustomerCardModel'
        },
        meta: {
            navWidget: "NavPage",
            get title() {
                return i18n.t('helpdesk.clients_label')
            },
            icon: 'fi-rr-id-card-clip-alt',
            hideSidebar: true,
            isShow: false,
            hideMobile: false
        }
    },
    {
        name: 'directories-positions',
        path: 'positions',
        isShow: false,
        isHidden: true,
        component: () => import(`../views/Positions`),
        props: {
            initPageModel: 'help_desk.ContactPersonPostModel',
            initPageName: 'help_desk.ContactPersonPostModel'
        },
        meta: {
            navWidget: "NavPage",
            get title() {
                return i18n.t('helpdesk.positions_label')
            },
            icon: 'fi-rr-rectangle-list',
            hideSidebar: true,
            isShow: false,
            hideMobile: false
        }
    },
    {
        name: 'directories-work-directions',
        path: 'work-directions',
        isShow: false,
        isHidden: true,
        component: () => import(`../views/WorkDirections`),
        props: {
            initPageModel: 'catalogs.WorkDirectionModel',
            initPageName: 'catalogs.WorkDirectionModel'
        },
        meta: {
            navWidget: "NavPage",
            get title() {
                return i18n.t('directories.work_directions_label')
            },
            icon: 'fi-rr-rectangle-list',
            hideSidebar: true,
            isShow: false,
            hideMobile: false
        }
    },
    {
        name: 'directories-categories',
        path: 'categories',
        isShow: false,
        isHidden: true,
        component: () => import(`../views/Categories`),
        props: {
            initPageModel: 'help_desk.HelpDeskTicketCategoryModel',
            initPageName: 'help_desk.HelpDeskTicketCategoryModel'
        },
        meta: {
            navWidget: "NavPage",
            get title() {
                return i18n.t('helpdesk.categories_label')
            },
            icon: 'fi-rr-rectangle-list',
            hideSidebar: true,
            isShow: false,
            hideMobile: false
        }
    },
    {
        name: 'directories-groups',
        path: 'groups',
        isShow: false,
        isHidden: true,
        component: () => import('../views/Groups'),
        meta: {
            navWidget: "NavPage",
            get title() {
                return 'Команды'
            },
            icon: 'fi-rr-users',
            hideSidebar: true,
            isShow: false,
            hideMobile: false
        }
    }
]
