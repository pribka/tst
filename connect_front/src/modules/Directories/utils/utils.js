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
