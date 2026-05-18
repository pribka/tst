import _extends from 'babel-runtime/helpers/extends';
import CalendarLocale from 'ant-design-vue/es/ant-design-vue/es/vc-calendar/src/locale/el_GR';
import TimePickerLocale from 'ant-design-vue/es/ant-design-vue/es/time-picker/locale/el_GR';

// Merge into a locale object
var locale = {
    lang: _extends({
        placeholder: 'Επιλέξτε ημερομηνία',
        rangePlaceholder: ['Αρχική ημερομηνία', 'Τελική ημερομηνία']
    }, CalendarLocale),
    timePickerLocale: _extends({}, TimePickerLocale)
};

// All settings at:
// https://github.com/ant-design/ant-design/issues/424

export default locale;