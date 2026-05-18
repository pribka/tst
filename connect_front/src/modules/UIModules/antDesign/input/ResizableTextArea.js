import _mergeJSXProps from 'babel-helper-vue-jsx-merge-props'
import _defineProperty from 'babel-runtime/helpers/defineProperty'
import _extends from 'babel-runtime/helpers/extends'
import ResizeObserver from 'ant-design-vue/es/vc-resize-observer'
import omit from 'omit.js'
import classNames from 'classnames'
import calculateNodeHeight from './calculateNodeHeight'
import raf from 'ant-design-vue/es/_util/raf'
import warning from 'ant-design-vue/es/_util/warning'
import BaseMixin from 'ant-design-vue/es/_util/BaseMixin'
import inputProps from './inputProps'
import PropTypes from 'ant-design-vue/es/_util/vue-types'
import { getOptionProps, getListeners } from 'ant-design-vue/es/_util/props-util'

var RESIZE_STATUS_NONE = 0
var RESIZE_STATUS_RESIZING = 1
var RESIZE_STATUS_RESIZED = 2

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

var ResizableTextArea = {
    name: 'ResizableTextArea',
    props: TextAreaProps,
    data() {
        return {
            textareaStyles: {},
            resizeStatus: RESIZE_STATUS_NONE
        }
    },
    mixins: [BaseMixin],
    mounted() {
        this.$nextTick(() => {
            this.resizeTextarea()
        })
    },
    beforeDestroy() {
        raf.cancel(this.nextFrameActionId)
        raf.cancel(this.resizeFrameId)
    },
    watch: {
        value() {
            this.$nextTick(() => {
                this.resizeTextarea()
            })
        }
    },
    methods: {
        handleResize(size) {
            if (this.resizeStatus !== RESIZE_STATUS_NONE) return
            this.$emit('resize', size)
            if (this.autoSize) {
                this.resizeOnNextFrame()
            }
        },
        resizeOnNextFrame() {
            raf.cancel(this.nextFrameActionId)
            this.nextFrameActionId = raf(this.resizeTextarea)
        },
        resizeTextarea() {
            const autoSize = this.autoSize || this.autosize
            if (!autoSize || !this.$refs.textArea) return

            const { minRows, maxRows } = autoSize
            const textareaStyles = calculateNodeHeight(this.$refs.textArea, false, minRows, maxRows)

            this.setState({ textareaStyles, resizeStatus: RESIZE_STATUS_RESIZING }, () => {
                raf.cancel(this.resizeFrameId)
                this.resizeFrameId = raf(() => {
                    this.setState({ resizeStatus: RESIZE_STATUS_RESIZED }, () => {
                        this.resizeFrameId = raf(() => {
                            this.setState({ resizeStatus: RESIZE_STATUS_NONE })
                            this.fixFirefoxAutoScroll()
                        })
                    })
                })
            })
        },
        fixFirefoxAutoScroll() {
            try {
                if (document.activeElement === this.$refs.textArea) {
                    const currentStart = this.$refs.textArea.selectionStart
                    const currentEnd = this.$refs.textArea.selectionEnd
                    this.$refs.textArea.setSelectionRange(currentStart, currentEnd)
                }
            } catch (e) {}
        },
        renderTextArea() {
            const h = this.$createElement
            const props = getOptionProps(this)
            const { prefixCls, autoSize, autosize, disabled, inputType } = props
            const { textareaStyles, resizeStatus } = this.$data

            warning(autosize === undefined, 'Input.TextArea', 'autosize is deprecated, please use autoSize instead.')

            const otherProps = omit(props, ['prefixCls', 'autoSize', 'autosize', 'defaultValue', 'allowClear', 'type', 'lazy', 'value', 'inputType'])

            const cls = classNames(
                prefixCls,
                _defineProperty({}, `${prefixCls}-disabled`, disabled),
                inputType === 'ghost' ? `${prefixCls}-ghost` : null,
                inputType === 'bg' ? `${prefixCls}-bg` : null
            )

            const domProps = {}
            if ('value' in props) {
                domProps.value = props.value || ''
            }

            const style = _extends({}, textareaStyles, resizeStatus === RESIZE_STATUS_RESIZING ? { overflowX: 'hidden', overflowY: 'hidden' } : null)

            const textareaProps = {
                attrs: otherProps,
                domProps,
                style,
                class: cls,
                on: omit(getListeners(this), 'pressEnter'),
                directives: [{ name: 'ant-input' }]
            }

            return h(
                ResizeObserver,
                {
                    on: { resize: this.handleResize },
                    attrs: { disabled: !(autoSize || autosize) }
                },
                [h('textarea', _mergeJSXProps([textareaProps, { ref: 'textArea' }]))]
            )
        }
    },
    render() {
        return this.renderTextArea()
    }
}

export default ResizableTextArea