import _extends from 'babel-runtime/helpers/extends'
import RcDropdown from 'ant-design-vue/es/vc-dropdown/src/index'
import DropdownButton from './dropdown-button'
import PropTypes from 'ant-design-vue/es/_util/vue-types'
import { cloneElement } from 'ant-design-vue/es/_util/vnode'
import { getOptionProps, getPropsData, getComponentFromProp, getListeners } from 'ant-design-vue/es/_util/props-util'
import getDropdownProps from './getDropdownProps'
import { ConfigConsumerProps } from 'ant-design-vue/es/config-provider/configConsumerProps'

let timer
var DropdownProps = getDropdownProps()
var Dropdown = {
    name: 'ADropdown',

    props: _extends({}, DropdownProps, {
        prefixCls: PropTypes.string,
        mouseEnterDelay: PropTypes.number.def(0.15),
        mouseLeaveDelay: PropTypes.number.def(0.1),
        placement: DropdownProps.placement.def('bottomLeft')
    }),

    model: {
        prop: 'visible',
        event: 'visibleChange'
    },

    data: function () {
        return {
            dropdownUid: 'dropdown_' + Math.random().toString(36).slice(2),
            zIndex: 1050,
            innerVisible: false,
            scrollParents: [],
            onAnyScroll: null,
            ignoreScrollUntil: 0,
            bindScrollTimer: null,
            closeScrollTimer: null
        }
    },

    provide: function provide() {
        return {
            savePopupRef: this.savePopupRef
        }
    },

    inject: {
        configProvider: { 'default': function _default() {
            return ConfigConsumerProps
        } }
    },

    computed: {
        isVisibleControlled() {
            const pd = this.$options && this.$options.propsData
            return !!(pd && Object.prototype.hasOwnProperty.call(pd, 'visible'))
        },
        currentVisible() {
            return this.isVisibleControlled ? this.visible : this.innerVisible
        }
    },

    watch: {
        visible(val) {
            if (this.isVisibleControlled) {
                if (!this.trigger.length) {
                    if (val) {
                        this.$store.commit('PUSH_OPEN_DRAWERS', this.dropdownUid)
                        this.initZIndex()
                    } else {
                        this.$store.commit('REMOVE_OPEN_DRAWERS', this.dropdownUid)
                        clearTimeout(timer)
                        timer = setTimeout(() => {
                            this.initZIndex()
                        }, 300)
                    }
                }

                if (val) {
                    this.bindCloseOnScroll()
                } else {
                    this.unbindCloseOnScroll()
                }
            }
        }
    },

    beforeDestroy() {
        this.unbindCloseOnScroll()
    },

    methods: {
        closeDropdown() {
            if (!this.currentVisible) return

            if (!this.isVisibleControlled) {
                this.innerVisible = false
            }

            this.handleVisibleChange(false)
            this.$emit('visibleChange', false)
        },

        bindCloseOnScroll() {
            this.unbindCloseOnScroll()

            const triggerEl = this.getTriggerEl()
            if (!triggerEl) return

            clearTimeout(this.bindScrollTimer)
            clearTimeout(this.closeScrollTimer)

            const now = Date.now()
            this.ignoreScrollUntil = now + 300

            this.onAnyScroll = (e) => {
                if (Date.now() < this.ignoreScrollUntil) return
                if (e && e.type !== 'scroll') return

                const t = e && e.target
                const popupEl = this.popupRef && (this.popupRef.$el || this.popupRef)

                if (popupEl && t && popupEl.contains && popupEl.contains(t)) return

                clearTimeout(this.closeScrollTimer)
                this.closeScrollTimer = setTimeout(() => {
                    this.closeDropdown()
                }, 80)
            }

            this.scrollParents = this.getScrollParents(triggerEl)

            this.bindScrollTimer = setTimeout(() => {
                this.scrollParents.forEach(p => {
                    p.addEventListener('scroll', this.onAnyScroll, { passive: true, capture: true })
                })

                window.addEventListener('scroll', this.onAnyScroll, { passive: true, capture: true })
            }, 60)
        },

        unbindCloseOnScroll() {
            clearTimeout(this.bindScrollTimer)
            clearTimeout(this.closeScrollTimer)

            if (!this.onAnyScroll) return

            this.scrollParents.forEach(p => {
                p.removeEventListener('scroll', this.onAnyScroll, { capture: true })
            })
            this.scrollParents = []

            window.removeEventListener('scroll', this.onAnyScroll, { capture: true })

            this.onAnyScroll = null
        },

        getTriggerEl() {
            const vnodes = this.$slots && this.$slots['default']
            const vnode = Array.isArray(vnodes) ? vnodes[0] : vnodes
            if (vnode && vnode.elm) return vnode.elm

            const root = this.$el
            if (!root) return null

            const customizePrefixCls = this.$props && this.$props.prefixCls
            const getPrefixCls = this.configProvider.getPrefixCls
            const prefixCls = getPrefixCls('dropdown', customizePrefixCls)

            return root.querySelector('.' + prefixCls + '-trigger') || root
        },

        getScrollParents(el) {
            const res = []
            let node = el && el.parentNode

            const isScrollable = (n) => {
                if (!n || n === document || n === document.documentElement) return false
                const style = window.getComputedStyle(n)
                const overflowY = style.overflowY
                const overflowX = style.overflowX
                const canScrollY = (overflowY === 'auto' || overflowY === 'scroll') && n.scrollHeight > n.clientHeight
                const canScrollX = (overflowX === 'auto' || overflowX === 'scroll') && n.scrollWidth > n.clientWidth
                return canScrollY || canScrollX
            }

            while (node && node !== document.body) {
                if (isScrollable(node)) res.push(node)
                node = node.parentNode
            }

            res.push(document)
            return res
        },

        initZIndex() {
            const openDrawers = this.$store.state.openDrawers
            const currentDrawer = openDrawers.find(drawer => drawer.uid === this.dropdownUid)
            if (currentDrawer) {
                this.zIndex = currentDrawer?.zIndex || openDrawers?.[openDrawers.length - 1]?.zIndex + 100 || 1000
            }
        },

        savePopupRef: function savePopupRef(ref) {
            this.popupRef = ref
        },

        getTransitionName: function getTransitionName() {
            var _$props = this.$props,
                _$props$placement = _$props.placement,
                placement = _$props$placement === undefined ? '' : _$props$placement,
                transitionName = _$props.transitionName

            if (transitionName !== undefined) {
                return transitionName
            }
            if (placement.indexOf('top') >= 0) {
                return 'slide-down'
            }
            return 'slide-up'
        },

        handleVisibleChange: function (val) {
            if (this.$store) {
                if (val) {
                    this.$store.commit('PUSH_OPEN_DRAWERS', this.dropdownUid)
                } else {
                    this.$store.commit('REMOVE_OPEN_DRAWERS', this.dropdownUid)
                }
                this.initZIndex()
            }

            if (val) {
                this.bindCloseOnScroll()
            } else {
                this.unbindCloseOnScroll()
            }
        },

        renderOverlay: function renderOverlay(prefixCls) {
            var h = this.$createElement

            var overlay = getComponentFromProp(this, 'overlay')
            var overlayNode = Array.isArray(overlay) ? overlay[0] : overlay
            var overlayProps = overlayNode && getPropsData(overlayNode)

            var _ref = overlayProps || {},
                _ref$selectable = _ref.selectable,
                selectable = _ref$selectable === undefined ? false : _ref$selectable,
                _ref$focusable = _ref.focusable,
                focusable = _ref$focusable === undefined ? true : _ref$focusable

            var expandIcon = h(
                'span',
                { 'class': prefixCls + '-menu-submenu-arrow' },
                [h('i', {
                    attrs: { type: 'right' },
                    'class': prefixCls + '-menu-submenu-arrow-icon fi fi-rr-angle-small-right' })]
            )

            if (overlayNode && overlayNode.componentOptions) {
                const prevOn = (overlayNode.componentOptions && overlayNode.componentOptions.listeners) || {}

                return cloneElement(overlayNode, {
                    props: {
                        mode: 'vertical',
                        selectable: selectable,
                        focusable: focusable,
                        expandIcon: expandIcon
                    },
                    on: _extends({}, prevOn, {
                        click: (e) => {
                            if (prevOn.click) prevOn.click(e)
                            this.closeDropdown()
                        }
                    })
                })
            }

            return overlay
        }
    },

    render: function render() {
        var h = arguments[0]
        var $slots = this.$slots

        var props = getOptionProps(this)
        var customizePrefixCls = props.prefixCls,
            trigger = props.trigger,
            disabled = props.disabled,
            getPopupContainer = props.getPopupContainer

        var getContextPopupContainer = this.configProvider.getPopupContainer
        var getPrefixCls = this.configProvider.getPrefixCls
        var prefixCls = getPrefixCls('dropdown', customizePrefixCls)

        var dropdownTrigger = cloneElement($slots['default'], {
            'class': prefixCls + '-trigger',
            props: {
                disabled: disabled
            }
        })

        var triggerActions = disabled ? [] : trigger
        var alignPoint
        if (triggerActions && triggerActions.indexOf('contextmenu') !== -1) {
            alignPoint = true
        }

        var mergedProps = _extends({
            alignPoint: alignPoint,
            overlayStyle: {
                zIndex: this.zIndex
            }
        }, props, {
            prefixCls: prefixCls,
            getPopupContainer: getPopupContainer || getContextPopupContainer,
            transitionName: this.getTransitionName(),
            trigger: triggerActions
        })

        if (!this.isVisibleControlled) {
            mergedProps.visible = this.innerVisible
        }

        var dropdownProps = {
            props: mergedProps,
            on: _extends({}, getListeners(this), {
                visibleChange: (val) => {
                    if (!this.isVisibleControlled) {
                        this.innerVisible = val
                    }
                    this.handleVisibleChange(val)
                    this.$emit('visibleChange', val)
                }
            })
        }

        return h(
            RcDropdown,
            dropdownProps,
            [dropdownTrigger, h(
                'template',
                { slot: 'overlay' },
                [this.renderOverlay(prefixCls)]
            )]
        )
    }
}

Dropdown.Button = DropdownButton
export default Dropdown
export { DropdownProps }