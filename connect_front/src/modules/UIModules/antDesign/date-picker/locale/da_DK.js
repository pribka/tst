import _extends from 'babel-runtime/helpers/extends';
import CalendarLocale from 'ant-design-vue/es/ant-design-vue/es/vc-calendar/src/locale/da_DK';
import TimePickerLocale from 'ant-design-vue/es/ant-design-vue/es/time-picker/locale/da_DK';

// Merge into a locale object
var locale = {
    lang: _extends({
        placeholder: 'Vælg dato',
        rangePlaceholder: ['Startdato', 'Slutdato']
    }, CalendarLocale),
    timePickerLocale: _extends({}, TimePickerLocale)
};

// All settings at:
// https://github.com/ant-design/ant-design/blob/master/components/date-picker/locale/example.json

export default locale;