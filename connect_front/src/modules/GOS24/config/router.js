import { i18n } from '@/config/i18n-setup'

export default [
    {
        name: 'articles',
        path: 'articles',
        isShow: false,
        isHidden: true,
        component: () => import(`../views/Articles.vue`),
        meta: {
            navWidget: "NavPage",
            get title() {
                return 'Статьи'
            },
            hideSidebar: true,
            isShow: false,
            hideMobile: false
        }
    },
    {
        name: 'news',
        path: 'news',
        isShow: false,
        isHidden: true,
        component: () => import(`../views/News.vue`),
        meta: {
            navWidget: "NavPage",
            get title() {
                return 'Новости и публикации Гос24'
            },
            hideSidebar: true,
            isShow: false,
            hideMobile: false
        }
    },
    {
        name: 'official',
        path: 'official',
        isShow: false,
        isHidden: true,
        component: () => import(`../views/Official.vue`),
        meta: {
            navWidget: "NavPage",
            get title() {
                return 'Официальные разъяснения'
            },
            hideSidebar: true,
            isShow: false,
            hideMobile: false
        }
    },
    {
        name: 'webinar',
        path: 'webinar',
        isShow: false,
        isHidden: true,
        component: () => import(`../views/Webinar.vue`),
        meta: {
            navWidget: "NavPage",
            get title() {
                return 'Вебинары'
            },
            hideSidebar: true,
            isShow: false,
            hideMobile: false
        }
    },
    {
        name: 'question',
        path: 'question',
        isShow: false,
        isHidden: true,
        component: () => import(`../views/Question.vue`),
        meta: {
            navWidget: "NavPage",
            get title() {
                return 'Вопрос-ответ'
            },
            hideSidebar: true,
            isShow: false,
            hideMobile: false
        }
    },
    {
        name: 'knowledgebase',
        path: 'knowledgebase',
        isShow: false,
        isHidden: true,
        component: () => import(`../views/Knowledgebase.vue`),
        meta: {
            navWidget: "NavPage",
            get title() {
                return 'База знаний'
            },
            hideSidebar: true,
            isShow: false,
            hideMobile: false
        }
    },
    {
        name: 'partition',
        path: 'partition',
        isShow: false,
        isHidden: true,
        component: () => import(`../views/Partition.vue`),
        meta: {
            navWidget: "NavPage",
            get title() {
                return 'Разделы'
            },
            hideSidebar: true,
            isShow: false,
            hideMobile: false
        }
    },
    {
        name: 'organ',
        path: 'organ',
        isShow: false,
        isHidden: true,
        component: () => import(`../views/Organ.vue`),
        meta: {
            navWidget: "NavPage",
            get title() {
                return 'Государственные органы'
            },
            hideSidebar: true,
            isShow: false,
            hideMobile: false
        }
    },
    {
        name: 'tag',
        path: 'tag',
        isShow: false,
        isHidden: true,
        component: () => import(`../views/Tag.vue`),
        meta: {
            navWidget: "NavPage",
            get title() {
                return 'Tеги'
            },
            hideSidebar: true,
            isShow: false,
            hideMobile: false
        }
    },
    {
        name: 'holidaycalendar',
        path: 'holidaycalendar',
        isShow: false,
        isHidden: true,
        component: () => import(`../views/HolidayCalendarAdmin.vue`),
        meta: {
            navWidget: "NavPage",
            get title() {
                return 'Праздничные и выходные дни'
            },
            hideSidebar: true,
            isShow: false,
            hideMobile: false
        }
    },
    {
        name: 'news_finance',
        path: 'news_finance',
        isShow: false,
        isHidden: true,
        component: () => import(`../views/NewsFinance.vue`),
        meta: {
            navWidget: "NavPage",
            get title() {
                return 'Публикации GOS24.Finance'
            },
            hideSidebar: true,
            isShow: false,
            hideMobile: false
        }
    },
    {
        name: 'calendar_finance',
        path: 'calendar_finance',
        isShow: false,
        isHidden: true,
        component: () => import(`../views/CalendarFinance.vue`),
        meta: {
            navWidget: "NavPage",
            get title() {
                return 'Календарь Finance'
            },
            hideSidebar: true,
            isShow: false,
            hideMobile: false
        }
    },

]
