import _defineProperty from 'babel-runtime/helpers/defineProperty';
import _extends from 'babel-runtime/helpers/extends';
import classNames from 'classnames';
import Dialog from 'ant-design-vue/es/vc-dialog';
import PropTypes from 'ant-design-vue/es/_util/vue-types';
import addEventListener from 'ant-design-vue/es/vc-util/Dom/addEventListener';
import { getConfirmLocale } from './locale';
import Button from 'ant-design-vue/es/button';
import buttonTypes from 'ant-design-vue/es/button/buttonTypes';
var ButtonType = buttonTypes().type;
import LocaleReceiver from 'ant-design-vue/es/locale-provider/LocaleReceiver';
import { initDefaultProps, getComponentFromProp, getClass, getStyle, mergeProps, getListeners } from 'ant-design-vue/es/_util/props-util';
import { ConfigConsumerProps } from 'ant-design-vue/es/config-provider/configConsumerProps';
import { v1 as uuidv1 } from 'uuid';

var mousePosition = null;
// ref: https://github.com/ant-design/ant-design/issues/15795
var getClickPosition = function getClickPosition(e) {
    mousePosition = {
        x: e.pageX,
        y: e.pageY
    };
    // 100ms 内发生过点击事件，则从点击位置动画展示
    // 否则直接 zoom 展示
    // 这样可以兼容非点击方式展开
    setTimeout(function () {
        return mousePosition = null;
    }, 100);
};

// 只有点击事件支持从鼠标位置动画展开
if (typeof window !== 'undefined' && window.document && window.document.documentElement) {
    addEventListener(document.documentElement, 'click', getClickPosition, true);
}

function noop() {}
var modalProps = function modalProps() {
    var defaultProps = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : {};

    var props = {
        prefixCls: PropTypes.string,
        /** 对话框是否可见*/
        visible: PropTypes.bool,
        /** 确定按钮 loading*/
        confirmLoading: PropTypes.bool,
        /** 标题*/
        title: PropTypes.any,
        /** 是否显示右上角的关闭按钮*/
        closable: PropTypes.bool,
        closeIcon: PropTypes.any,
        /** 点击确定回调*/
        // onOk: (e: React.MouseEvent<any>) => void,
        /** 点击模态框右上角叉、取消按钮、Props.maskClosable 值为 true 时的遮罩层或键盘按下 Esc 时的回调*/
        // onCancel: (e: React.MouseEvent<any>) => void,
        afterClose: PropTypes.func.def(noop),
        afterVisibleChange: PropTypes.func.def(noop),
        /** 垂直居中 */
        centered: PropTypes.bool,
        /** 宽度*/
        width: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
        /** 底部内容*/
        footer: PropTypes.any,
        /** 确认按钮文字*/
        okText: PropTypes.any,
        /** 确认按钮类型*/
        okType: ButtonType,
        /** 取消按钮文字*/
        cancelText: PropTypes.any,
        icon: PropTypes.any,
        /** 点击蒙层是否允许关闭*/
        maskClosable: PropTypes.bool,
        /** 强制渲染 Modal*/
        forceRender: PropTypes.bool,
        okButtonProps: PropTypes.object,
        cancelButtonProps: PropTypes.object,
        destroyOnClose: true,
        wrapClassName: PropTypes.string,
        maskTransitionName: PropTypes.string,
        transitionName: PropTypes.string,
        getContainer: PropTypes.func,
        hardZIndex: PropTypes.number,
        bodyStyle: PropTypes.object,
        maskStyle: PropTypes.object,
        mask: PropTypes.bool,
        keyboard: PropTypes.bool,
        wrapProps: PropTypes.object,
        isConfirm: PropTypes.bool.def(false),
        focusTriggerAfterClose: PropTypes.bool,
        dialogStyle: PropTypes.object.def(function () {
            return {};
        })
    };
    return initDefaultProps(props, defaultProps);
};

export var destroyFns = [];

export default {
    name: 'AModal',
    inheritAttrs: false,
    model: {
        prop: 'visible',
        event: 'change'
    },
    props: modalProps({
        width: 520,
        transitionName: 'zoom',
        maskTransitionName: 'fade',
        confirmLoading: false,
        visible: false,
        okType: 'primary'
    }),
    data: function data() {
        return {
            sVisible: !!this.visible,
            modalUid: uuidv1(),
        };
    },

    computed: {
        zIndex() {
            if (this.hardZIndex) { return this.hardZIndex }

            if(this.$store?.state) {
                const openDrawers = this.$store.state.openDrawers
                const currentDrawer = openDrawers.find(drawer => drawer.uid === this.modalUid)
                return currentDrawer?.zIndex || openDrawers?.[openDrawers.length-1]?.zIndex + 100 || 1000
            }
            return 999999
        }
    },

    watch: {
        visible: function visible(val) {
            this.sVisible = val;
            if(!this.isConfirm) {
                if(val) {
                    this.$store.commit('PUSH_OPEN_DRAWERS', this.modalUid)
                } else {
                    this.$store.commit('REMOVE_OPEN_DRAWERS', this.modalUid)
                }
            }

            setTimeout(() => {
                this.$emit('afterVisibleChange', val)
            }, 400)
        }
    },
    inject: {
        configProvider: { 'default': function _default() {
            return ConfigConsumerProps;
        } }
    },
    // static info: ModalFunc;
    // static success: ModalFunc;
    // static error: ModalFunc;
    // static warn: ModalFunc;
    // static warning: ModalFunc;
    // static confirm: ModalFunc;
    methods: {
        handleCancel: function handleCancel(e) {
            this.$emit('cancel', e);
            this.$emit('change', false);
        },
        handleOk: function handleOk(e) {
            this.$emit('ok', e);
        },
        renderFooter: function renderFooter(locale) {
            var h = this.$createElement;
            var okType = this.okType,
                confirmLoading = this.confirmLoading;

            var cancelBtnProps = mergeProps({ on: { click: this.handleCancel } }, this.cancelButtonProps || {});
            var okBtnProps = mergeProps({
                on: { click: this.handleOk },
                props: {
                    type: okType,
                    loading: confirmLoading
                }
            }, this.okButtonProps || {});
            return h('div', [h(
                Button,
                cancelBtnProps,
                [getComponentFromProp(this, 'cancelText') || locale.cancelText]
            ), h(
                Button,
                okBtnProps,
                [getComponentFromProp(this, 'okText') || locale.okText]
            )]);
        }
    },

    mounted() {
        if(this.visible && this.$store?.state && !this.isConfirm)
            this.$store.commit('PUSH_OPEN_DRAWERS', this.modalUid)
    },

    beforeDestroy() {
        if(this.$store?.state) {
            const openDrawers = this.$store.state.openDrawers
            const find = openDrawers.find(drawer => drawer.uid === this.modalUid)
            if(find)
                this.$store.commit('REMOVE_OPEN_DRAWERS', this.modalUid)
        }
    },

    render: function render() {
        var h = arguments[0];
        var customizePrefixCls = this.prefixCls,
            visible = this.sVisible,
            wrapClassName = this.wrapClassName,
            centered = this.centered,
            getContainer = this.getContainer,
            $slots = this.$slots,
            $scopedSlots = this.$scopedSlots,
            $attrs = this.$attrs;

        var children = $scopedSlots['default'] ? $scopedSlots['default']() : $slots['default'];
        var _configProvider = this.configProvider,
            getPrefixCls = _configProvider.getPrefixCls,
            getContextPopupContainer = _configProvider.getPopupContainer;

        var prefixCls = getPrefixCls('modal', customizePrefixCls);

        var defaultFooter = h(LocaleReceiver, {
            attrs: {
                componentName: 'Modal',
                defaultLocale: getConfirmLocale()
            },
            scopedSlots: { 'default': this.renderFooter }
        });
        var closeIcon = getComponentFromProp(this, 'closeIcon');
        var closeIconToRender = h(
            'span',
            { 'class': prefixCls + '-close-x' },
            [closeIcon || h('i', { 'class': prefixCls + '-close-icon flaticon fi fi-rr-cross-small', attrs: { type: 'close' }
            })]
        );
        var footer = getComponentFromProp(this, 'footer');
        var title = getComponentFromProp(this, 'title');
        var dialogProps = {
            props: _extends({}, this.$props, {
                getContainer: getContainer === undefined ? getContextPopupContainer : getContainer,
                prefixCls: prefixCls,
                wrapClassName: classNames(_defineProperty({}, prefixCls + '-centered', !!centered), wrapClassName),
                title: title,
                footer: footer === undefined ? defaultFooter : footer,
                visible: visible,
                mousePosition: mousePosition,
                closeIcon: closeIconToRender,
                zIndex: this.zIndex
            }),
            on: _extends({}, getListeners(this), {
                close: this.handleCancel
            }),
            'class': getClass(this),
            style: getStyle(this),
            attrs: $attrs
        };
        return h(
            Dialog,
            dialogProps,
            [children]
        );
    }
};