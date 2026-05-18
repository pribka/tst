import DateConstants from './DateConstants'
import moment from 'moment'

export default {
    functional: true,
    render(h, context) {
        const props = context.props
        const value = props.value

        const forcedLocale =
      (props.locale && (props.locale.locale || props.locale.lang && props.locale.lang.locale)) ||
      (value && value.locale && value.locale()) ||
      moment.locale()

        const base = (value ? value.clone() : moment()).locale(forcedLocale)
        const localeData = base.localeData()
        const prefixCls = props.prefixCls
        const veryShortWeekdays = []
        const weekDays = []
        const firstDayOfWeek = localeData.firstDayOfWeek()
        let showWeekNumberEl
        const now = base.clone()

        for (let i = 0; i < DateConstants.DATE_COL_COUNT; i++) {
            const index = (firstDayOfWeek + i) % DateConstants.DATE_COL_COUNT
            now.day(index)
            veryShortWeekdays[i] = localeData.weekdaysMin(now)
            weekDays[i] = localeData.weekdaysShort(now)
        }

        if (props.showWeekNumber) {
            showWeekNumberEl = h(
                'th',
                { attrs: { role: 'columnheader' }, class: prefixCls + '-column-header ' + prefixCls + '-week-number-header' },
                [h('span', { class: prefixCls + '-column-header-inner' }, ['x'])]
            )
        }

        const weekDaysEls = weekDays.map((day, xindex) =>
            h(
                'th',
                { key: xindex, attrs: { role: 'columnheader', title: day }, class: prefixCls + '-column-header' },
                [h('span', { class: prefixCls + '-column-header-inner' }, [veryShortWeekdays[xindex]])]
            )
        )

        return h('thead', [h('tr', { attrs: { role: 'row' } }, [showWeekNumberEl, weekDaysEls])])
    }
}