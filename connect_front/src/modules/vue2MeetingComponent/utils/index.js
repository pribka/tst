import moment from 'moment'
import { i18n } from '@/config/i18n-setup'

export const declOfNum = (n, text_forms) => {
    n = Math.abs(n) % 100; var n1 = n % 10;
    if (n > 10 && n < 20) { return text_forms[2]; }
    if (n1 > 1 && n1 < 5) { return text_forms[1]; }
    if (n1 === 1) { return text_forms[0]; }
    return text_forms[2];
}

export const durationFormat = (duration) => {
    const getTimeFromMins = (mins) => {
        if (mins >= 24 * 60 || mins < 0) {
            throw new RangeError("Valid input should be greater than or equal to 0 and less than 1440.");
        }
        const h = mins / 60 | 0,
            m = mins % 60 | 0,
            times = moment.utc().hours(h).minutes(m)

        if(times.format("mm") === '00') {
            return times.format(`HH ${declOfNum(Number(times.format(`HH`)),
                [i18n.t('meeting.hour'), i18n.t('meeting.hours'), i18n.t('meeting.of_hours')])}`)
        } else {
            return times.format(`HH ${declOfNum(Number(times.format(`HH`)), [i18n.t('meeting.hour'), i18n.t('meeting.hours'), i18n.t('meeting.of_hours')])} mm ${declOfNum(Number(times.format(`mm`)), [i18n.t('meeting.minute'), i18n.t('meeting.minutes'), i18n.t('meeting.of_minutes')])}`)
        }
    }

    if(duration > 59) {
        return getTimeFromMins(duration)
    } else {
        return `${duration} ${declOfNum(duration, [i18n.t('meeting.minute'), i18n.t('meeting.minutes'), i18n.t('meeting.of_minutes')])}`
    }
}