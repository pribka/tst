import Pagination from './Pagination';
import Base from 'ant-design-vue/es/base';

export { PaginationProps, PaginationConfig } from './Pagination';

/* istanbul ignore next */
Pagination.install = function (Vue) {
    Vue.use(Base);
    Vue.component(Pagination.name, Pagination);
};

export default Pagination;