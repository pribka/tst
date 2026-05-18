import _mergeJSXProps from 'babel-helper-vue-jsx-merge-props'
import _extends from 'babel-runtime/helpers/extends'
import ClearableLabeledInput from './ClearableLabeledInput'
import ResizableTextArea from './ResizableTextArea'
import inputProps from './inputProps'
import hasProp, { getListeners, getOptionProps } from 'ant-design-vue/es/_util/props-util'
import { ConfigConsumerProps } from 'ant-design-vue/es/config-provider/configConsumerProps'
import { fixControlledValue, resolveOnChange } from './Input'
import PropTypes from 'ant-design-vue/es/_util/vue-types'
import omit from 'omit.js'

var TextAreaProps = {
    ...Object.keys(inputProps)
        .filter(key => key !== 'inputType')
        .reduce((obj, key) => {
            obj[key] = inputProps[key]
            return obj
        }, {}),
    autosize: PropTypes.oneOfType([Object, Boolean]),
    autoSize: PropTypes.oneOfType([Object, Boolean]),
    inputType: PropTypes.oneOf(['default', 'ghost', 'bg']) // ← твой кастомный
}

export default {
    name: 'ATextarea',
    inheritAttrs: false,
    model: {
        prop: 'value',
        event: 'change.value'
    },
    props: _extends({}, TextAreaProps),
    inject: {
        configProvider: { default: () => ConfigConsumerProps }
    },
    data() {
        const value = typeof this.value === 'undefined' ? this.defaultValue : this.value
        return {
            stateValue: typeof value === 'undefined' ? '' : value
        }
    },
    watch: {
        value(val) {
            this.stateValue = val
        }
    },
    mounted() {
        this.$nextTick(() => {
            if (this.autoFocus) {
                this.focus()
            }
        })
    },
    methods: {
        setValue(value, callback) {
            if (!hasProp(this, 'value')) {
                this.stateValue = value
                this.$nextTick(() => {
                    if (callback) callback()
                })
            }
        },
        handleKeyDown(e) {
            if (e.keyCode === 13) {
                this.$emit('pressEnter', e)
            }
            this.$emit('keydown', e)
        },
        onChange(e) {
            this.$emit('change.value', e.target.value)
            this.$emit('change', e)
            this.$emit('input', e)
        },
        handleChange(e) {
            const { value, composing } = e.target
            if ((e.isComposing || composing) && this.lazy || this.stateValue === value) return

            this.setValue(value, () => {
                this.$refs.resizableTextArea.resizeTextarea()
            })
            resolveOnChange(this.$refs.resizableTextArea.$refs.textArea, e, this.onChange)
        },
        focus() {
            this.$refs.resizableTextArea.$refs.textArea.focus()
        },
        blur() {
            this.$refs.resizableTextArea.$refs.textArea.blur()
        },
        handleReset(e) {
            this.setValue('', () => {
                this.$refs.resizableTextArea.renderTextArea()
                this.focus()
            })
            resolveOnChange(this.$refs.resizableTextArea.$refs.textArea, e, this.onChange)
        },
        renderTextArea(prefixCls) {
            const h = this.$createElement
            const props = getOptionProps(this)

            const resizeProps = {
                props: _extends({}, props, {
                    prefixCls,
                    inputType: this.inputType
                }),
                on: _extends({}, getListeners(this), {
                    input: this.handleChange,
                    keydown: this.handleKeyDown
                }),
                attrs: this.$attrs
            }

            return h(ResizableTextArea, _mergeJSXProps([resizeProps, { ref: 'resizableTextArea' }]))
        }
    },
    render(h) {
        const { stateValue, prefixCls: customizePrefixCls } = this
        const getPrefixCls = this.configProvider.getPrefixCls
        const prefixCls = getPrefixCls('input', customizePrefixCls)

        const props = {
            props: _extends({}, getOptionProps(this), {
                prefixCls,
                inputType: this.inputType,
                value: fixControlledValue(stateValue),
                element: this.renderTextArea(prefixCls),
                handleReset: this.handleReset
            }),
            on: getListeners(this)
        }

        return h(ClearableLabeledInput, props)
    }
}