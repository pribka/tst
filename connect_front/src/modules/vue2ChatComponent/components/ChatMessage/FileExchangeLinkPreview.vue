<template>
    <div class="file-exchange-preview">
        <iframe
            class="file-exchange-preview__frame"
            :src="embedUrl"
            :title="normalizedUrl"
            loading="lazy"
            referrerpolicy="strict-origin-when-cross-origin"
            allow="clipboard-write"
            scrolling="yes" />
        <a
            class="file-exchange-preview__link"
            :href="normalizedUrl"
            target="_blank"
            rel="noopener noreferrer">
            {{ normalizedUrl }}
        </a>
    </div>
</template>

<script>
export default {
    name: 'FileExchangeLinkPreview',
    props: {
        url: {
            type: String,
            required: true
        }
    },
    computed: {
        normalizedUrl() {
            return String(this.url || '').trim()
        },
        fileExchangeLang() {
            const locale = String(this.$i18n?.locale || 'ru').toLowerCase()

            if (locale === 'kk') {
                return 'kz'
            }

            if (['ru', 'kz', 'en'].includes(locale)) {
                return locale
            }

            return 'ru'
        },
        embedUrl() {
            try {
                const url = new URL(this.normalizedUrl)
                url.searchParams.set('embed', 'chat-preview')
                url.searchParams.set('lang', this.fileExchangeLang)
                return url.toString()
            } catch (error) {
                return this.normalizedUrl
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.file-exchange-preview {
    width: 100%;
    max-width: none;
    margin: 8px 0 4px;
    border-radius: 16px;
    overflow: hidden;
    border: 1px solid #d7e6fb;
    background: #fff;
}

.file-exchange-preview__frame {
    display: block;
    width: 100%;
    height: 460px;
    border: 0;
    background: #fff;
}

.file-exchange-preview__link {
    display: block;
    padding: 10px 12px 12px;
    border-top: 1px solid #e8eef8;
    color: #1d65c0;
    font-size: 13px;
    line-height: 1.35;
    text-decoration: underline;
    word-break: break-word;
    background: #fff;
}
</style>
