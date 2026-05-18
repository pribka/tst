<template>
    <div v-if="embedded" class="emoji_picker" :class="pickerSizeClass">
        <Segmented
            v-if="showTabs"
            v-model="activeTab"
            bgInvert
            block
            :options="tabOptions"
            class="emoji_picker__tabs" />
        <div v-if="activeTab === 'emoji'" class="emoji_picker__body">
            <div class="emoji_list">
                <button
                    v-for="item in emojiList"
                    :key="item.key"
                    type="button"
                    class="emoji_list__item"
                    @click="selectEmoji(item)">
                    {{ item.unicode }}
                </button>
            </div>
        </div>
        <div v-else class="emoji_picker__body emoji_picker__body--gif">
            <div class="gif_search">
                <i class="fi fi-rr-search gif_search__icon"></i>
                <input
                    ref="gifSearchInput"
                    :value="gifSearch"
                    type="text"
                    class="gif_search__input"
                    :placeholder="$t('emoji.search_gif')"
                    @input="handleSearchInput" />
                <button
                    v-if="gifSearch"
                    type="button"
                    class="gif_search__clear"
                    @click="clearGifSearch">
                    <i class="fi fi-rr-cross-small"></i>
                </button>
            </div>
            <div
                ref="gifScroll"
                class="gif_grid"
                @scroll.passive="handleGifScroll">
                <div v-if="!hasGiphyApiKey" class="gif_state">
                    {{ $t('emoji.enable_gif') }}
                </div>
                <div v-else-if="gifInitialLoading" class="gif_state">
                    <a-spin />
                </div>
                <div v-else-if="!gifList.length" class="gif_state">
                    {{ $t('emoji.not_found') }}
                </div>
                <template v-else>
                    <button
                        v-for="gif in gifList"
                        :key="gif.id"
                        type="button"
                        class="gif_card"
                        :disabled="gifUploading"
                        :title="gif.title || $t('emoji.gif_title')"
                        @click="selectGif(gif)">
                        <img
                            class="gif_card__image"
                            :src="gif.previewUrl"
                            :alt="gif.title || $t('emoji.gif_title')" />
                    </button>
                    <div v-if="gifLoadingMore" class="gif_grid__loader">
                        <a-spin size="small" />
                    </div>
                </template>
            </div>
        </div>
    </div>
    <a-popover
        v-else
        trigger="click"
        destroyTooltipOnHide
        transitionName=""
        :visible="visible"
        :overlayStyle="{
            zIndex: 99999999
        }"
        overlayClassName="emoji_popover"
        @visibleChange="handleVisibleChange">
        <template slot="content">
            <div class="emoji_picker" :class="pickerSizeClass">
                <Segmented
                    v-if="showTabs"
                    v-model="activeTab"
                    bgInvert
                    block
                    :options="tabOptions"
                    class="emoji_picker__tabs" />
                <div v-if="activeTab === 'emoji'" class="emoji_picker__body">
                    <div class="emoji_list">
                        <button
                            v-for="item in emojiList"
                            :key="item.key"
                            type="button"
                            class="emoji_list__item"
                            @click="selectEmoji(item)">
                            {{ item.unicode }}
                        </button>
                    </div>
                </div>
                <div v-else class="emoji_picker__body emoji_picker__body--gif">
                    <div class="gif_search">
                        <i class="fi fi-rr-search gif_search__icon"></i>
                        <input
                            ref="gifSearchInput"
                            :value="gifSearch"
                            type="text"
                            class="gif_search__input"
                            :placeholder="$t('emoji.search_gif')"
                            @input="handleSearchInput" />
                        <button
                            v-if="gifSearch"
                            type="button"
                            class="gif_search__clear"
                            @click="clearGifSearch">
                            <i class="fi fi-rr-cross-small"></i>
                        </button>
                    </div>
                    <div
                        ref="gifScroll"
                        class="gif_grid"
                        @scroll.passive="handleGifScroll">
                        <div v-if="!hasGiphyApiKey" class="gif_state">
                            {{ $t('emoji.enable_gif') }}
                        </div>
                        <div v-else-if="gifInitialLoading" class="gif_state">
                            <a-spin />
                        </div>
                        <div v-else-if="!gifList.length" class="gif_state">
                            {{ $t('emoji.not_found') }}
                        </div>
                        <template v-else>
                            <button
                                v-for="gif in gifList"
                                :key="gif.id"
                                type="button"
                                class="gif_card"
                                :disabled="gifUploading"
                                :title="gif.title || $t('emoji.gif_title')"
                                @click="selectGif(gif)">
                                <img
                                    class="gif_card__image"
                                    :src="gif.previewUrl"
                                    :alt="gif.title || $t('emoji.gif_title')" />
                            </button>
                            <div v-if="gifLoadingMore" class="gif_grid__loader">
                                <a-spin size="small" />
                            </div>
                        </template>
                    </div>
                </div>
            </div>
        </template>
        <a-button
            type="ui"
            ghost
            :size="size"
            icon="fi-rr-smile"
            shape="circle"
            flaticon
            :loading="gifUploading" />
    </a-popover>
</template>

<script>
import { debounce } from 'lodash'

const GIF_LIMIT = 24

export default {
    components: {
        Segmented: () => import('@/modules/UIModules/Segmented')
    },
    props: {
        size: {
            type: String,
            default: 'default'
        },
        pickerSize: {
            type: String,
            default: 'default'
        },
        gifUploading: {
            type: Boolean,
            default: false
        },
        embedded: {
            type: Boolean,
            default: false
        },
        initialTab: {
            type: String,
            default: 'emoji'
        },
        showTabs: {
            type: Boolean,
            default: true
        }
    },
    data() {
        return {
            visible: false,
            activeTab: this.initialTab === 'gif' ? 'gif' : 'emoji',
            gifSearch: '',
            gifList: [],
            gifOffset: 0,
            gifHasMore: true,
            gifLoadingMore: false,
            gifInitialLoading: false,
            gifRequestId: 0,
            emojiList: [
                '👍', '👎', '👏', '🙌', '🫶',
                '🔥', '✨', '🎉', '🎊', '🎁',
                '🎂', '🥳', '🍾', '🥂', '💐',
                '❤️', '😍', '😘', '😊', '😉',
                '😄', '😁', '🤗', '😎', '🤩',
                '🤯', '😮', '😳', '😭', '😂',
                '😕', '😔', '😡', '😴', '😰',
                '🤔', '🫡', '🤝', '🙏', '💪',
                '👌', '✌️', '🤘', '🤟', '👋',
                '💯', '✅', '❌', '⚡', '🌈',
                '☀️', '🌙', '⭐', '🌹', '🍀',
                '🎵', '🎶', '🎤', '🎧', '🎬',
                '🏆', '🥇', '⚽', '🏀', '🎯',
                '🍕', '🍔', '🍓', '☕', '🍺',
                '🐶', '🐱', '🐼', '🦊', '🐻',
                '🚀', '🌟', '💥', '🎆', '🎇'
            ].map((unicode, index) => ({
                key: `emoji_${index}`,
                unicode
            }))
        }
    },
    computed: {
        tabOptions() {
            return [
                {
                    key: 'emoji',
                    title: this.$t('emoji.tab_emoji')
                },
                {
                    key: 'gif',
                    title: this.$t('emoji.tab_gif')
                }
            ]
        },
        hasGiphyApiKey() {
            return !!String(process.env.VUE_APP_GIPHY_API_KEY || '').trim()
        },
        pickerSizeClass() {
            if (this.pickerSize === 'drawer') {
                return 'emoji_picker--drawer'
            }

            return this.pickerSize === 'compact' ? 'emoji_picker--compact' : 'emoji_picker--default'
        }
    },
    created() {
        this.debouncedGifSearch = debounce(() => {
            this.loadGifs({ reset: true })
        }, 350)
    },
    mounted() {
        if (this.embedded && this.activeTab === 'gif') {
            this.ensureGifList()
            this.focusGifSearchInput()
        }
    },
    beforeDestroy() {
        this.debouncedGifSearch?.cancel?.()
    },
    methods: {
        handleVisibleChange(value) {
            this.visible = value

            if (value && this.activeTab === 'gif') {
                this.ensureGifList()
                this.focusGifSearchInput()
            }
        },
        focusGifSearchInput() {
            this.$nextTick(() => {
                requestAnimationFrame(() => {
                    this.$refs.gifSearchInput?.focus?.()
                })
            })
        },
        async ensureGifList() {
            if (!this.hasGiphyApiKey || this.gifList.length || this.gifInitialLoading || this.gifLoadingMore) {
                return
            }

            await this.loadGifs({ reset: true })
        },
        async loadGifs({ reset = false } = {}) {
            if (!this.hasGiphyApiKey || this.gifLoadingMore) {
                return
            }

            const nextOffset = reset ? 0 : this.gifOffset
            if (!reset && !this.gifHasMore) {
                return
            }

            const requestId = Date.now()
            this.gifRequestId = requestId

            if (reset) {
                this.gifInitialLoading = true
                this.gifHasMore = true
            } else {
                this.gifLoadingMore = true
            }

            try {
                const endpoint = this.gifSearch.trim()
                    ? 'https://api.giphy.com/v1/gifs/search'
                    : 'https://api.giphy.com/v1/gifs/trending'
                const params = new URLSearchParams({
                    api_key: process.env.VUE_APP_GIPHY_API_KEY,
                    limit: String(GIF_LIMIT),
                    offset: String(nextOffset),
                    rating: 'pg'
                })

                if (this.gifSearch.trim()) {
                    params.set('q', this.gifSearch.trim())
                    params.set('lang', this.resolveGiphyLang())
                }

                const response = await fetch(`${endpoint}?${params.toString()}`)
                if (!response.ok) {
                    throw new Error(`GIPHY request failed with status ${response.status}`)
                }

                const payload = await response.json()
                if (this.gifRequestId !== requestId) {
                    return
                }

                const items = Array.isArray(payload?.data)
                    ? payload.data.map(this.normalizeGif).filter(Boolean)
                    : []

                this.gifList = reset ? items : [...this.gifList, ...items]
                this.gifOffset = nextOffset + items.length
                this.gifHasMore = items.length === GIF_LIMIT
            } catch (error) {
                console.error(error)

                if (reset) {
                    this.gifList = []
                    this.gifHasMore = false
                }
            } finally {
                if (this.gifRequestId === requestId) {
                    this.gifInitialLoading = false
                    this.gifLoadingMore = false
                }
            }
        },
        normalizeGif(item) {
            const previewUrl = item?.images?.fixed_width?.url
                || item?.images?.downsized?.url
                || item?.images?.preview_gif?.url
            const downloadUrl = item?.images?.original?.url
                || item?.images?.downsized_large?.url
                || item?.images?.fixed_width?.url

            if (!previewUrl || !downloadUrl || !item?.id) {
                return null
            }

            return {
                id: item.id,
                title: item.title || '',
                previewUrl,
                downloadUrl,
                filename: `${String(item.slug || item.id).replace(/[^a-z0-9-_]+/gi, '-').replace(/^-+|-+$/g, '') || item.id}.gif`
            }
        },
        resolveGiphyLang() {
            const locale = String(this.$i18n?.locale || 'ru').toLowerCase()

            if (locale === 'kk') {
                return 'ru'
            }

            if (['ru', 'en'].includes(locale)) {
                return locale
            }

            return 'ru'
        },
        handleSearchInput(event) {
            this.gifSearch = String(event?.target?.value || '')
            this.debouncedGifSearch()
        },
        clearGifSearch() {
            this.gifSearch = ''
            this.loadGifs({ reset: true })
        },
        handleGifScroll(event) {
            const target = event?.target
            if (!target || this.gifLoadingMore || this.gifInitialLoading || !this.gifHasMore) {
                return
            }

            const threshold = 280
            const distanceToBottom = target.scrollHeight - target.scrollTop - target.clientHeight

            if (distanceToBottom <= threshold) {
                this.loadGifs()
            }
        },
        selectEmoji(item) {
            this.visible = false
            this.$emit('click', {
                detail: {
                    unicode: item.unicode
                }
            })
        },
        selectGif(gif) {
            this.visible = false
            this.$emit('select-gif', gif)
        }
    },
    watch: {
        activeTab(value) {
            if (value === 'gif' && (this.visible || this.embedded)) {
                this.ensureGifList()
                this.focusGifSearchInput()
            }
        },
        embedded(value) {
            if (value && this.activeTab === 'gif') {
                this.ensureGifList()
                this.focusGifSearchInput()
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.emoji_picker{
    padding: 10px;
}

.emoji_picker--default{
    width: 360px;
}

.emoji_picker--compact{
    width: 320px;
}

.emoji_picker--drawer{
    width: 100%;
    padding: 0 14px 8px;
}

.emoji_picker__tabs{
    margin-bottom: 10px;
}

.emoji_picker__body{
    background: #fff;
    border-radius: 12px;
    overflow: hidden;
}

.emoji_picker--default .emoji_picker__body{
    height: 260px;
}

.emoji_picker--compact .emoji_picker__body{
    height: 220px;
}

.emoji_picker--drawer .emoji_picker__body{
    height: min(58vh, 430px);
}

.emoji_picker__body--gif{
    display: flex;
    flex-direction: column;
    background: transparent;
    padding: 0;
    border-radius: 0;
}

.emoji_list{
    display: grid;
    gap: 8px;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    height: 100%;
    overflow-y: auto;
    padding-right: 4px;
}

.emoji_list__item{
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 54px;
    border: 0;
    border-radius: 14px;
    background: transparent;
    font-size: 28px;
    cursor: pointer;
    transition: background 0.2s ease, transform 0.2s ease;

    &:hover{
        background: #f3f6ff;
        transform: translateY(-1px);
    }
}

.gif_search{
    display: flex;
    align-items: center;
    flex: 0 0 44px;
    gap: 8px;
    height: 44px;
    padding: 0 12px;
    margin-bottom: 10px;
    border-radius: 999px;
    background: #edf2fb;
    border: 1px solid rgba(71, 119, 255, 0.1);
}

.gif_search__icon,
.gif_search__clear{
    color: #7d8ca8;
    font-size: 16px;
}

.gif_search__input{
    width: 100%;
    border: 0;
    outline: 0;
    background: transparent;
    color: #1f2a44;
    font-size: 14px;
}

.gif_search__clear{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0;
    border: 0;
    background: transparent;
    cursor: pointer;
}

.gif_grid{
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    grid-auto-rows: 100px;
    gap: 8px;
    overflow-y: auto;
    align-content: start;
    padding-right: 4px;
}

.emoji_picker--default .gif_grid{
    height: 206px;
}

.emoji_picker--compact .gif_grid{
    height: 166px;
}

.emoji_picker--drawer .gif_grid{
    grid-auto-rows: 118px;
    height: calc(min(58vh, 430px) - 54px);
}

.gif_card{
    position: relative;
    display: block;
    padding: 0;
    border: 0;
    border-radius: 12px;
    overflow: hidden;
    background: #dce5f6;
    cursor: pointer;
    width: 100%;
    height: 100px;
    transition: transform 0.2s ease, opacity 0.2s ease;

    &:hover:not(:disabled){
        transform: translateY(-1px);
    }

    &:disabled{
        opacity: 0.6;
        cursor: wait;
    }
}

.emoji_picker--drawer .gif_card{
    height: 118px;
}

.gif_card__image{
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
}

.gif_state,
.gif_grid__loader{
    grid-column: 1 / -1;
    min-height: 80px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #667085;
    text-align: center;
    padding: 12px;
}
</style>
