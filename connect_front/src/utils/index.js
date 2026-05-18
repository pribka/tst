import message from '@/utils/clickableMessage'
import store from '@/store/index.js'
import { i18n } from '@/config/i18n-setup'

export const mobileModuleCheck = () => {
    if(store.state.isMobile) {
        message.info('Этот модуль доступен только в настольной версии приложения', 6)
        return false
    }
    return true
}

export const setWithExpiry = () => {
    const now = new Date()
    const time = now.getTime() + (1000 * 60 * 60 * 24)
    return now.getTime() + time
}

export const getTableFieldValue = ({ toField, value, editorType }) => {
    switch (editorType) {
    case 'WidgetSelect':
        if (toField)
            return value[toField]
        else
            return null
        break;
    case 'WidgetSelectEnum':
        if (toField)
            return value[toField]
        else
            return null
        break;
    case 'WidgetSwitch':
        return value === null ? false : value
    default:
        return value
    }
}

export const numberWithSpaces = (x) => {
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
}

export const fieldWidgetType = (col) => {
    switch (col.cellRenderer) {
    case 'UserRow':
        return null
        break;
    case 'RelatedRow':
        return null
        break;
    case 'IdRow':
        return null
        break;
    default:
        return null
    }
}

export const fieldType = (field) => {
    switch (field.type) {
    case 'string':
        return ''
        break;
    case 'number':
        return 0
        break;
    case 'date':
        return null
        break;
    case 'select':
        return null
        break;
    case 'radio':
        return null
        break;
    case 'checkbox':
        return null
        break;
    case 'checkboxGroup':
        return []
        break;
    case 'switch':
        return false
        break;
    case 'integer':
        return 0
    case 'selectEnum':
        return null
        break;
    case 'file':
        if (field?.widgetConfig?.multiple)
            return []
        else
            return null
        break;
    default:
        return ''
    }
}

export const flatFormFields = (fields) => {
    return fields.flatMap(field => {
        if (field.type === 'GroupFields')
            return field.fieldInfo
        else
            return field
    })
}

export const valueType = ({ fields, value, key }) => {
    const flatFields = flatFormFields(fields)
    const field = flatFields.find(f => f.name === key)

    switch (field.type) {
    case 'select':
        if (value) {
            return value[field.toField]
        } else
            return value
        break;
    case 'selectEnum':
        if (value) {
            return value[field.toField]
        } else
            return value
        break;
    case 'MultiplyGroupFields':
        if (value?.length) {
            const { fieldInfo } = field
            let result = []
            value.forEach(val => {
                let res = {}
                for (const key in val) {
                    res[key] = valueType({
                        fields: fieldInfo,
                        value: val[key],
                        key
                    })
                }
                result.push(res)
            })
            return result
        } else
            return []
        break;
    default:
        return value
    }
}

export const replacePath = ({ path, params }) => {
    let queryPath = path
    queryPath.replace(/\<(.*?)\>/g, (match, pattern) => {
        queryPath = queryPath.replace(`<${pattern}>`, params[pattern])
        return match
    })

    return queryPath
}

export const systemFormButton = [
    {
        icon: "delete",
        class: "",
        type: "dashed",
        title: "",
        action: "clear",
        size: "default",
        content: "Очистить",
        popconfirm: {
            title: "Вы действительно хотите очистить форму?",
            okText: "Да",
            cancelText: "Нет",
            action: "clear"
        },
        widget: "Popconfirm"
    }
]

export const systemFormButtonClose = [
    {
        icon: "close",
        class: "",
        type: "dashed",
        title: "",
        action: "close",
        size: "default",
        content: "Закрыть",
        widget: "Default"
    }
]

export const tableFormButton = [
    {
        icon: "delete",
        class: "",
        type: "dashed",
        title: "",
        action: "clear_table",
        size: "default",
        content: "Очистить",
        popconfirm: {
            title: "Вы действительно хотите очистить таб часть?",
            okText: "Да",
            cancelText: "Нет",
            action: "clear_table"
        },
        widget: "Popconfirm"
    }
]

export const filesFormat = [
    'ai',
    'doc',
    'css',
    'scss',
    'sass',
    'docx',
    'eps',
    'exe',
    'gif',
    'gz',
    'jpg',
    'js',
    'less',
    'svg',
    'mp3',
    'mp4',
    'pdf',
    'png',
    'pps',
    'ppt',
    'psd',
    'rar',
    'rtf',
    'tiff',
    'txt',
    'xls',
    'xlsx',
    'zip',
    '7z',
    'otf',
    'iso',
    'ico',
    'cdr',
    'php',
    'sketch',
    'javascript',
    'dmg',
    'sql',
    'tar',
    'wav',
    'msg',
    'jar',
    'apk',
    '3gp',
    'avi',
    'mov',
    'dll',
    'dat',
    'flv',
    'sys'
]
export const conv_size = (b) => {
    let fsizekb = b / 1024,
        fsizemb = fsizekb / 1024,
        fsizegb = fsizemb / 1024,
        fsizetb = fsizegb / 1024,
        fsize = '';

    if (fsizekb <= 1024) {
        fsize = fsizekb.toFixed(3) + ' кб';
    } else if (fsizekb >= 1024 && fsizemb <= 1024) {
        fsize = fsizemb.toFixed(3) + ' мб';
    } else if (fsizemb >= 1024 && fsizegb <= 1024) {
        fsize = fsizegb.toFixed(3) + ' гб';
    } else {
        fsize = fsizetb.toFixed(3) + ' тб';
    }

    return fsize;
}

export const priceFormatter = price => {
    const priceEnd = x => ( (x.toString().includes('.')) ? (x.toString().split('.').pop().length) : (0) )

    const valPrice = String(price)

    let newPrice = Number(valPrice)

    if(priceEnd(newPrice) > 2) { // Если после запятой больше 2х знаков округляем до двух.
        newPrice = +newPrice.toFixed(2)
    } 

    if(priceEnd(newPrice) === 2) {
        newPrice =  String(newPrice.toLocaleString('ru-RU')).replace(',', '.')
    }
    else if (priceEnd(newPrice) === 1) {
        newPrice =  `${String(newPrice.toLocaleString('ru-RU')).replace(',', '.')}0`
    }
    else {
        newPrice =  `${String(newPrice.toLocaleString('ru-RU')) }.00`
    }

    return newPrice
}

export const errorHandler = ({ error, text = '', duration = 2, key = 'handleError', show = true }) => {
    console.error(error?.data || error, text, `${error?.status ? `code: ${error.status}` : ''} !handleError`)

    if(show) {
        const messageConfig = {
            content: i18n.t('error'),
            key,
            duration
        }

        const detail = error?.data?.detail || error?.detail

        if (typeof detail === 'string' && detail.trim()) {
            messageConfig.content = detail
        } else if (Array.isArray(error) && error.length) {
            const messages = []
            error.forEach(e => {
                if (typeof e === 'string' && e.trim()) messages.push(e)
                else if (Array.isArray(e) && e.length) messages.push(e.join(', '))
                else if (e && typeof e === 'object') {
                    Object.keys(e).forEach(k => {
                        const v = e[k]
                        if (Array.isArray(v) && v.length) messages.push(v.join(', '))
                        else if (typeof v === 'string' && v.trim()) messages.push(v)
                    })
                }
            })
            if (messages.length) messageConfig.content = messages.join('; ')
            else messageConfig.content = String(error)
        } else if (error && typeof error === 'object' && !error.response && Object.keys(error).length) {
            const errs = error
            const messages = []
            Object.keys(errs).forEach(k => {
                const v = errs[k]
                if (Array.isArray(v) && v.length) messages.push(v.join(', '))
                else if (typeof v === 'string' && v.trim()) messages.push(v)
                else if (v && typeof v === 'object') {
                    const nested = []
                    Object.keys(v).forEach(nk => {
                        const nv = v[nk]
                        if (Array.isArray(nv) && nv.length) nested.push(nv.join(', '))
                        else if (typeof nv === 'string' && nv.trim()) nested.push(nv)
                    })
                    if (nested.length) messages.push(nested.join(', '))
                }
            })
            if (messages.length) messageConfig.content = messages.join('; ')
        } else if (error.status === 404) {
            messageConfig.content = 'Страница не найдена'
        } else if (error.status === 403) {
            messageConfig.content = i18n.t('no_rights')
        } else if (error.status === 401) {
            messageConfig.content = i18n.t('auth_required')
        } else if (error.status === 500 || error.status === 502) {
            messageConfig.content = i18n.t('server_error', { error: error.status })
        } else if (typeof error === 'string') {
            messageConfig.content = error
        } else if (Array.isArray(error) && error.length) {
            messageConfig.content = error.join(', ')
        } else if (error.response?.data?.description) {
            const descriptions = error.response.data.description
            if (Array.isArray(descriptions)) {
                messageConfig.content = descriptions.join('; ')
            } else {
                messageConfig.content = descriptions
            }
        } else if (error.response?.data?.error && typeof error.response.data.error === 'object') {
            const errs = error.response.data.error
            const messages = []
            Object.keys(errs).forEach(k => {
                const v = errs[k]
                if (Array.isArray(v) && v.length) messages.push(v.join(', '))
                else if (typeof v === 'string' && v.trim()) messages.push(v)
                else if (v && typeof v === 'object') {
                    const nested = []
                    Object.keys(v).forEach(nk => {
                        const nv = v[nk]
                        if (Array.isArray(nv) && nv.length) nested.push(nv.join(', '))
                        else if (typeof nv === 'string' && nv.trim()) nested.push(nv)
                    })
                    if (nested.length) messages.push(nested.join(', '))
                }
            })
            if (messages.length) messageConfig.content = messages.join('; ')
        }

        message.error(messageConfig)
    }
}
