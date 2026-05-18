import _extends from 'babel-runtime/helpers/extends';
// import { TimePickerProps } from 'ant-design-vue/es/time-picker'
import PropTypes from 'ant-design-vue/es/_util/vue-types';
import { TimesType, TimeType } from '@apps/UIModules/antDesign/moment-util.js';

export var PickerProps = function PickerProps() {
    return {
        name: PropTypes.string,
        transitionName: PropTypes.string,
        prefixCls: PropTypes.string,
        inputPrefixCls: PropTypes.string,
        format: PropTypes.oneOfType([PropTypes.string, PropTypes.array, PropTypes.func]),
        disabled: PropTypes.bool,
        allowClear: PropTypes.bool,
        suffixIcon: PropTypes.any,
        prefixIcon: PropTypes.any,
        iconPosition: PropTypes.oneOf(['left', 'default']),
        popupStyle: PropTypes.object,
        dropdownClassName: PropTypes.string,
        locale: PropTypes.any,
        localeCode: PropTypes.string,
        size: PropTypes.oneOf(['large', 'small', 'default']),
        inputType: PropTypes.oneOf(['ghost', 'default']),
        getCalendarContainer: PropTypes.func,
        open: PropTypes.bool,
        // onOpenChange: PropTypes.(status: bool) => void,
        disabledDate: PropTypes.func,
        showToday: PropTypes.bool,
        dateRender: PropTypes.any, // (current: moment.Moment, today: moment.Moment) => React.ReactNode,
        pickerClass: PropTypes.string,
        pickerInputClass: PropTypes.string,
        timePicker: PropTypes.any,
        autoFocus: PropTypes.bool,
        tagPrefixCls: PropTypes.string,
        tabIndex: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
        align: PropTypes.object.def(function () {
            return {};
        }),
        inputReadOnly: PropTypes.bool,
        valueFormat: PropTypes.string
    };
};

export var SinglePickerProps = function SinglePickerProps() {
    return {
        value: TimeType,
        defaultValue: TimeType,
        defaultPickerValue: TimeType,
        renderExtraFooter: PropTypes.any,
        placeholder: PropTypes.string
    // onChange?: (date: moment.Moment, dateString: string) => void;
    };
};

export var DatePickerProps = function DatePickerProps() {
    return _extends({}, PickerProps(), SinglePickerProps(), {
        showTime: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
        open: PropTypes.bool,
        mask: {
            type: [Boolean, Object],
            default: true
        },
        disabledTime: PropTypes.func,
        // onOpenChange?: (status: bool) => void;
        // onOk?: (selectedTime: moment.Moment) => void;
        mode: PropTypes.oneOf(['time', 'date', 'month', 'year', 'decade'])
    });
};

export var MonthPickerProps = function MonthPickerProps() {
    return _extends({}, PickerProps(), SinglePickerProps(), {
        placeholder: PropTypes.string,
        monthCellContentRender: PropTypes.func
    });
};
// export const RangePickerPresetRange = PropTypes.oneOfType([TimesType, PropTypes.func])

export var RangePickerProps = function RangePickerProps() {
    return _extends({}, PickerProps(), {
        tagPrefixCls: PropTypes.string,
        value: TimesType,
        defaultValue: TimesType,
        defaultPickerValue: TimesType,
        timePicker: PropTypes.any,
        // onChange?: (dates: TimesType, dateStrings: [string, string]) => void;
        // onCalendarChange?: (dates: TimesType, dateStrings: [string, string]) => void;
        // onOk?: (selectedTime: moment.Moment) => void;
        showTime: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
        ranges: PropTypes.object,
        placeholder: PropTypes.arrayOf(String),
        mode: PropTypes.oneOfType([PropTypes.string, PropTypes.arrayOf(String)]),
        separator: PropTypes.any,
        disabledTime: PropTypes.func,
        showToday: PropTypes.bool,
        renderExtraFooter: PropTypes.any,
        mask: {
            type: [Boolean, Object],
            default: false
        }
    // onPanelChange?: (value?: TimesType, mode?: string | string[]) => void;
    });
};

export var WeekPickerProps = function WeekPickerProps() {
    return _extends({}, PickerProps(), SinglePickerProps(), {
        placeholder: PropTypes.string
    });
};

// export interface DatePickerDecorator extends React.ClassicComponentClass<DatePickerProps> {
//   RangePicker: React.ClassicComponentClass<RangePickerProps>;
//   MonthPicker: React.ClassicComponentClass<MonthPickerProps>;
//   WeekPicker: React.ClassicComponentClass<WeexPickerProps>;
// }