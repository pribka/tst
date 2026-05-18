import { i18n } from '@/config/i18n-setup'

export default [
    {
        name: 'tickets',
        path: 'tickets',
        isShow: false,
        isHidden: true,
        component: () => import(`../views/Tickets`),
        meta: {
            navWidget: "NavPage",
            get title() {
                return i18n.t('helpdesk.request_label')
            },
            icon: 'fi-rr-comment-alt-dots',
            hideSidebar: true,
            isShow: false,
            hideMobile: false
        }
    },
    /*{
        name: 'clients',
        path: 'clients',
        isShow: false,
        isHidden: true,
        component: () => import(`../views/Clients`),
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
    },*/
    {
        name: 'unconfirmed_appeals',
        path: 'unconfirmed_appeals',
        isShow: false,
        isHidden: true,
        component: () => import(`../views/UnconfirmedAppeals`),
        meta: {
            navWidget: "NavPage",
            get title() {
                return i18n.t('helpdesk.unconfirmed_appeals_label')
            },
            icon: 'fi-rr-comment-exclamation',
            hideSidebar: true,
            isShow: false,
            hideMobile: false
        }
    },
    {
        name: 'spam',
        path: 'spam',
        isShow: false,
        isHidden: true,
        component: () => import(`../views/Spam`),
        meta: {
            navWidget: "NavPage",
            get title() {
                return i18n.t('helpdesk.spam_label')
            },
            icon: 'fi-rr-message-xmark',
            hideSidebar: true,
            isShow: false,
            hideMobile: false
        }
    },
    {
        name: 'request',
        path: 'request',
        isShow: false,
        isHidden: true,
        component: () => import(`../views/Request`),
        meta: {
            navWidget: "NavPage",
            get title() {
                return i18n.t('helpdesk.request_label')
            },
            icon: 'fi-rr-messages-question',
            hideSidebar: true,
            isShow: false,
            hideMobile: false
        }
    },
    /*{
        name: 'categories',
        path: 'categories',
        isShow: false,
        isHidden: true,
        component: () => import(`../views/Categories`),
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
        name: 'positions',
        path: 'positions',
        isShow: false,
        isHidden: true,
        component: () => import(`../views/Positions`),
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
    }*/
]
