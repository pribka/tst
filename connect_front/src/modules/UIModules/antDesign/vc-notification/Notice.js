import _defineProperty from 'babel-runtime/helpers/defineProperty';
import _extends from 'babel-runtime/helpers/extends';
import PropTypes from 'ant-design-vue/es/_util/vue-types';
import { getStyle, getComponentFromProp, getListeners } from 'ant-design-vue/es/_util/props-util';
import BaseMixin from 'ant-design-vue/es/_util/BaseMixin';

function noop() {}

var SWIPE_CLOSE_DISTANCE = 96;
var SWIPE_START_DISTANCE = 8;
var SWIPE_CLOSE_DURATION = 120;

export default {
    mixins: [BaseMixin],
    props: {
        duration: PropTypes.number.def(1.5),
        closable: PropTypes.bool,
        prefixCls: PropTypes.string,
        update: PropTypes.bool,
        closeIcon: PropTypes.any
    },
    data: function data() {
        return {
            swipeStartX: 0,
            swipeStartY: 0,
            swipeDeltaX: 0,
            swipeTracking: false,
            swipeDragging: false,
            swipeClosing: false,
            swipeMoved: false,
            swipeCloseTimer: null
        };
    },
    watch: {
        duration: function duration() {
            this.restartCloseTimer();
        }
    },

    mounted: function mounted() {
        this.startCloseTimer();
    },
    updated: function updated() {
        if (this.update) {
            this.restartCloseTimer();
        }
    },
    beforeDestroy: function beforeDestroy() {
        this.clearCloseTimer();
        this.clearSwipeCloseTimer();
        this.willDestroy = true; // beforeDestroy调用后依然会触发onMouseleave事件
    },

    methods: {
        getSwipePoint: function getSwipePoint(e) {
            var point = e.touches && e.touches.length ? e.touches[0] : e.changedTouches && e.changedTouches.length ? e.changedTouches[0] : e;
            return {
                x: point.clientX,
                y: point.clientY
            };
        },
        startSwipe: function startSwipe(e) {
            if (this.swipeClosing || e.button !== undefined && e.button !== 0) {
                return;
            }
            var point = this.getSwipePoint(e);
            this.swipeStartX = point.x;
            this.swipeStartY = point.y;
            this.swipeDeltaX = 0;
            this.swipeTracking = true;
            this.swipeDragging = false;
            this.swipeMoved = false;
            this.clearSwipeCloseTimer();
        },
        moveSwipe: function moveSwipe(e) {
            if (!this.swipeTracking || this.swipeClosing) {
                return;
            }

            var point = this.getSwipePoint(e);
            var diffX = point.x - this.swipeStartX;
            var diffY = point.y - this.swipeStartY;

            if (!this.swipeDragging) {
                if (Math.abs(diffX) < SWIPE_START_DISTANCE && Math.abs(diffY) < SWIPE_START_DISTANCE) {
                    return;
                }
                if (diffX <= 0 || Math.abs(diffY) > Math.abs(diffX)) {
                    this.cancelSwipe();
                    return;
                }
                this.swipeDragging = true;
                this.swipeMoved = true;
                this.clearCloseTimer();
            }

            this.swipeDeltaX = Math.max(0, diffX);
            if (e.cancelable !== false) {
                e.preventDefault();
            }
        },
        endSwipe: function endSwipe(e) {
            var _this = this;

            if (!this.swipeTracking) {
                return;
            }

            if (this.swipeDragging && this.swipeDeltaX >= SWIPE_CLOSE_DISTANCE) {
                if (e && e.stopPropagation) {
                    e.stopPropagation();
                }
                this.swipeClosing = true;
                this.swipeDeltaX = typeof window !== 'undefined' ? window.innerWidth : SWIPE_CLOSE_DISTANCE * 2;
                this.clearCloseTimer();
                this.swipeCloseTimer = setTimeout(function () {
                    _this.close();
                }, SWIPE_CLOSE_DURATION);
                this.swipeTracking = false;
                return;
            }

            this.resetSwipe();
            this.startCloseTimer();
        },
        cancelSwipe: function cancelSwipe() {
            this.resetSwipe();
        },
        resetSwipe: function resetSwipe() {
            this.swipeTracking = false;
            this.swipeDragging = false;
            this.swipeDeltaX = 0;
        },
        clearSwipeCloseTimer: function clearSwipeCloseTimer() {
            if (this.swipeCloseTimer) {
                clearTimeout(this.swipeCloseTimer);
                this.swipeCloseTimer = null;
            }
        },
        handleClick: function handleClick(e) {
            if (this.swipeMoved) {
                e.stopPropagation();
                this.swipeMoved = false;
                return;
            }
            (getListeners(this).click || noop)(e);
        },
        handleMouseLeave: function handleMouseLeave(e) {
            if (this.swipeTracking) {
                this.endSwipe(e);
                return;
            }
            this.startCloseTimer();
        },
        close: function close(e) {
            if (e) {
                e.stopPropagation();
            }
            this.clearCloseTimer();
            this.__emit('close', e ? { manual: true } : undefined);
        },
        startCloseTimer: function startCloseTimer() {
            var _this = this;

            this.clearCloseTimer();
            if (!this.willDestroy && this.duration) {
                this.closeTimer = setTimeout(function () {
                    _this.close();
                }, this.duration * 1000);
            }
        },
        clearCloseTimer: function clearCloseTimer() {
            if (this.closeTimer) {
                clearTimeout(this.closeTimer);
                this.closeTimer = null;
            }
        },
        restartCloseTimer: function restartCloseTimer() {
            this.clearCloseTimer();
            this.startCloseTimer();
        }
    },

    render: function render() {
        var _className;

        var h = arguments[0];
        var prefixCls = this.prefixCls,
            closable = this.closable,
            clearCloseTimer = this.clearCloseTimer,
            $slots = this.$slots,
            close = this.close;

        var componentClass = prefixCls + '-notice';
        var className = (_className = {}, _defineProperty(_className, '' + componentClass, 1), _defineProperty(_className, componentClass + '-closable', closable), _className);
        var baseStyle = getStyle(this) || { right: '50%' };
        var swipeStyle = this.swipeDragging || this.swipeClosing ? {
            transform: 'translate3d(' + this.swipeDeltaX + 'px, 0, 0)',
            opacity: Math.max(0, 1 - this.swipeDeltaX / 240),
            transition: this.swipeClosing ? 'transform ' + SWIPE_CLOSE_DURATION + 'ms ease, opacity ' + SWIPE_CLOSE_DURATION + 'ms ease' : 'none'
        } : {};
        var style = _extends({}, baseStyle, swipeStyle);
        var closeIcon = getComponentFromProp(this, 'closeIcon');
        return h(
            'div',
            {
                'class': className,
                style: style,
                on: {
                    'mouseenter': clearCloseTimer,
                    'mouseleave': this.handleMouseLeave,
                    'click': this.handleClick,
                    'touchstart': this.startSwipe,
                    'touchmove': this.moveSwipe,
                    'touchend': this.endSwipe,
                    'touchcancel': this.cancelSwipe,
                    'mousedown': this.startSwipe,
                    'mousemove': this.moveSwipe,
                    'mouseup': this.endSwipe
                }
            },
            [h(
                'div',
                { 'class': componentClass + '-content' },
                [$slots['default']]
            ), closable ? h(
                'a',
                {
                    attrs: { tabIndex: '0' },
                    on: {
                        'click': close
                    },
                    'class': componentClass + '-close' },
                [closeIcon || h('span', { 'class': componentClass + '-close-x' })]
            ) : null]
        );
    }
};
