import _objectWithoutProperties from 'babel-runtime/helpers/objectWithoutProperties'
import _defineProperty from 'babel-runtime/helpers/defineProperty'
import Vue from 'vue'
import PropTypes from 'ant-design-vue/es/_util/vue-types'
import { getStyle, getComponentFromProp } from 'ant-design-vue/es/_util/props-util'
import BaseMixin from 'ant-design-vue/es/_util/BaseMixin'
import createChainedFunction from 'ant-design-vue/es/_util/createChainedFunction'
import getTransitionProps from 'ant-design-vue/es/_util/getTransitionProps'
import Notice from './Notice'
import Base from 'ant-design-vue/es/base'
import { i18n } from '@/config/i18n-setup'
import notificationChannel from '@/utils/notificationChannel.js'
import { closeAllBrowserPushNotifications } from '@/utils/browserPushNotifications'

function noop() {}

let seed = 0
const now = Date.now()

function getUuid() {
    return 'rcNotification_' + now + '_' + seed++
}

const Notification = {
    mixins: [BaseMixin],
    props: {
        prefixCls: PropTypes.string.def('rc-notification'),
        transitionName: PropTypes.string,
        animation: PropTypes.oneOfType([PropTypes.string, PropTypes.object]).def('fade'),
        maxCount: PropTypes.number,
        closeIcon: PropTypes.any
    },
    data() {
        return {
            notices: [],
            hasItemsDelay: false,
            hideTimer: null
        }
    },
    computed: {
        itemsCount() {
            return this.notices.length
        },
        hasItemsActive() {
            return this.itemsCount > 0 || this.hasItemsDelay
        }
    },
    watch: {
        itemsCount(val) {
            if (val > 0) {
                this.hasItemsDelay = true
                if (this.hideTimer) {
                    clearTimeout(this.hideTimer)
                    this.hideTimer = null
                }
            } else {
                if (this.hideTimer) clearTimeout(this.hideTimer)
                this.hideTimer = setTimeout(() => {
                    this.hasItemsDelay = false
                    this.hideTimer = null
                }, 500)
            }
        }
    },
    beforeDestroy() {
        if (this.hideTimer) clearTimeout(this.hideTimer)
    },
    methods: {
        getTransitionName() {
            const props = this.$props
            let transitionName = props.transitionName
            if (!transitionName && props.animation) transitionName = props.prefixCls + '-' + props.animation
            return transitionName
        },
        add(notice) {
            const key = notice.key = notice.key || getUuid()
            const maxCount = this.$props.maxCount
            this.setState(previousState => {
                const notices = previousState.notices
                const noticeIndex = notices.map(v => v.key).indexOf(key)
                const updatedNotices = notices.concat()
                if (noticeIndex !== -1) {
                    updatedNotices.splice(noticeIndex, 1, notice)
                } else {
                    if (maxCount && notices.length >= maxCount) {
                        notice.updateKey = updatedNotices[0].updateKey || updatedNotices[0].key
                        updatedNotices.shift()
                    }
                    updatedNotices.push(notice)
                }
                return { notices: updatedNotices }
            })
        },
        remove(key) {
            this.setState(previousState => {
                return { notices: previousState.notices.filter(notice => notice.key !== key) }
            })
        },
        closeAll() {
            const keys = this.notices.map(n => n.key)
            keys.forEach(k => this.remove(k))
            try {
                notificationChannel.broadcastCloseAll()
            } catch(e) {}
            closeAllBrowserPushNotifications()
        }
    },
    render(h) {
        const { prefixCls, notices, remove, getTransitionName } = this
        const transitionProps = getTransitionProps(getTransitionName())
        const noticeNodes = notices.map((notice, index) => {
            const update = Boolean(index === notices.length - 1 && notice.updateKey)
            const key = notice.updateKey ? notice.updateKey : notice.key
            const { content, duration, closable, onClose, style, class: className } = notice
            const close = createChainedFunction(remove.bind(this, notice.key), onClose)
            const noticeProps = {
                props: {
                    prefixCls,
                    duration,
                    closable,
                    update,
                    closeIcon: getComponentFromProp(this, 'closeIcon')
                },
                on: {
                    close,
                    click: notice.onClick || noop
                },
                style,
                class: className,
                key
            }
            return h(Notice, noticeProps, [typeof content === 'function' ? content(h) : content])
        })

        const rootClass = {
            [prefixCls]: 1,
            'ant-notification-has-items': this.hasItemsActive
        }

        const style = getStyle(this)

        const footer = notices.length > 1
            ? h('div', { class: prefixCls + '-footer ant-notification-footer' }, [
                h('button', { class: 'close_btn', on: { click: this.closeAll } }, [i18n.t('close_all_notify')])
            ])
            : null

        return h(
            'div',
            { class: rootClass, style: style || { top: '65px', left: '50%' } },
            [
                h('transition-group', transitionProps, [noticeNodes]),
                footer
            ]
        )
    }
}

Notification.newInstance = function newNotificationInstance(properties, callback) {
    const _ref = properties || {}
    const getContainer = _ref.getContainer
    const style = _ref.style
    const className = _ref['class']
    const props = _objectWithoutProperties(_ref, ['getContainer', 'style', 'class'])

    const div = document.createElement('div')
    if (getContainer) {
        const root = getContainer()
        root.appendChild(div)
    } else {
        document.body.appendChild(div)
    }
    const V = Base.Vue || Vue
    new V({
        el: div,
        mounted() {
            const self = this
            this.$nextTick(function () {
                callback({
                    notice(noticeProps) {
                        self.$refs.notification.add(noticeProps)
                    },
                    removeNotice(key) {
                        self.$refs.notification.remove(key)
                    },
                    component: self,
                    destroy() {
                        self.$destroy()
                        self.$el.parentNode.removeChild(self.$el)
                    }
                })
            })
        },
        render() {
            const h = arguments[0]
            const p = {
                props,
                ref: 'notification',
                style,
                class: className
            }
            return h(Notification, p)
        }
    })
}

export default Notification
