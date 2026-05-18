import Vue from 'vue'
import { setData, getById, updateById } from '../utils/productDb'
import store from '@/store'

export default {
    CHANGE_PRODUCT_PRICE(state, {price_by_catalog, id}) {
        if(Object.keys(state.goodsList)?.length) {
            for (const key in state.goodsList) {
                const index = state.goodsList[key].results.findIndex(f => f.id === id)
                if(index !== -1) {
                    Vue.set(state.goodsList[key].results[index], 'price_by_catalog', price_by_catalog)
                }
            }
        }
    },
    SET_DEFAULT_GRID_TYPE(state) {
        const storedListType = localStorage.getItem('listType')
        const isActualType = storedListType && state.gridType.reduce((hasInTypeList, gridTypeItem) => {
            return hasInTypeList || (gridTypeItem.type === storedListType)
        }, false)
        
        if(isActualType)
            state.activeGridType = storedListType
        else if(store.state.config.config?.product_setting?.product_default_list)
            state.activeGridType = store.state.config.config.product_setting.product_default_list
        else
            state.activeGridType = 'ProductCard'
    },
    SET_GRID_TYPE(state, value) {
        state.gridType = value
    },
    CHANGE_ACTIVE_TYPE(state, value) {
        localStorage.setItem('listType', value)
        state.activeGridType = value
    },
    SET_HISTORY(state, value) {
        state.historyGoods = value
    },
    async REMOVE_HISTORY(state, id) {
        if(state.historyGoods?.length) {
            try {
                const index = state.historyGoods.findIndex(f => f.id === id)
                if(index !== -1) {
                    const usId = store.state.user?.user?.id ? store.state.user.user.id : 'default',
                        id = `history_${usId}`,
                        databaseName = 'products';

                    state.historyGoods.splice(index, 1)

                    await updateById({
                        id,
                        value: state.historyGoods,
                        databaseName
                    })
                }
            } catch(e) {
                console.log(e)
            }
        }
    },
    async SAVE_HISTORY(state) {
        const usId = store.state.user?.user?.id ? store.state.user.user.id : 'default'
        if(state.detail) {
            try {
                const id = `history_${usId}`,
                    databaseName = 'products';

                let oList = [],
                    hGoods = [],
                    limit = 15;

                hGoods.unshift(state.detail)

                const data = await getById({ 
                    id, 
                    databaseName
                })
                if(data?.value?.length) {
                    oList = data.value

                    hGoods.forEach(item => {
                        const index = oList.findIndex(f => f.id === item.id)
                        if(index !== -1) {
                            oList.splice(index, 1)
                        }
                    })
                    hGoods = hGoods.concat(oList)
                }

                if(hGoods.length > limit)
                    hGoods = hGoods.slice(0, limit)

                if(data?.id) {
                    await updateById({
                        id,
                        value: hGoods,
                        databaseName
                    })
                } else {
                    await setData({
                        data: {
                            id,
                            value: hGoods
                        },
                        databaseName
                    })
                }

                state.historyGoods = hGoods
            } catch(e) {
                console.log(e)
            }
        }
    },
    SET_GOODS_PAGE(state, {value, page_name}) {
        Vue.set(state.goodsPage, page_name, value)
    },
    CHANGE_GOODS_SEARCH(state, value) {
        state.goodsSearch = value
    },
    INIT_GOODS_LIST(state, page_name) {
        if(!state.goodsPage?.[page_name] && typeof state.goodsPage[page_name] === 'undefined') {
            Vue.set(state.goodsPage, page_name, 0)
        }
        if(!state.goodsList?.[page_name]) {
            Vue.set(state.goodsList, page_name, {
                count: 0,
                next: true,
                results: []
            })
        }
    },
    SEARCH_HANDLER(state, page_name) {
        Vue.set(state.goodsEmpty, page_name, false)
        Vue.set(state.goodsPage, page_name, 0)
        Vue.set(state.goodsList, page_name, {
            count: 0,
            next: true,
            results: []
        })
    },
    SET_GOODS_EMPTY(state, {value, page_name}) {
        Vue.set(state.goodsEmpty, page_name, value)
    },
    SET_GOODS_NEXT(state, {value, page_name}) {
        Vue.set(state.goodsList[page_name], 'next', value)
    },
    CONCAT_GOODS_LIST(state, {value, page_name}) {
        state.goodsList[page_name].results = state.goodsList[page_name].results.concat(value)
    },
    PRODUCT_CART_ADDED(state, { goods, quantity }) {
        if(Object.keys(state.goodsList)?.length) {
            for (const key in state.goodsList) {
                const index = state.goodsList[key].results.findIndex(f => f.id === goods)
                if(index !== -1) {
                    Vue.set(state.goodsList[key].results[index], 'in_cart', quantity)
                }
            }
        }
    },
    DETAIL_PRODUCT_CART_ADDED(state, { goods, quantity }) {
        if (state.detail?.id === goods) {
            Vue.set(state.detail, 'in_cart', quantity)
        }
    },
    PRODUCT_CART_REMOVED(state, id) {
        if(Object.keys(state.goodsList)?.length) {
            for (const key in state.goodsList) {
                const index = state.goodsList[key].results.findIndex(f => f.id === id)
                if(index !== -1) {
                    Vue.set(state.goodsList[key].results[index], 'in_cart', 0)
                }
            }
        }
    },
    ALL_PRODUCT_CART_REMOVED(state) {
        if(Object.keys(state.goodsList)?.length) {
            for (const key in state.goodsList) {
                const cartAdded = state.goodsList[key].results.filter(f => f.in_cart)
                if (cartAdded?.length) {
                    cartAdded.forEach(prod => {
                        const index = state.goodsList[key].results.findIndex(f => f.id === prod.id)
                        if (index !== -1) {
                            Vue.set(state.goodsList[key].results[index], 'in_cart', 0)
                        }
                    })
                }
            }
        }
    },
    SET_DETAIL(state, value) {
        state.detail = value
    },
    SET_CATEGORY(state, value) {
        state.goodsCategory = value === 'all' ? null : value
    },
    SET_ORDERING(state, value) {
        state.ordering = value
    }
}