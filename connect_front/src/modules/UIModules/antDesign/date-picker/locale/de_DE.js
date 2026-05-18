import _extends from 'babel-runtime/helpers/extends';
import CalendarLocale from 'ant-design-vue/es/ant-design-vue/es/vc-calendar/src/locale/de_DE';
import TimePickerLocale from 'ant-design-vue/es/ant-design-vue/es/time-picker/locale/de_DE';

// Merge into a locale object
var locale = {
    lang: _extends({
        placeholder: 'Datum auswählen',
        rangePlaceholder: ['Startdatum', 'Enddatum']
    }, CalendarLocale),
    timePickerLocale: _extends({}, TimePickerLocale)
};

// All settings at:
// https://github.com/ant-design/ant-design/issues/424

export default locale;