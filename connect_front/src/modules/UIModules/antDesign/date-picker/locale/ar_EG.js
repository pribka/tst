import _extends from 'babel-runtime/helpers/extends';
import CalendarLocale from 'ant-design-vue/es/ant-design-vue/es/vc-calendar/src/locale/ar_EG';
import TimePickerLocale from 'ant-design-vue/es/ant-design-vue/es/time-picker/locale/ar_EG';

// Merge into a locale object
var locale = {
    lang: _extends({
        placeholder: 'اختيار التاريخ',
        rangePlaceholder: ['البداية', 'النهاية']
    }, CalendarLocale),
    timePickerLocale: _extends({}, TimePickerLocale),
    dateFormat: 'DD-MM-YYYY',
    monthFormat: 'MM-YYYY',
    dateTimeFormat: 'DD-MM-YYYY HH:mm:ss',
    weekFormat: 'wo-YYYY'
};

// All settings at:
// https://github.com/ant-design/ant-design/blob/master/components/date-picker/locale/example.json

export default locale;