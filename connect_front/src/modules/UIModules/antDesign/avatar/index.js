import Avatar from './Avatar';
import Base from 'ant-design-vue/es/base';
import './style/index.js'

/* istanbul ignore next */
Avatar.install = function (Vue) {
    Vue.use(Base);
    Vue.component(Avatar.name, Avatar);
};

export default Avatar;