<template>
    <div
        v-if="bannerNews"
        class="news_banner"
        role="button"
        tabindex="0"
        @click="openNews"
        @keydown.enter="openNews"
        @keydown.space.prevent="openNews">
        <div class="news_banner__inner">
            <div class="news_banner__container">
                <div class="news_banner__content">
                    <i class="fi fi-rr-comment-info"></i>
                    <div class="news_banner__text">
                        <div class="news_banner__title">
                            {{ bannerNews.title }}
                        </div>
                        <div v-if="bannerText" class="news_banner__description">
                            {{ bannerText }}
                        </div>
                    </div>
                </div>
                <a-button v-if="!isMobile" type="link" class="news_banner__action" @click.stop="openNews">
                    <span class="news_banner__action_text">{{ $t('support.moreDetails') }}</span>
                    <i class="fi fi-rr-arrow-right"></i>
                </a-button>
                <a-button
                    type="link"
                    shape="circle"
                    class="news_banner__close"
                    @click.stop="closeBanner">
                    <i class="fi fi-rr-cross"></i>
                </a-button>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    computed: {
        bannerNews() {
            return this.$store.state.config.bannerNews
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        bannerText() {
            return this.bannerNews?.short_content || ''
        }
    },
    methods: {
        async closeBanner() {
            await this.$store.dispatch('config/closeBannerNews')
        },
        openNews() {
            if(!this.bannerNews?.id || this.$route.query.newsItem === this.bannerNews.id)
                return

            this.$router.push({
                query: {
                    ...this.$route.query,
                    newsItem: this.bannerNews.id
                }
            })
        }
    }
}
</script>

<style lang="scss" scoped>
.news_banner{
    width: 100%;
    cursor: pointer;
    &__inner{
        min-height: 44px;
        padding: 10px 18px;
        background: linear-gradient(90deg, #efc36f 0%, #f5d5a0 45%, #efc36f 100%);
        color: #3b2b00;
    }
    &__container{
        margin: 0 auto;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
    }
    &__content{
        display: flex;
        align-items: center;
        gap: 12px;
        min-width: 0;
        flex: 1;
        i{
            font-size: 18px;
            flex-shrink: 0;
        }
    }
    &__text{
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 2px;
        min-width: 0;
        flex: 1;
    }
    &__title{
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        font-size: 14px;
        line-height: 1.2;
        font-weight: 600;
    }
    &__description{
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        font-size: 14px;
        line-height: 1.2;
        opacity: 0.9;
    }
    &__action{
        flex-shrink: 0;
        padding: 0 !important;
        height: auto !important;
        color: #3b2b00 !important;
        font-size: 14px !important;
        font-weight: 600;
        display: inline-flex !important;
        align-items: center;
        gap: 6px;
        text-decoration: none !important;
    }
    &__action_text{
        text-decoration: underline;
    }
    &__close{
        flex-shrink: 0;
        width: 28px !important;
        min-width: 28px !important;
        height: 28px !important;
        padding: 0 !important;
        color: #3b2b00 !important;
        display: inline-flex !important;
        align-items: center;
        justify-content: center;
        opacity: 0.8;
    }
    @media (max-width: 768px) {
        &__inner{
            padding: 10px 12px;
        }
        &__container{
            gap: 10px;
        }
        &__content{
            gap: 8px;
        }
    }
}
</style>
