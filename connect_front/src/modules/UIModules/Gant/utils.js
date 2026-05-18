import moment from 'moment'

export const durationFormat = durationMin => {
    const duration = moment.duration(durationMin, 'minutes')
  
    const years = Math.floor(duration.asYears())
    const months = Math.floor(duration.asMonths()) % 12
    const weeks = Math.floor(duration.asWeeks()) % 4
    const days = Math.floor(duration.asDays()) % 7
    const hours = duration.hours()
    const minutes = duration.minutes()

    const parts = []
    if (years > 0) parts.push(`${years} ${getPlural(years, 'год', 'года', 'лет')}`)
    if (months > 0) parts.push(`${months} ${getPlural(months, 'месяц', 'месяца', 'месяцев')}`)
    if (weeks > 0) parts.push(`${weeks} ${getPlural(weeks, 'неделя', 'недели', 'недель')}`)
    if (days > 0) parts.push(`${days} ${getPlural(days, 'день', 'дня', 'дней')}`)
    if (hours > 0) parts.push(`${hours} ${getPlural(hours, 'час', 'часа', 'часов')}`)
    if (minutes > 0) parts.push(`${minutes} ${getPlural(minutes, 'минута', 'минуты', 'минут')}`)

    return parts.length > 0 ? parts.join(' ') : '0 минут'
}

export const shortDurationFormat = durationMin => {
    const duration = moment.duration(durationMin, 'minutes')
  
    const years = Math.floor(duration.asYears())
    const months = Math.floor(duration.asMonths()) % 12
    const weeks = Math.floor(duration.asWeeks()) % 4
    const days = Math.floor(duration.asDays()) % 7
    const hours = duration.hours()
    const minutes = duration.minutes()

    const parts = []
    if (years > 0) parts.push(`${years} г.`)
    if (months > 0) parts.push(`${months} мес.`)
    if (weeks > 0) parts.push(`${weeks} нед.`)
    if (days > 0) parts.push(`${days} д.`)
    if (hours > 0) parts.push(`${hours} ч.`)
    if (minutes > 0) parts.push(`${minutes} мин.`)

    return parts.length > 0 ? parts.join(' ') : '0 мин.'
}
  
function getPlural(number, one, few, many) {
    if (number % 10 === 1 && number % 100 !== 11) return one
    if ([2, 3, 4].includes(number % 10) && ![12, 13, 14].includes(number % 100)) return few
    return many
}

export const marks = {
    0: '',
    1: '',
    2: '',
    3: '',
    4: ''
}

export const injectData = {
    $calculate_duration: false,
    $no_start: false,
    $no_end: false
}