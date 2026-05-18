import _mergeJSXProps from 'babel-helper-vue-jsx-merge-props'
import PropTypes from 'ant-design-vue/es/_util/vue-types'
import BaseMixin from 'ant-design-vue/es/_util/BaseMixin'
import { getComponentFromProp } from 'ant-design-vue/es/_util/props-util'
import moment from 'moment'
import { formatDate } from '../util'
import KeyCode from 'ant-design-vue/es/_util/KeyCode'

var DateInput = {
    mixins: [BaseMixin],
    props: {
        prefixCls: PropTypes.string,
        timePicker: PropTypes.object,
        value: PropTypes.object,
        disabledTime: PropTypes.any,
        format: PropTypes.oneOfType([PropTypes.string, PropTypes.arrayOf(PropTypes.string), PropTypes.func]),
        locale: PropTypes.object,
        disabledDate: PropTypes.func,
        placeholder: PropTypes.string,
        selectedValue: PropTypes.object,
        clearIcon: PropTypes.any,
        inputMode: PropTypes.string,
        inputReadOnly: PropTypes.bool,
        mask: PropTypes.oneOfType([PropTypes.bool, PropTypes.object]).def(false),
        useFocus: PropTypes.oneOfType([PropTypes.bool]).def(true),
    },

    data: function data() {
        var selectedValue = this.selectedValue
        return {
            str: formatDate(selectedValue, this.format),
            prevSelectedValue: selectedValue,
            invalid: false,
            hasFocus: false,
            _maskInstance: null,
            _dateInput: null,
            _cachedSelectionStart: null,
            _cachedSelectionEnd: null
        }
    },

    watch: {
        selectedValue: function selectedValue() {
            this.setState()
        },
        format: function format() {
            this.setState()
            this.rebindMask && this.rebindMask()
        },
        mask: function mask() {
            this.rebindMask && this.rebindMask()
        }
    },

    updated: function updated() {
        var _this = this
        this.$nextTick(function () {
            var di = _this._dateInput
            if (di && _this.$data.hasFocus && !_this.invalid && !(_this._cachedSelectionStart === 0 && _this._cachedSelectionEnd === 0)) {
                try {
                    di.setSelectionRange(_this._cachedSelectionStart, _this._cachedSelectionEnd)
                } catch (e) {}
            }
        })
    },
    beforeDestroy: function beforeDestroy() {
        this.detachMask()
        this._dateInput = null
    },
    mounted: function mounted() {
        if (!this.$store.state.isMobile && this.useFocus) {
            this.$nextTick(() => {
                this.focus()
            })
        }
    },
    getInstance: function getInstance() {
        return this._dateInput
    },

    methods: {
        getDerivedStateFromProps: function getDerivedStateFromProps(nextProps, state) {
            var newState = {}
            var di = this._dateInput
            if (di) {
                this._cachedSelectionStart = di.selectionStart
                this._cachedSelectionEnd = di.selectionEnd
            }
            var selectedValue = nextProps.selectedValue
            var selectedValueChanged = selectedValue !== state.prevSelectedValue || selectedValue && state.prevSelectedValue && !selectedValue.isSame(state.prevSelectedValue)
            if (!state.hasFocus || selectedValueChanged) {
                newState = {
                    str: formatDate(selectedValue, this.format),
                    prevSelectedValue: selectedValue,
                    invalid: false
                }
            }
            return newState
        },
        onClear: function onClear() {
            this.setState({
                str: ''
            })
            this.__emit('clear', null)
        },
        onInputChange: function onInputChange(e) {
            var _e$target = e.target,
                str = _e$target.value,
                composing = _e$target.composing
            var _str = this.str,
                oldStr = _str === undefined ? '' : _str

            if (e.isComposing || composing || oldStr === str) return

            var _$props = this.$props,
                disabledDate = _$props.disabledDate,
                format = _$props.format,
                selectedValue = _$props.selectedValue

            if (!str) {
                this.__emit('change', null)
                this.setState({
                    invalid: false,
                    str: str
                })
                return
            }

            var parsed = moment(str, format, true)
            var formatHasTime = typeof format === 'string' && /H|h|m|s/.test(format)
            var inputHasTime = /\d{1,2}:\d{2}/.test(str)
            if (!parsed.isValid()) {
                this.setState({
                    invalid: true,
                    str: str
                })
                return
            }

            var value = parsed.clone()
            try {
                if (
                    formatHasTime &&
                    !inputHasTime &&
                    this.value &&
                    this.value.isValid &&
                    this.value.isValid()
                ) {
                    value.hour(this.value.hour())
                        .minute(this.value.minute())
                        .second(this.value.second())
                }
            } catch (e) {}

            if (!value || disabledDate && disabledDate(value)) {
                this.setState({
                    invalid: true,
                    str: str
                })
                return
            }

            if (selectedValue !== value || selectedValue && value && !selectedValue.isSame(value)) {
                this.setState({
                    invalid: false,
                    str: str
                })
                this.__emit('change', value)
            }
        },
        onFocus: function onFocus() {
            this.setState({ hasFocus: true })
        },
        onBlur: function onBlur() {
            this.setState(function (prevState, prevProps) {
                return {
                    hasFocus: false,
                    str: formatDate(prevProps.selectedValue, prevProps.format)
                }
            })
        },
        onKeyDown: function onKeyDown(event) {
            var keyCode = event.keyCode
            var _$props2 = this.$props,
                value = _$props2.value,
                selectedValue = _$props2.selectedValue,
                disabledDate = _$props2.disabledDate

            if (keyCode === KeyCode.ENTER) {
                var validateValue = selectedValue || value
                var validateDate = !disabledDate || !disabledDate(validateValue)
                if (validateDate) {
                    this.__emit('select', validateValue.clone())
                }
                event.preventDefault()
            }
        },
        getRootDOMNode: function getRootDOMNode() {
            return this.$el
        },
        focus: function focus() {
            var di = this._dateInput
            if (!di) return
            try {
                var prevReadOnly = di.readOnly
                if (di.readOnly) di.readOnly = false

                var maskEl = null
                try {
                    if (this._maskInstance) {
                        maskEl = this._maskInstance.el || this._maskInstance.input || null
                    }
                } catch (err) {}

                var target = maskEl || di

                setTimeout(function () {
                    try {
                        if (typeof target.focus === 'function') target.focus()
                        if (typeof target.setSelectionRange === 'function') {
                            var len = (target.value || '').length
                            try { target.setSelectionRange(len, len) } catch (e) {}
                        }
                    } catch (err) {
                        console.warn('focus attempt failed', err)
                    } finally {
                        try { if (prevReadOnly) di.readOnly = prevReadOnly } catch (e) {}
                    }
                }, 10)
            } catch (err) {
                console.warn('focus wrapper error', err)
            }
        },
        saveDateInput: function saveDateInput(dateInput) {
            this._dateInput = dateInput
            this.rebindMask && this.rebindMask()
        },
        attachMask: async function attachMask() {
            if (!this.mask || !this._dateInput) return
            try {
                var IMaskModule = await import('imask')
                var IMask = IMaskModule && IMaskModule.default ? IMaskModule.default : IMaskModule
                if (this._maskInstance) {
                    try {
                        this._maskInstance.destroy()
                    } catch (e) {}
                    this._maskInstance = null
                }

                var options = null
                if (typeof this.mask === 'object' && this.mask.mask) {
                    options = this.mask
                } else if (this.mask === true) {
                    options = this.buildIMaskDateOptions(this.format, IMask)
                } else {
                    return
                }

                this._maskInstance = IMask(this._dateInput, options)
                var self = this
                this._maskInstance.on('accept', function () {
                    var v = self._maskInstance.value
                    self.setState({ str: v })
                    var parsed = moment(v, self.format, true)
                    if (parsed.isValid()) {
                        var value = parsed.clone()

                        try {
                            var formatHasTime = typeof self.format === 'string' && /H|h|m|s/.test(self.format)
                            if (!formatHasTime) {
                                if (self.value && self.value.isValid && self.value.isValid()) {
                                    value.hour(self.value.hour()).minute(self.value.minute()).second(self.value.second())
                                } else if (self.value instanceof Date) {
                                    var vv = moment(self.value)
                                    if (vv.isValid()) value.hour(vv.hour()).minute(vv.minute()).second(vv.second())
                                }
                            }
                        } catch (err) {
                            console.error('DateInput.attachMask accept copy-time error', err)
                        }

                        if (!(self.disabledDate && self.disabledDate(value))) {
                            self.__emit('change', value)
                        }
                    }
                })
                this._maskInstance.on('complete', function () {
                    try {
                        self._maskInstance.updateValue()
                    } catch (e) {}
                })
            } catch (err) {}
        },

        buildIMaskDateOptions: function buildIMaskDateOptions(formatStr, IMask) {
            if (!formatStr) {
                return { mask: Number }
            }
            var pattern = ''
            var blocks = {}
            var i = 0
            var tokenOrder = []
            var tokenMap = [
                { tk: 'DD', name: 'd', len: 2 },
                { tk: 'D', name: 'd', len: 1 },
                { tk: 'MM', name: 'm', len: 2 },
                { tk: 'M', name: 'm', len: 1 },
                { tk: 'YYYY', name: 'Y', len: 4 },
                { tk: 'YY', name: 'Y', len: 2 },
                { tk: 'HH', name: 'h', len: 2 },
                { tk: 'H', name: 'h', len: 1 },
                { tk: 'mm', name: 'i', len: 2 },
                { tk: 'm', name: 'i', len: 1 },
                { tk: 'ss', name: 's', len: 2 },
                { tk: 's', name: 's', len: 1 }
            ]
            while (i < formatStr.length) {
                var matched = false
                for (var t = 0; t < tokenMap.length; t++) {
                    var tk = tokenMap[t].tk
                    if (formatStr.substr(i, tk.length) === tk) {
                        var name = tokenMap[t].name
                        pattern += name
                        tokenOrder.push({ token: tk, name: name })
                        i += tk.length
                        matched = true
                        break
                    }
                }
                if (!matched) {
                    var ch = formatStr[i]
                    pattern += ch
                    i += 1
                }
            }

            blocks.d = {
                mask: IMask.MaskedRange,
                from: 1,
                to: 31,
                maxLength: 2
            }
            blocks.m = {
                mask: IMask.MaskedRange,
                from: 1,
                to: 12,
                maxLength: 2
            }
            blocks.Y = {
                mask: IMask.MaskedRange,
                from: 1900,
                to: 9999,
                maxLength: 4
            }
            blocks.h = {
                mask: IMask.MaskedRange,
                from: 0,
                to: 23,
                maxLength: 2
            }
            blocks.i = {
                mask: IMask.MaskedRange,
                from: 0,
                to: 59,
                maxLength: 2
            }
            blocks.s = {
                mask: IMask.MaskedRange,
                from: 0,
                to: 59,
                maxLength: 2
            }

            return {
                mask: Date,
                pattern: pattern,
                lazy: true,
                autofix: true,
                blocks: blocks,
                format: function (date) {
                    return moment(date).format(formatStr)
                },
                parse: function (str) {
                    var dt = moment(str, formatStr, true)
                    return dt.isValid() ? dt.toDate() : new Date(NaN)
                }
            }
        },
        detachMask: function detachMask() {
            if (this._maskInstance) {
                try {
                    this._maskInstance.destroy()
                } catch (e) {}
                this._maskInstance = null
            }
        },
        rebindMask: function rebindMask() {
            this.detachMask()
            this.$nextTick(function () {
                try {
                    this._dateInput && this.attachMask()
                } catch (e) {
                    this._dateInput && this.attachMask()
                }
            }.bind(this))
        },
        formatToIMask: function formatToIMask(formatStr) {
            if (!formatStr) {
                return { mask: Number }
            }
            var tokenMap = {
                YYYY: '0000',
                YY: '00',
                MM: '00',
                M: '0',
                DD: '00',
                D: '0',
                HH: '00',
                H: '0',
                mm: '00',
                m: '0',
                ss: '00',
                s: '0'
            }
            var tokens = Object.keys(tokenMap).sort(function (a, b) {
                return b.length - a.length
            })
            var out = ''
            var i = 0
            while (i < formatStr.length) {
                var matched = false
                for (var t = 0; t < tokens.length; t++) {
                    var tk = tokens[t]
                    if (formatStr.substr(i, tk.length) === tk) {
                        out += tokenMap[tk]
                        i += tk.length
                        matched = true
                        break
                    }
                }
                if (!matched) {
                    out += formatStr[i]
                    i += 1
                }
            }
            return { mask: out }
        }
    },

    render: function render() {
        var h = arguments[0]
        var invalid = this.invalid,
            str = this.str,
            locale = this.locale,
            prefixCls = this.prefixCls,
            placeholder = this.placeholder,
            disabled = this.disabled,
            showClear = this.showClear,
            inputMode = this.inputMode,
            inputReadOnly = this.inputReadOnly

        var clearIcon = getComponentFromProp(this, 'clearIcon')
        var invalidClass = invalid ? prefixCls + '-input-invalid' : ''
        return h(
            'div',
            { 'class': prefixCls + '-input-wrap' },
            [h(
                'div',
                { 'class': prefixCls + '-date-input-wrap' },
                [h('input', _mergeJSXProps([{
                    directives: [{
                        name: 'ant-ref',
                        value: this.saveDateInput
                    }, {
                        name: 'ant-input'
                    }]
                }, {
                    'class': prefixCls + '-input ' + invalidClass,
                    domProps: {
                        'value': str
                    },
                    attrs: {
                        disabled: disabled,
                        placeholder: placeholder,
                        inputMode: inputMode,
                        readOnly: inputReadOnly
                    },
                    on: {
                        'input': this.onInputChange,
                        'keydown': this.onKeyDown,
                        'focus': this.onFocus,
                        'blur': this.onBlur
                    }
                }]))]
            ), showClear ? h(
                'a',
                {
                    attrs: { role: 'button', title: locale.clear },
                    on: {
                        'click': this.onClear
                    }
                },
                [clearIcon || h('span', { 'class': prefixCls + '-clear-btn' })]
            ) : null]
        )
    }
}

export default DateInput
