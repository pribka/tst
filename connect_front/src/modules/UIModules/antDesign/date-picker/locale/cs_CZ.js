import _extends from 'babel-runtime/helpers/extends';
import CalendarLocale from 'ant-design-vue/es/ant-design-vue/es/vc-calendar/src/locale/cs_CZ';
import TimePickerLocale from 'ant-design-vue/es/ant-design-vue/es/time-picker/locale/cs_CZ';

// Merge into a locale object
var locale = {
    lang: _extends({
        placeholder: 'Vybrat datum',
        rangePlaceholder: ['Od', 'Do']
    }, CalendarLocale),
    timePickerLocale: _extends({}, TimePickerLocale)
};

// All settings at:
// https://github.com/ant-design/ant-design/blob/master/components/date-picker/locale/example.json

export default locale;