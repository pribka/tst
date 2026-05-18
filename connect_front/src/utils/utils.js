import { i18n } from '@/config/i18n-setup'
import merge from 'lodash/fp/merge'
import isNil from 'lodash/fp/isNil'
import moment from 'moment'
import { DeviceUUID } from 'device-uuid'
import store from '../store'

let lastManualTitle = null

const getSiteName = () => {
    if(store.config?.site_setting?.site_name)
        return store.config.site_setting.site_name
    else
        return 'Gos24.КОННЕКТ'
}

export const secondsFormat = duration => {
    const sec = Number(duration)
    if (!sec || !Number.isFinite(sec)) return '0 секунд'

    const hours = Math.floor(sec / 3600)
    const minutes = Math.floor((sec % 3600) / 60)
    const seconds = sec % 60

    const plural = (num, one, few, many) => {
        const n = Math.abs(num) % 100
        const n1 = n % 10
        if (n > 10 && n < 20) return many
        if (n1 > 1 && n1 < 5) return few
        if (n1 === 1) return one
        return many
    }

    let res = ''

    if (hours > 0)
        res += `${hours} ${plural(hours, i18n.t('helpdesk.hour1'), i18n.t('helpdesk.hour2'), i18n.t('helpdesk.hour3'))}`

    if (minutes > 0) {
        if (res) res += ' '
        res += `${minutes} ${plural(minutes, i18n.t('helpdesk.minute1'), i18n.t('helpdesk.minute2'), i18n.t('helpdesk.minute3'))}`
    }

    if (!res)
        res = `${seconds} ${plural(seconds, i18n.t('helpdesk.second1'), i18n.t('helpdesk.second2'), i18n.t('helpdesk.second3'))}`

    return res
}

export const clearLastTitle = () => {
    lastManualTitle = null
}

export const generateDeviceUUID = () => {
    let buid = localStorage.getItem('buid')
    if(!buid) {
        buid = new DeviceUUID().get()
        localStorage.setItem('buid', buid)
    }
    return buid
}

export const changePageTitle = title => {
    lastManualTitle = title
    setTimeout(() => {
        document.title = title + ` | ${getSiteName()}`
    }, 600)
}

export const restorePageTitle = () => {
    if (lastManualTitle) {
        setTimeout(() => {
            document.title = lastManualTitle + ` | ${getSiteName()}`
        }, 600)
    }
}

export const getDeviceType = () => {
    const ua = navigator.userAgent
    let type = 'desktop'

    if (/Mobi|Android|iPhone|iPod|BlackBerry|IEMobile|Opera Mini/i.test(ua)) {
        type = 'mobile'
    } else if (
        /iPad|Tablet|PlayBook|Silk/i.test(ua) ||
    (navigator.maxTouchPoints && navigator.maxTouchPoints > 1 && window.innerWidth > 768 && window.innerWidth <= 1024)
    ) {
        type = 'tablet'
    }

    return {
        type,
        isMobile: type === 'mobile',
        isTablet: type === 'tablet',
        isDesktop: type === 'desktop'
    }
}

export const replaceFlatArray = (array) => {
    let newArray = []
    array.forEach(item => {
        newArray.push(item)
        if(item.children && item.children.length) {
            newArray = newArray.concat(replaceFlatArray(item.children))
        }
    })
    return newArray
}

export const setWithExpiry = () => {
    const now = new Date()
    const time = now.getTime() + (1000 * 60 * 60 * 24)
    return now.getTime() + time
}

export const declOfNum = (n, text_forms) => {
    n = Math.abs(n) % 100; var n1 = n % 10;
    if (n > 10 && n < 20) { return text_forms[2]; }
    if (n1 > 1 && n1 < 5) { return text_forms[1]; }
    if (n1 === 1) { return text_forms[0]; }
    return text_forms[2];
}

export const checkNameType = (file) => {
    const types = ['.jpg', '.jpeg', '.png', '.gif']
    let res = false
    types.forEach(item => {
        if(file.name.includes(item))
            res = true
    })
    return res
}

export const isFileImage = (file) => {
    return file && file['type'].split('/')[0] === 'image'
}

const isImageFileType = (type) => {
    return !!type && type.indexOf('image/') === 0;
}

export const previewImage = (file, size = 74) => {
    return new Promise(function (resolve) {
        if (!isImageFileType(file.type)) {
            resolve('');
            return;
        }

        var canvas = document.createElement('canvas');
        canvas.width = size;
        canvas.height = size;
        canvas.style.cssText = 'position: fixed; left: 0; top: 0; width: ' + size + 'px; height: ' + size + 'px; z-index: 9999; display: none;';
        document.body.appendChild(canvas);
        var ctx = canvas.getContext('2d');
        var img = new Image();
        img.onload = function () {
            var width = img.width,
                height = img.height;


            var drawWidth = size;
            var drawHeight = size;
            var offsetX = 0;
            var offsetY = 0;

            if (width < height) {
                drawHeight = height * (size / width);
                offsetY = -(drawHeight - drawWidth) / 2;
            } else {
                drawWidth = width * (size / height);
                offsetX = -(drawWidth - drawHeight) / 2;
            }

            ctx.drawImage(img, offsetX, offsetY, drawWidth, drawHeight);
            var dataURL = canvas.toDataURL();
            document.body.removeChild(canvas);

            resolve(dataURL);
        };
        img.src = window.URL.createObjectURL(file);
    })
}

export const also = (f) => (x) => {
    f(x)
    return x
}

export const extractData = ({ data }) => data

export const checkImageWidthHeight = (file) => {
    return new Promise(function (resolve) {
        let img = new Image();
        img.onload = function () {
            const width = img.width,
                height = img.height;

            resolve({width, height});
        };
        img.src = window.URL.createObjectURL(file);
    })
}

export const dataURItoBlob = (dataURI) => {
    // convert base64/URLEncoded data component to raw binary data held in a string
    var byteString;
    if (dataURI.split(',')[0].indexOf('base64') >= 0)
        byteString = atob(dataURI.split(',')[1]);
    else
        byteString = unescape(dataURI.split(',')[1]);

    // separate out the mime component
    var mimeString = dataURI.split(',')[0].split(':')[1].split(';')[0];

    // write the bytes of the string to a typed array
    var ia = new Uint8Array(byteString.length);
    for (var i = 0; i < byteString.length; i++) {
        ia[i] = byteString.charCodeAt(i);
    }

    return new Blob([ia], {type:mimeString});
}

export const hashString = (s) => {
    return s.split("").reduce(function(a,b){a=((a<<5)-a)+b.charCodeAt(0);return a&a},0)
}

export const getFileExtension = (filename) => {
    let ext = /^.+\.([^.]+)$/.exec(filename)
    return ext == null ? "" : ext[1]
}

export const sleep = (ms) => new Promise(r => setTimeout(r, ms))

/**
 * Example: addToDate(new Date(), 30, 'minutes') // returns 30 minutes from now.
 * https://stackoverflow.com/a/1214753/18511
 *
 * @param date  Date to start with
 * @param units  Number of units of the given interval to add.
 * @param interval  One of: years, quarters, months, weeks, days, hours, minutes, seconds
 */
export const addToDate = (date, units, interval) => {
    const ret = new Date(date)
    const checkRollover = () => {
        if(ret.getDate() !== date.getDate())
            ret.setDate(0)
    }

    switch(String(interval).toLowerCase()) {
    case 'years'   :  ret.setFullYear(ret.getFullYear() + units); checkRollover();  break
    case 'quarters':  ret.setMonth(ret.getMonth() + 3*units); checkRollover();  break
    case 'months'  :  ret.setMonth(ret.getMonth() + units); checkRollover();  break
    case 'weeks'   :  ret.setDate(ret.getDate() + 7*units);  break
    case 'days'    :  ret.setDate(ret.getDate() + units);  break
    case 'hours'   :  ret.setTime(ret.getTime() + units*3600000);  break
    case 'minutes' :  ret.setTime(ret.getTime() + units*60000);  break
    case 'seconds' :  ret.setTime(ret.getTime() + units*1000);  break
    default       :  ret = undefined;  break
    }
    return ret;
}

export const areSameDate = (d1, d2) => {
    return d1.getFullYear() === d2.getFullYear()
        && d1.getMonth() === d2.getMonth()
        && d1.getDate() === d2.getDate()
}

const timeFormatOptions = {
    hour: 'numeric',
    minute: 'numeric',
}
const dateFormatOptions = {
    month: 'short',
    day: 'numeric',
    useWordsWhenPossible: true,
}
const dateTimeFormatOptions = merge(
    dateFormatOptions,
    timeFormatOptions,
)

export const formatIntervalShort = (start, end) => {
    if (areSameDate(start, end)) {
        const date = formatDateTime(start, {
            useWordsWhenPossible: true,
        })
        const timeInterval = formatInterval(
            start, end, timeFormatOptions
        )

        return `${date}, ${timeInterval}`
    }

    const sameYear = start.year === end.year
    const isCurrentYear = sameYear
        && start.year === Date().year

    return formatInterval(start, end, {
        ...dateTimeFormatOptions,
        year: isCurrentYear ? undefined : 'numeric',
        month: isCurrentYear ? 'short' : '2-digit',
    })
}

export const formatInterval =
    (start, end, options) => {
        const f = formatDateTime

        return `${f(start, options)} - ${f(end, options)}`
    }
export const formatTime = (d) => {
    return formatDateTime(d, timeFormatOptions)
}

const formatDateUsingWords = (d, options) => {
    const today = new Date()
    const tomorrow = addToDate(today, 1, 'days')
    const yesterday = addToDate(today, -1, 'days')
    const dateOptions = {
        year: options.year,
        month: options.month,
        day: options.day,
        useWordsWhenPossible: false,
    }
    const timeOptions = {
        hour: options.hour,
        minute: options.minute,
        second: options.second,
        useWordsWhenPossible: false,
    }

    const date = areSameDate(d, today)
        ? i18n.t('today')
        : areSameDate(d, tomorrow)
            ? i18n.t('tomorrow')
            : areSameDate(d, yesterday)
                ? i18n.t('yesterday')
                : formatDateTime(d, dateOptions)
    const time = formatDateTime(d, timeOptions)

    return time.length === 0 ? date : date + ", " + time
}

export const mergeForm = (base, override) => {
    const isObj = v => v && Object.prototype.toString.call(v) === '[object Object]'
    const isArr = v => Array.isArray(v)

    const walk = (a, b) => {
        if (!a && !b) return undefined
        if (b && isObj(b) && b.display === false) return undefined

        if (isArr(a) || isArr(b)) return b !== undefined ? b : a

        if (isObj(a) || isObj(b)) {
            const out = {}
            const keys = new Set([
                ...Object.keys(a || {}),
                ...Object.keys(b || {})
            ])
            keys.forEach(k => {
                const v = walk(a ? a[k] : undefined, b ? b[k] : undefined)
                if (v !== undefined) out[k] = v
            })
            return Object.keys(out).length ? out : undefined
        }

        return b !== undefined ? b : a
    }

    const res = walk(base, override)
    return res || {}
}

export const formatDateTime =
    (d, options = dateTimeFormatOptions) => {
        if (options.useWordsWhenPossible) {
            return formatDateUsingWords(d, options)
        }

        if ( isNil(options.year)
        && ( isNil(options.month) )
        && ( isNil(options.day) )
        && ( isNil(options.hour) )
        && ( isNil(options.minute) )
        && ( isNil(options.second) ))
            return ""

        return d.toLocaleString(i18n.locale, options)
    }

export const replaceDate = (datetime, d) =>
    moment(datetime)
        .set('year', d.year())
        .set('month', d.month())
        .set('date', d.date())
        .toDate()

export const replaceTime = (datetime, t) =>
    moment(datetime)
        .set('hour', t.hour())
        .set('minute', t.minute())
        .toDate()
