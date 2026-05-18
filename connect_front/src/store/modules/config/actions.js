import axios from '@/config/axios'
import { deleteById, getById, setData, updateById } from '@/utils/cacheDb'

const BANNER_NEWS_DB = 'bannerNews'

const getBannerNewsStorageId = userId => `banner-news-${userId}`

export default {
    init({commit}, {data}) {
        commit('SET_CONFIG', data)
    },
    async fetchBannerNews({ state, commit, rootState }, { force = false } = {}) {
        if(state.bannerNewsLoaded && !force)
            return state.bannerNews

        const { data } = await axios.get('/news/news/list/', {
            params: {
                page: 1,
                page_size: 1,
                is_banner: true
            }
        })

        const bannerNews = data?.results?.[0] || null
        const userId = rootState.user.user?.id

        if(userId) {
            const storageId = getBannerNewsStorageId(userId)
            const hiddenBanner = await getById({
                id: storageId,
                databaseName: BANNER_NEWS_DB
            }).catch(() => null)
            const hiddenNewsId = hiddenBanner?.value?.newsId || null

            if(!bannerNews && hiddenNewsId) {
                await deleteById({
                    id: storageId,
                    databaseName: BANNER_NEWS_DB
                }).catch(() => null)
            }

            if(hiddenNewsId && hiddenNewsId !== bannerNews?.id) {
                await deleteById({
                    id: storageId,
                    databaseName: BANNER_NEWS_DB
                }).catch(() => null)
            }

            if(hiddenNewsId && hiddenNewsId === bannerNews?.id) {
                commit('SET_BANNER_NEWS', null)
                return null
            }
        }

        commit('SET_BANNER_NEWS', bannerNews)

        return bannerNews
    },
    async closeBannerNews({ state, commit, rootState }) {
        const userId = rootState.user.user?.id
        const newsId = state.bannerNews?.id

        if(userId && newsId) {
            const storageId = getBannerNewsStorageId(userId)
            const hiddenBanner = await getById({
                id: storageId,
                databaseName: BANNER_NEWS_DB
            }).catch(() => null)

            if(hiddenBanner?.id) {
                await updateById({
                    id: storageId,
                    value: { newsId },
                    databaseName: BANNER_NEWS_DB
                }).catch(() => null)
            } else {
                await setData({
                    data: {
                        id: storageId,
                        value: { newsId }
                    },
                    databaseName: BANNER_NEWS_DB
                }).catch(() => null)
            }
        }

        commit('SET_BANNER_NEWS', null)
    },
    async clearHiddenBannerNews(_, { userId } = {}) {
        if(!userId)
            return

        await deleteById({
            id: getBannerNewsStorageId(userId),
            databaseName: BANNER_NEWS_DB
        }).catch(() => null)
    }
}
