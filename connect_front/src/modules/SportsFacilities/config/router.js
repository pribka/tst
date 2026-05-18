import { i18n } from '@/config/i18n-setup'

export default [
    {
        name: 'full_sports_facilities',
        path: 'sports-facilities',
        isHidden: true,
        component: () => import('../layouts/ProjectLayout.vue'),
        redirect: { name: 'full_sports_facilities_gallery' },
        isShow: false,
        hideMobile: false,
        children: [
            {
                name: 'full_sports_facilities_pasport',
                path: ':id/pasport',
                component: () => import(`../views/Pasport`),
                isHidden: true,
                isShow: false,
                hideMobile: false,
                meta: {
                    navWidget: "NavPage",
                    title: i18n.t('sports.sportsFacilities'),
                    icon: 'fi-rr-shopping-cart',
                    hideSidebar: true,
                    isShow: false,
                    hideMobile: false
                }
            },
            {
                name: 'full_sports_facilities_repair',
                path: ':id/info',
                component: () => import(`../views/RepairInformation`),
                isHidden: true,
                isShow: false,
                hideMobile: false,
                meta: {
                    navWidget: "NavPage",
                    title: i18n.t('sports.sportsFacilities'),
                    icon: 'fi-rr-shopping-cart',
                    hideSidebar: true,
                    isShow: false,
                    hideMobile: false
                }
            },
            {
                name: 'full_sports_facilities_technical',
                path: ':id/technical',
                component: () => import(`../views/MaterialTechnicalEquipment`),
                isHidden: true,
                isShow: false,
                hideMobile: false,
                meta: {
                    navWidget: "NavPage",
                    title: i18n.t('sports.sportsFacilities'),
                    icon: 'fi-rr-shopping-cart',
                    hideSidebar: true,
                    isShow: false,
                    hideMobile: false
                }
            },
            {
                name: 'full_sports_facilities_files',
                path: ':id/files',
                component: () => import(`../views/Files`),
                isHidden: true,
                isShow: false,
                hideMobile: false,
                meta: {
                    navWidget: "NavPage",
                    title: i18n.t('sports.files'),
                    icon: 'fi-rr-shopping-cart',
                    hideSidebar: true,
                    isShow: false,
                    hideMobile: false
                }
            },
            {
                name: 'full_sports_facilities_history',
                path: ':id/history',
                component: () => import(`../views/History`),
                isHidden: true,
                isShow: false,
                hideMobile: false,
                meta: {
                    navWidget: "NavPage",
                    title: i18n.t('sports.history'),
                    icon: 'fi-rr-shopping-cart',
                    hideSidebar: true,
                    isShow: false,
                    hideMobile: false
                }
            },
            {
                name: 'full_sports_facilities_gallery',
                path: ':id/gallery',
                component: () => import(`../views/Gallery`),
                isHidden: true,
                isShow: false,
                hideMobile: false,
                meta: {
                    navWidget: "NavPage",
                    title: i18n.t('sports.gallery'),
                    icon: 'fi-rr-shopping-cart',
                    hideSidebar: true,
                    isShow: false,
                    hideMobile: false
                }
            },
            {
                name: 'full_sports_facilities_characteristics',
                path: ':id/characteristics',
                component: () => import(`../views/Characteristics`),
                isHidden: true,
                isShow: false,
                hideMobile: false,
                meta: {
                    navWidget: "NavPage",
                    title: i18n.t('sports.gallery'),
                    icon: 'fi-rr-shopping-cart',
                    hideSidebar: true,
                    isShow: false,
                    hideMobile: false
                }
            },
            {
                name: 'full_sports_facilities_object_information',
                path: ':id/object_information',
                component: () => import(`../views/ObjectInformation`),
                isHidden: true,
                isShow: false,
                hideMobile: false,
                meta: {
                    navWidget: "NavPage",
                    title: i18n.t('sports.objectInformation'),
                    icon: 'fi-rr-shopping-cart',
                    hideSidebar: true,
                    isShow: false,
                    hideMobile: false
                }
            },
            {
                name: 'full_sports_facilities_section_information',
                path: ':id/section_information',
                component: () => import(`../views/SectionInformation`),
                isHidden: true,
                isShow: false,
                hideMobile: false,
                meta: {
                    navWidget: "NavPage",
                    title: i18n.t('sports.sectionInfo'),
                    icon: 'fi-rr-shopping-cart',
                    hideSidebar: true,
                    isShow: false,
                    hideMobile: false
                }
            }
        ],
        meta: {
            navWidget: "NavPage",
            title: i18n.t('sports.sportsFacilities'),
            icon: 'fi-rr-shopping-cart',
            hideSidebar: true,
            isShow: false
        }
    }
]