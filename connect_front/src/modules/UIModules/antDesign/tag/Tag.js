import _mergeJSXProps from 'babel-helper-vue-jsx-merge-props';
import _defineProperty from 'babel-runtime/helpers/defineProperty';
import PropTypes from 'ant-design-vue/es/_util/vue-types';
import Icon from 'ant-design-vue/es/icon';
import getTransitionProps from 'ant-design-vue/es/_util/getTransitionProps';
import omit from 'omit.js';
import Wave from 'ant-design-vue/es/_util/wave';
import { hasProp, getListeners, getOptionProps } from 'ant-design-vue/es/_util/props-util';
import BaseMixin from 'ant-design-vue/es/_util/BaseMixin';
import { ConfigConsumerProps } from 'ant-design-vue/es/config-provider/configConsumerProps';
import warning from 'ant-design-vue/es/_util/warning';

var PresetColorTypes = ['pink', 'red', 'yellow', 'orange', 'cyan', 'green', 'blue', 'purple', 'geekblue', 'magenta', 'volcano', 'gold', 'lime', 'grey', 'brown'];
var PresetColorRegex = new RegExp('^(' + PresetColorTypes.join('|') + ')(-inverse)?$');

export default {
    name: 'ATag',
    mixins: [BaseMixin],
    model: {
        prop: 'visible',
        event: 'close.visible'
    },
    props: {
        prefixCls: PropTypes.string,
        color: PropTypes.string,
        closable: PropTypes.bool.def(false),
        contrastText: PropTypes.bool.def(false),
        visible: PropTypes.bool,
        afterClose: PropTypes.func,
        useTextColor: PropTypes.bool.def(true),
        block: PropTypes.bool.def(false),
        size: PropTypes.oneOf(['small', 'large', 'default']).def('default')
    },
    inject: {
        configProvider: { 'default': function _default() {
            return ConfigConsumerProps;
        } }
    },
    data: function data() {
        var _visible = true;
        var props = getOptionProps(this);
        if ('visible' in props) {
            _visible = this.visible;
        }
        warning(!('afterClose' in props), 'Tag', "'afterClose' will be deprecated, please use 'close' event, we will remove this in the next version.");
        return {
            _visible: _visible
        };
    },

    watch: {
        visible: function visible(val) {
            this.setState({
                _visible: val
            });
        }
    },
    methods: {
        setVisible: function setVisible(visible, e) {
            this.$emit('close', e);
            this.$emit('close.visible', false);
            var afterClose = this.afterClose;
            if (afterClose) {
                // next version remove.
                afterClose();
            }
            if (e.defaultPrevented) {
                return;
            }
            if (!hasProp(this, 'visible')) {
                this.setState({ _visible: visible });
            }
        },
        handleIconClick: function handleIconClick(e) {
            e.stopPropagation();
            this.setVisible(false, e);
        },
        isPresetColor: function isPresetColor() {
            var color = this.$props.color;

            if (!color) {
                return false;
            }
            return PresetColorRegex.test(color);
        },
        getTagStyle: function getTagStyle() {
            var color = this.$props.color;

            var isPresetColor = this.isPresetColor();
            var contrastText = this.$props.contrastText;
            return {
                backgroundColor: color && !isPresetColor ? color : undefined,
                color: contrastText && !isPresetColor ? this.getTextColorClass(color) : undefined
            };
        },
        getTextColorClass: function getTextColorClass(backgroundColor) {
            if (!backgroundColor || backgroundColor === 'default') {
                return "#000";
            }
            const c = backgroundColor.substring(1);
            const rgb = parseInt(c, 16);
            const r = (rgb >> 16) & 0xff;
            const g = (rgb >> 8) & 0xff;
            const b = (rgb >> 0) & 0xff;

            const luma = 0.299 * r + 0.587 * g + 0.114 * b;
            return luma < 180 ? "#fff" : "#000";
        },
        getTagClassName: function getTagClassName(prefixCls) {
            var _ref

            var color = this.$props.color
            var useTextColor = this.$props.useTextColor
            var block = this.$props.block
            var size = this.$props.size
            var sizeCls = '';
            switch (size) {
            case 'large':
                sizeCls = 'lg';
                break;
            case 'small':
                sizeCls = 'sm';
                break;
            default:
                break;
            }

            var isPresetColor = this.isPresetColor()
            return _ref = {}, 
            _defineProperty(_ref, prefixCls, true), 
            _defineProperty(_ref, prefixCls + '-' + color, isPresetColor), 
            _defineProperty(_ref, prefixCls + '-' + sizeCls, sizeCls), 
            _defineProperty(_ref, prefixCls + '-has-color', color && !isPresetColor), 
            _defineProperty(_ref, prefixCls + '-text-color', useTextColor === true), 
            _defineProperty(_ref, prefixCls + '-block', block === true), 
            _ref
        },
        renderCloseIcon: function renderCloseIcon() {
            var h = this.$createElement;
            var closable = this.$props.closable;

            return closable ? h('i', {
                attrs: { type: 'close', class: 'fi fi-rr-cross-small icon-close' },
                on: {
                    'click': this.handleIconClick
                }
            }) : null;
        }
    },

    render: function render() {
        var h = arguments[0];
        var customizePrefixCls = this.$props.prefixCls;

        var getPrefixCls = this.configProvider.getPrefixCls;
        var prefixCls = getPrefixCls('tag', customizePrefixCls);
        var visible = this.$data._visible;

        var tag = h(
            'span',
            _mergeJSXProps([{
                directives: [{
                    name: 'show',
                    value: visible
                }]
            }, { on: omit(getListeners(this), ['close']) }, {
                'class': this.getTagClassName(prefixCls),
                style: this.getTagStyle()
            }]),
            [this.$slots['default'], this.renderCloseIcon()]
        );
        var transitionProps = getTransitionProps(prefixCls + '-zoom', {
            appear: false
        });
        return h(Wave, [h(
            'transition',
            transitionProps,
            [tag]
        )]);
    }
};