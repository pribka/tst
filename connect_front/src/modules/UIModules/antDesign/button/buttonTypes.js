import PropTypes from 'ant-design-vue/es/_util/vue-types';
export default (function () {
    return {
        prefixCls: PropTypes.string,
        type: PropTypes.string,
        htmlType: PropTypes.oneOf(['button', 'submit', 'reset']).def('button'),
        icon: PropTypes.any,
        shape: PropTypes.oneOf(['circle', 'circle-outline', 'round']),
        size: PropTypes.oneOf(['small', 'large', 'default']).def('default'),
        loading: PropTypes.oneOfType([PropTypes.bool, PropTypes.object]),
        disabled: PropTypes.bool,
        ghost: PropTypes.bool,
        block: PropTypes.bool,
        flaticon: PropTypes.bool.def(false),
        iconRight: PropTypes.bool.def(false),
        useTruncate: PropTypes.bool.def(false)
    };
});