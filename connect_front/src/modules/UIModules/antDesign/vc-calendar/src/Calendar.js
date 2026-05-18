import _extends from 'babel-runtime/helpers/extends'
import PropTypes from 'ant-design-vue/es/_util/vue-types'
import BaseMixin from 'ant-design-vue/es/_util/BaseMixin'
import { getOptionProps, hasProp, getComponentFromProp } from 'ant-design-vue/es/_util/props-util'
import { cloneElement } from 'ant-design-vue/es/_util/vnode'
import KeyCode from 'ant-design-vue/es/_util/KeyCode'
import moment from 'moment'
import DateTable from './date/DateTable'
import CalendarHeader from './calendar/CalendarHeader'
import CalendarFooter from './calendar/CalendarFooter'
import CalendarMixin, { getNowByCurrentStateValue } from './mixin/CalendarMixin'
import CommonMixin from './mixin/CommonMixin'
import DateInput from './date/DateInput'
import ruRU from './locale/ru_RU'
import { getTimeConfig, getTodayTime, syncTime } from './util'
import { goStartMonth, goEndMonth, goTime as _goTime } from './util/toTime'

var getMomentObjectIfValid = function getMomentObjectIfValid(date) {
    if (moment.isMoment(date) && date.isValid()) {
        return date
    }
    return false
}

var Calendar = {
    name: 'Calendar',
    props: {
        locale: PropTypes.object.def(ruRU),
        format: PropTypes.oneOfType([PropTypes.string, PropTypes.arrayOf(PropTypes.string), PropTypes.func]),
        visible: PropTypes.bool.def(true),
        prefixCls: PropTypes.string.def('rc-calendar'),
        defaultValue: PropTypes.object,
        value: PropTypes.object,
        selectedValue: PropTypes.object,
        defaultSelectedValue: PropTypes.object,
        mode: PropTypes.oneOf(['time', 'date', 'month', 'year', 'decade']),
        showDateInput: PropTypes.bool.def(true),
        showWeekNumber: PropTypes.bool,
        showToday: PropTypes.bool.def(true),
        showOk: PropTypes.bool,
        timePicker: PropTypes.any,
        dateInputPlaceholder: PropTypes.any,
        disabledDate: PropTypes.func,
        disabledTime: PropTypes.any,
        dateRender: PropTypes.func,
        renderFooter: PropTypes.func.def(function () {
            return null
        }),
        renderSidebar: PropTypes.func.def(function () {
            return null
        }),
        clearIcon: PropTypes.any,
        focusablePanel: PropTypes.bool.def(true),
        inputMode: PropTypes.string,
        inputReadOnly: PropTypes.bool,
        mask: PropTypes.oneOfType([PropTypes.bool, PropTypes.object]).def(false)
    },

    mixins: [BaseMixin, CommonMixin, CalendarMixin],

    data: function data() {
        var props = this.$props
        var storeIsMobile = this.$store && this.$store.state && this.$store.state.isMobile
        return {
            sMode: this.mode || 'date',
            sValue: getMomentObjectIfValid(props.value) || getMomentObjectIfValid(props.defaultValue) || moment(),
            sSelectedValue: props.selectedValue || props.defaultSelectedValue,
            sShowTimePanel: !!props.timePicker && !storeIsMobile
        }
    },

    watch: {
        mode: function mode(val) {
            this.setState({ sMode: val })
        },
        value: function value(val) {
            this.setState({
                sValue: getMomentObjectIfValid(val) || getMomentObjectIfValid(this.defaultValue) || getNowByCurrentStateValue(this.sValue)
            })
        },
        selectedValue: function selectedValue(val) {
            this.setState({
                sSelectedValue: val
            })
        },
        timePicker: function timePicker(val) {
            var isMobile = this.isMobile
            this.setState({
                sShowTimePanel: !!val && !isMobile
            })
        }
    },
    mounted: function mounted() {
        var _this = this

        this.$nextTick(function () {
            _this.saveFocusElement(DateInput.getInstance())
        })
    },

    computed: {
        isMobile: function isMobile() {
            return this.$store && this.$store.state && !!this.$store.state.isMobile
        }
    },

    methods: {
        onPanelChange: function onPanelChange(value, mode) {
            var sValue = this.sValue
            if (!hasProp(this, 'mode')) {
                if (mode === 'time') {
                    if (this.isMobile) {
                        this.setState({ sMode: 'time' })
                    }
                } else {
                    this.setState({ sMode: mode })
                }
            }
            this.__emit('panelChange', value || sValue, mode)
        },
        onKeyDown: function onKeyDown(event) {
            if (event.target.nodeName.toLowerCase() === 'input') {
                return undefined
            }
            var keyCode = event.keyCode
            var ctrlKey = event.ctrlKey || event.metaKey
            var disabledDate = this.disabledDate
            var value = this.sValue

            switch (keyCode) {
            case KeyCode.DOWN:
                this.goTime(1, 'weeks')
                event.preventDefault()
                return 1
            case KeyCode.UP:
                this.goTime(-1, 'weeks')
                event.preventDefault()
                return 1
            case KeyCode.LEFT:
                if (ctrlKey) {
                    this.goTime(-1, 'years')
                } else {
                    this.goTime(-1, 'days')
                }
                event.preventDefault()
                return 1
            case KeyCode.RIGHT:
                if (ctrlKey) {
                    this.goTime(1, 'years')
                } else {
                    this.goTime(1, 'days')
                }
                event.preventDefault()
                return 1
            case KeyCode.HOME:
                this.setValue(goStartMonth(value))
                event.preventDefault()
                return 1
            case KeyCode.END:
                this.setValue(goEndMonth(value))
                event.preventDefault()
                return 1
            case KeyCode.PAGE_DOWN:
                this.goTime(1, 'month')
                event.preventDefault()
                return 1
            case KeyCode.PAGE_UP:
                this.goTime(-1, 'month')
                event.preventDefault()
                return 1
            case KeyCode.ENTER:
                if (!disabledDate || !disabledDate(value)) {
                    this.onSelect(value, {
                        source: 'keyboard'
                    })
                }
                event.preventDefault()
                return 1
            default:
                this.__emit('keydown', event)
                return 1
            }
        },
        onClear: function onClear() {
            this.onSelect(null)
            this.__emit('clear')
        },
        onOk: function onOk() {
            var sSelectedValue = this.sSelectedValue

            if (this.isAllowedDate(sSelectedValue)) {
                this.__emit('ok', sSelectedValue)
            }
        },
        onDateInputChange: function onDateInputChange(value) {
            this.onSelect(value, {
                source: 'dateInput'
            })
        },
        onDateInputSelect: function onDateInputSelect(value) {
            this.onSelect(value, {
                source: 'dateInputSelect'
            })
        },
        onDateTableSelect: function onDateTableSelect(value) {
            var timePicker = this.timePicker
            var sSelectedValue = this.sSelectedValue

            if (!sSelectedValue && timePicker) {
                var timePickerProps = getOptionProps(timePicker)
                var timePickerDefaultValue = timePickerProps.defaultValue
                if (timePickerDefaultValue) {
                    syncTime(timePickerDefaultValue, value)
                }
            }
            this.onSelect(value)
        },
        onToday: function onToday() {
            var sValue = this.sValue

            var now = getTodayTime(sValue)
            this.onSelect(now, {
                source: 'todayButton'
            })
        },
        onBlur: function onBlur(event) {
            var _this2 = this

            setTimeout(function () {
                var dateInput = DateInput.getInstance()
                var rootInstance = _this2.rootInstance

                if (!rootInstance || rootInstance.contains(document.activeElement) || dateInput && dateInput.contains(document.activeElement)) {
                    return
                }

                _this2.$emit('blur', event)
            }, 0)
        },
        getRootDOMNode: function getRootDOMNode() {
            return this.$el
        },
        openTimePicker: function openTimePicker() {
            if (this.isMobile) {
                this.onPanelChange(null, 'time')
            } else {
                this.setState({ sShowTimePanel: true })
            }
        },
        closeTimePicker: function closeTimePicker() {
            if (this.isMobile) {
                this.onPanelChange(null, 'date')
            } else {
                this.setState({ sShowTimePanel: false })
            }
        },
        goTime: function goTime(direction, unit) {
            this.setValue(_goTime(this.sValue, direction, unit))
        }
    },

    render: function render() {
        var h = arguments[0]
        var locale = this.locale
        var prefixCls = this.prefixCls
        var disabledDate = this.disabledDate
        var dateInputPlaceholder = this.dateInputPlaceholder
        var timePicker = this.timePicker
        var disabledTime = this.disabledTime
        var showDateInput = this.showDateInput
        var sValue = this.sValue
        var sSelectedValue = this.sSelectedValue
        var sMode = this.sMode
        var renderFooter = this.renderFooter
        var inputMode = this.inputMode
        var inputReadOnly = this.inputReadOnly
        var monthCellRender = this.monthCellRender
        var monthCellContentRender = this.monthCellContentRender
        var mask = this.mask
        var props = this.$props

        var clearIcon = getComponentFromProp(this, 'clearIcon')
        var isMobile = this.isMobile
        var headerShowTimeFlag = isMobile ? sMode === 'time' : false
        var timePanelEnabled = !!timePicker
        var showTimePanel = (isMobile ? sMode === 'time' : this.sShowTimePanel) && timePanelEnabled
        var disabledTimeConfig = showTimePanel && disabledTime && timePicker ? getTimeConfig(sSelectedValue || sValue, disabledTime) : null

        var timePickerEle = null
        if (timePicker) {
            var timePickerOriginProps = getOptionProps(timePicker)
            var timePickerProps = {
                props: _extends({
                    showHour: true,
                    showSecond: true,
                    showMinute: true
                }, timePickerOriginProps, disabledTimeConfig, {
                    value: sSelectedValue || sValue,
                    disabledTime: disabledTime
                }),
                on: {
                    change: this.onDateInputChange
                }
            }

            if (timePickerOriginProps.defaultValue !== undefined) {
                timePickerProps.props.defaultOpenValue = timePickerOriginProps.defaultValue
            }
            timePickerEle = cloneElement(timePicker, timePickerProps)
        }

        var dateInputWrap = null
        if (showDateInput) {
            var di = h(DateInput, {
                attrs: {
                    format: this.getFormat(),
                    value: sValue,
                    locale: locale,
                    placeholder: dateInputPlaceholder,
                    showClear: true,
                    disabledTime: disabledTime,
                    disabledDate: disabledDate,
                    prefixCls: prefixCls,
                    selectedValue: sSelectedValue,
                    clearIcon: clearIcon,
                    inputMode: inputMode,
                    inputReadOnly: inputReadOnly,
                    mask: mask
                },
                key: 'date-input',
                on: {
                    clear: this.onClear,
                    change: this.onDateInputChange,
                    select: this.onDateInputSelect
                }
            })

            dateInputWrap = h('div', { class: prefixCls + '-input-wrap-panel' }, [
                h('div', { class: prefixCls + '-date-input-wrap' }, [di]),
                h('div', { class: prefixCls + '-extra-actions' }, [
                    h('i', {
                        class: 'fi fi-rr-cross-small',
                        on: {
                            click: () => {
                                const val = this.sSelectedValue || this.sValue
                                if (this.timePicker) {
                                    this.onOk()
                                } else {
                                    this.onSelect(val, { source: 'customClose' })
                                }
                            }
                        }
                    })
                ])
            ])
        }

        var children = []
        if (props.renderSidebar) {
            children.push(props.renderSidebar())
        }
        children.push(h(
            'div',
            { 'class': prefixCls + '-panel', key: 'panel' },
            [dateInputWrap, h(
                'div',
                {
                    attrs: { tabIndex: props.focusablePanel ? 0 : undefined },
                    'class': prefixCls + '-date-panel' },
                [h(CalendarHeader, {
                    attrs: {
                        locale: locale,
                        mode: sMode,
                        value: sValue,
                        disabledMonth: disabledDate,
                        renderFooter: renderFooter,
                        showTimePicker: headerShowTimeFlag,
                        prefixCls: prefixCls,
                        monthCellRender: monthCellRender,
                        monthCellContentRender: monthCellContentRender
                    },
                    on: {
                        'valueChange': this.setValue,
                        'panelChange': this.onPanelChange
                    }
                }), h(
                    'div',
                    { 'class': prefixCls + '-main-with-time' },
                    [h(
                        'div',
                        { 'class': prefixCls + '-body' },
                        [h(DateTable, {
                            attrs: {
                                locale: locale,
                                value: sValue,
                                selectedValue: sSelectedValue,
                                prefixCls: prefixCls,
                                dateRender: props.dateRender,
                                disabledDate: disabledDate,
                                showWeekNumber: props.showWeekNumber
                            },
                            on: {
                                'select': this.onDateTableSelect
                            }
                        })]
                    ), showTimePanel ? h(
                        'div',
                        { 'class': prefixCls + '-time-picker' },
                        [h(
                            'div',
                            { 'class': prefixCls + '-time-picker-panel' },
                            [timePickerEle]
                        )]
                    ) : null]
                ), h(CalendarFooter, {
                    attrs: {
                        showOk: props.showOk,
                        mode: sMode,
                        renderFooter: props.renderFooter,
                        locale: locale,
                        prefixCls: prefixCls,
                        showToday: props.showToday,
                        disabledTime: disabledTime,
                        showTimePicker: headerShowTimeFlag,
                        showDateInput: props.showDateInput,
                        timePicker: timePicker,
                        selectedValue: sSelectedValue,
                        timePickerDisabled: !(sSelectedValue || sValue),
                        value: sValue,
                        disabledDate: disabledDate,
                        okDisabled: props.showOk !== false && (!(sSelectedValue || sValue) || !this.isAllowedDate(sSelectedValue || sValue))
                    },
                    on: {
                        'ok': this.onOk,
                        'select': this.onSelect,
                        'today': this.onToday,
                        'openTimePicker': this.openTimePicker,
                        'closeTimePicker': this.closeTimePicker
                    }
                })]
            )]
        ))

        var rootClass = props.showWeekNumber ? prefixCls + '-week-number' : ''
        if (!this.isMobile) {
            rootClass = (rootClass + ' ' + prefixCls + '-pc').trim()
        }

        return this.renderRoot({
            children: children,
            'class': rootClass
        })
    }
}

export default Calendar