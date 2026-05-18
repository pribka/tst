export const clientFormKey = 'customer_form'
import { i18n } from '@/config/i18n-setup'

export const clientFormModel = {
    name: "",
    full_name: "",
    inn: "",
    budget_program_administrator: null,
    legal_address: "",
    description: "",
    org_admin: null,
    customer_card: null,
    admins: [
        {
            key: Date.now(),
            name: "",
            bin: "",
            results: [],
            next: true,
            page: 1,
            add: true,
            trigger: "none",
            selected: false,
            loading: false
        }
    ],
    contact_persons: [
        {
            key: Date.now(),
            name:"",
            email:"", 
            telegram:"", 
            phone:"",
            post: "",
            post_inst: null,
            is_main: false
        }
    ]
}

export const audioFormats = [
    'mp3',
    'wav',
    'ogg',
    'oga',
    'm4a',
    'aac',
    'flac',
    'alac',
    'wma',
    'aiff',
    'aif',
    'au',
    'amr',
    'ac3',
    'opus',
    'ra',
    'rm',
    'mid',
    'midi',
    'dsd',
    'caf',
    'm4r'
]

export const videoFormats = [
    'mp4',
    'm4v',
    'mov',
    'avi',
    'wmv',
    'flv',
    'webm',
    'mkv',
    '3gp',
    '3g2',
    'f4v',
    'mpeg',
    'mpg',
    'mp2',
    'mpe',
    'mpv',
    'ts',
    'm2ts',
    'mts',
    'vob',
    'ogv',
    'divx',
    'xvid',
    'rm',
    'rmvb',
    'asf',
    'dv',
    'mxf'
]

export const clientForm = {
    "description": {
        "placeholder": i18n.t('helpdesk.additional_information')
    },
    "inn": {
        "title": i18n.t('helpdesk.organization_bin'),
        "placeholder": i18n.t('helpdesk.enter_organization_bin')
    },
    "full_name": {
        "title": i18n.t('helpdesk.full_name'),
        "placeholder": i18n.t('helpdesk.full_name')
    },
    "legal_address": {
        "title": i18n.t('helpdesk.legal_address'),
        "placeholder": i18n.t('helpdesk.enter_legal_address'),
    },
    "org_admin": {
        "title": i18n.t('helpdesk.support_organization'),
        "placeholder": i18n.t('helpdesk.support_organization')
    },
    "admins": {
        "title": i18n.t('helpdesk.admin_organization'),
        "fields": {
            "bin": {
                "title": i18n.t('helpdesk.bin'),
                "placeholder": i18n.t('helpdesk.enter_bin')
            },
            "name": {
                "title": i18n.t('helpdesk.name_string'),
                "placeholder": i18n.t('helpdesk.enter_name')
            }
        }
    },
    "contact_persons": {
        "title": i18n.t('helpdesk.contact_person'),
        "fields": {
            "name": {
                "placeholder": i18n.t('helpdesk.enter_full_name')
            },
            "phone": {
                "placeholder": i18n.t('helpdesk.enter_phone')
            },
            "telegram": {
                "placeholder": i18n.t('helpdesk.enter_telegram')
            },
            "email": {
                "placeholder": i18n.t('helpdesk.enter_email')
            },
            "post": {
                "placeholder": i18n.t('helpdesk.enter_position')
            },
            "post_inst": {
                "placeholder": i18n.t('helpdesk.select_position')
            },
            "is_main": {
                "title": i18n.t('helpdesk.is_main')
            },
            "comment": {
                "placeholder": i18n.t('helpdesk.enter_comment')
            }
        }
    }
}

export function formatSeconds(sec) {
    if (!sec && sec !== 0) return ''
    sec = Number(sec)

    const units = [
        {
            name: [
                i18n.t('helpdesk.year1'),
                i18n.t('helpdesk.year2'),
                i18n.t('helpdesk.year3')
            ],
            value: 365 * 24 * 3600
        },
        {
            name: [
                i18n.t('helpdesk.month1'),
                i18n.t('helpdesk.month2'),
                i18n.t('helpdesk.month3')
            ],
            value: 30 * 24 * 3600
        },
        {
            name: [
                i18n.t('helpdesk.week1'),
                i18n.t('helpdesk.week2'),
                i18n.t('helpdesk.week3')
            ],
            value: 7 * 24 * 3600
        },
        {
            name: [
                i18n.t('helpdesk.day1'),
                i18n.t('helpdesk.day2'),
                i18n.t('helpdesk.day3')
            ],
            value: 24 * 3600
        },
        {
            name: [
                i18n.t('helpdesk.hour1'),
                i18n.t('helpdesk.hour2'),
                i18n.t('helpdesk.hour3')
            ],
            value: 3600
        },
        {
            name: [
                i18n.t('helpdesk.minute1'),
                i18n.t('helpdesk.minute2'),
                i18n.t('helpdesk.minute3')
            ],
            value: 60
        },
        {
            name: [
                i18n.t('helpdesk.second1'),
                i18n.t('helpdesk.second2'),
                i18n.t('helpdesk.second3')
            ],
            value: 1
        }
    ]

    const parts = []

    for (const u of units) {
        const count = Math.floor(sec / u.value)
        if (count > 0) {
            const form = count % 10 === 1 && count % 100 !== 11
                ? u.name[0]
                : count % 10 >= 2 && count % 10 <= 4 && (count % 100 < 10 || count % 100 >= 20)
                    ? u.name[1]
                    : u.name[2]

            parts.push(`${count} ${form}`)
            sec = sec % u.value
        }
    }

    if (parts.length === 0) return i18n.t('null_sec', { num: 0 })
    return parts.join(' ')
}
