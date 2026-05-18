import { ConfigConsumerProps } from 'ant-design-vue/es/config-provider/configConsumerProps';
import Icon from 'ant-design-vue/es/icon';
import { getListeners, getComponentFromProp } from 'ant-design-vue/es/_util/props-util';
import PropTypes from 'ant-design-vue/es/_util/vue-types';
import 'lazysizes';
// (опционально) плагин отслеживания изменений атрибутов, если используете
// import 'lazysizes/plugins/attrchange/ls.attrchange';

export default {
    name: 'AAvatar',
    props: {
        prefixCls: { type: String, default: undefined },
        shape: {
            validator: (val) => ['circle', 'square'].includes(val),
            default: 'circle'
        },
        size: {
            validator: (val) => typeof val === 'number' || ['small', 'large', 'default'].includes(val),
            default: 'default'
        },
        src: String,
        /** srcset для аватара */
        srcSet: String,
        icon: PropTypes.any,
        flaticon: PropTypes.bool,
        alt: String,
        loadError: Function,
        /** Если true — добавляем ?w&h к URL (серверный ресайз) */
        avResize: PropTypes.bool
    },
    inject: {
        configProvider: { default: () => ConfigConsumerProps }
    },
    data() {
        return {
            isImgExist: true,
            isMounted: false,
            scale: 1,

            // анти-мигание:
            isLazyLoaded: false, // картинка уже догружена lazysizes и закреплена
            lastSrc: null        // последний применённый URL (с учётом ?w&h)
        };
    },
    watch: {
        src(newVal, oldVal) {
            if (newVal !== oldVal) {
                // Новый URL → сбрасываем состояние, позволяем lazysizes снова догрузить
                this.isImgExist = true;
                this.isLazyLoaded = false;
                this.lastSrc = null;
                this.scale = 1;
            }
        }
    },
    mounted() {
        this.$nextTick(() => {
            this.setScale();
            this.isMounted = true;
            this.attachLazyListener(); // если <img> уже отрендерился
        });
    },
    updated() {
        this.$nextTick(() => {
            this.setScale();
            // при апдейтах убеждаемся, что слушатель 'lazyloaded' навешан
            this.attachLazyListener();
        });
    },
    methods: {
    // Подгон текста под рамку (поведение Antd)
        setScale() {
            if (!this.$refs.avatarChildren || !this.$refs.avatarNode) return;
            const childrenWidth = this.$refs.avatarChildren.offsetWidth;
            const nodeWidth = this.$refs.avatarNode.offsetWidth;
            if (
                childrenWidth === 0 ||
        nodeWidth === 0 ||
        (this.lastChildrenWidth === childrenWidth && this.lastNodeWidth === nodeWidth)
            ) return;

            this.lastChildrenWidth = childrenWidth;
            this.lastNodeWidth = nodeWidth;
            this.scale = nodeWidth - 8 < childrenWidth ? (nodeWidth - 8) / childrenWidth : 1;
        },

        handleImgLoadError() {
            const { loadError } = this.$props;
            const errorFlag = loadError ? loadError() : undefined;
            if (errorFlag !== false) this.isImgExist = false;
        },

        attachLazyListener() {
            const img = this.$refs.imgRef;
            if (!img || this._lazybound) return;
            // флаг, чтобы не навешивать слушатель многократно
            this._lazybound = true;
            img.addEventListener(
                'lazyloaded',
                () => {
                    // как только lazysizes подставил src — фиксируем состояние
                    this.isLazyLoaded = true;
                    // lastSrc должен соответствовать текущему вычисленному URL
                    this.lastSrc = this.computeUrl();
                },
                { once: true }
            );
        },

        // нормализуем размер в пикселях для avResize
        numericSize() {
            const { size } = this.$props;
            if (typeof size === 'number') return size;
            if (size === 'small') return 24;
            if (size === 'large') return 40;
            return 32; // default
        },

        // безопасно добавляем ?w&h (с учётом уже существующего query)
        addResizeParams(url, w, h) {
            if (!url) return url;
            const sep = url.includes('?') ? '&' : '?';
            return `${url}${sep}w=${w}&h=${h}`;
        },

        computeUrl() {
            const { src, avResize } = this.$props;
            if (!src) return src;
            if (!avResize) return src;
            const n = this.numericSize();
            return this.addResizeParams(src, n + 130, n + 130);
        }
    },

    render(h) {
        const {
            prefixCls: customizePrefixCls, shape, size, src, alt, srcSet
        } = this.$props;

        const icon = getComponentFromProp(this, 'icon');
        const flaticon = getComponentFromProp(this, 'flaticon');
        const avResize = getComponentFromProp(this, 'avResize');
        const { getPrefixCls } = this.configProvider;
        const prefixCls = getPrefixCls('avatar', customizePrefixCls);

        const { isImgExist, scale, isMounted, isLazyLoaded } = this.$data;

        const sizeCls = {
            [`${prefixCls}-lg`]: size === 'large',
            [`${prefixCls}-sm`]: size === 'small'
        };

        const classString = {
            [prefixCls]: true,
            ...sizeCls,
            [`${prefixCls}-${shape}`]: !!shape,
            [`${prefixCls}-image`]: !!(src && isImgExist),
            [`${prefixCls}-icon`]: !!icon
        };

        const sizeStyle =
      typeof size === 'number'
          ? {
              width: `${size}px`,
              height: `${size}px`,
              lineHeight: `${size}px`,
              fontSize: icon ? `${size / 2}px` : '18px'
          }
          : {};

        let children = this.$slots.default;

        if (src && isImgExist) {
            // Итоговый URL (с учетом avResize)
            const url = this.computeUrl();

            // Если уже lazyloaded и URL не менялся — используем обычный src и 'lazyloaded',
            // чтобы Vue-патчи не переводили назад в 'lazyload'
            const useNormalSrc = isLazyLoaded && this.lastSrc === url;

            const imgDataAttrs = useNormalSrc
                ? { src: url, alt, srcset: srcSet }
                : {
                    'data-src': url,
                    alt,
                    // lazysizes ожидает data-srcset
                    ...(srcSet ? { 'data-srcset': srcSet } : {})
                };

            children = h('img', {
                ref: 'imgRef',
                class: useNormalSrc ? 'lazyloaded' : 'lazyload',
                attrs: imgDataAttrs,
                on: { error: this.handleImgLoadError }
            });

            // При первичном рендере запомним url (для сравнения в следующих патчах)
            if (!this.lastSrc) this.lastSrc = url;

        } else if (icon) {
            if (typeof icon === 'string') {
                children = flaticon
                    ? h('i', { class: `flaticon fi ${icon}` })
                    : h(Icon, { attrs: { type: icon } });
            } else {
                children = icon;
            }
        } else {
            // Текст внутри аватара
            const childrenNode = this.$refs.avatarChildren;
            if (childrenNode || scale !== 1) {
                const transformString = `scale(${scale}) translateX(-50%)`;
                const childrenStyle = {
                    transform: transformString,
                    msTransform: transformString,
                    WebkitTransform: transformString
                };
                const sizeChildrenStyle =
          typeof size === 'number' ? { lineHeight: `${size}px` } : {};
                children = h(
                    'span',
                    {
                        class: `${prefixCls}-string`,
                        ref: 'avatarChildren',
                        style: { ...sizeChildrenStyle, ...childrenStyle }
                    },
                    [children]
                );
            } else {
                // как в Antd — скрываем до mount, чтобы избежать скачка
                children = h(
                    'span',
                    { class: `${prefixCls}-string`, ref: 'avatarChildren', style: { opacity: 0 } },
                    [children]
                );
            }
        }

        return h(
            'span',
            {
                ref: 'avatarNode',
                on: getListeners(this),
                class: classString,
                style: sizeStyle
            },
            [children]
        );
    }
};
