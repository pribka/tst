export default {
    getHeaderConfig: state => state.config?.header_setting || null,
    ai: state => state.config?.AISettings || false,
    bannerNews: state => state.bannerNews
}
