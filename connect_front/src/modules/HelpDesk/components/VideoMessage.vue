<template>
    <div class="video_msg" ref="root">
        <div v-if="!visible" class="video_msg__placeholder" @click="forceShow">
            <i class="fi fi-rr-play"></i>
            <span class="ml-2">{{ $t('helpdesk.video') }}</span>
        </div>
        <video
            v-else
            ref="player"
            class="video_msg__player"
            controls
            playsinline
            preload="metadata"
            @canplay="handleLoaded"
            @loadedmetadata="handleLoaded"
            @play="handlePlay"
            @error="error = true">
            <source :src="resolvedSrc" :type="mimeType"/>
        </video>
        <div v-if="error" class="video_msg__error">
            <a :href="resolvedSrc" target="_blank" rel="noopener">{{ $t('helpdesk.open_video') }}</a>
        </div>
    </div>
</template>

<script>
import { videoFormats } from '../utils/utils.js'

export default {
    props: {
        video: { type: Object, required: true },
        onLoaded: { type: Function, default: () => {} },
        onPlayStart: { type: Function, default: () => {} }
    },
    data() {
        return {
            visible: false,
            io: null,
            error: false
        }
    },
    computed: {
        rawPath() {
            return this.video.path || this.video.url || this.video.src || ''
        },
        resolvedSrc() {
            if (!this.rawPath) return ''
            try {
                const u = new URL(this.rawPath)
                return u.pathname + u.search
            } catch {
                return this.rawPath
            }
        },
        ext() {
            if (this.video.extension) return this.video.extension.toLowerCase()
            const n = this.video.name || ''
            const p = n.split('.')
            return p.length > 1 ? p.pop().toLowerCase() : ''
        },
        mimeType() {
            const map = {
                mp4: 'video/mp4',
                m4v: 'video/x-m4v',
                mov: 'video/quicktime',
                avi: 'video/x-msvideo',
                wmv: 'video/x-ms-wmv',
                flv: 'video/x-flv',
                webm: 'video/webm',
                mkv: 'video/x-matroska',
                '3gp': 'video/3gpp',
                '3g2': 'video/3gpp2',
                f4v: 'video/x-f4v',
                mpeg: 'video/mpeg',
                mpg: 'video/mpeg',
                mp2: 'video/mpeg',
                mpe: 'video/mpeg',
                mpv: 'video/mpeg',
                ts: 'video/mp2t',
                m2ts: 'video/mp2t',
                mts: 'video/mp2t',
                vob: 'video/dvd',
                ogv: 'video/ogg',
                divx: 'video/divx',
                xvid: 'video/xvid',
                rm: 'application/vnd.rn-realmedia',
                rmvb: 'application/vnd.rn-realmedia-vbr',
                asf: 'video/x-ms-asf',
                dv: 'video/x-dv',
                mxf: 'application/mxf'
            }
            if (videoFormats.includes(this.ext)) return map[this.ext] || 'video/mp4'
            return 'video/mp4'
        }
    },
    mounted() {
        const root = this.$refs.root
        if ('IntersectionObserver' in window && root) {
            this.io = new IntersectionObserver(entries => {
                const e = entries[0]
                if (e && e.isIntersecting) {
                    this.visible = true
                    this.io.disconnect()
                }
            }, { root: null, rootMargin: '200px 0px', threshold: 0.01 })
            this.io.observe(root)
        } else {
            this.visible = true
        }
    },
    beforeDestroy() {
        if (this.io) this.io.disconnect()
    },
    methods: {
        forceShow() {
            this.visible = true
        },
        handleLoaded() {
            this.error = false
            this.onLoaded && this.onLoaded()
        },
        handlePlay() {
            this.onPlayStart && this.onPlayStart(this.$refs.player)
        }
    }
}
</script>

<style lang="scss" scoped>
.video_msg{
    max-width: 400px;
    &:not(:last-child){
        margin-bottom: 10px;
    }
    .video_msg__player{
        width: 100%;
        height: auto;
        border-radius: 8px;
        max-height: 400px;
    }
    .video_msg__placeholder{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 220px;
        min-height: 120px;
        padding: 16px;
        border-radius: 8px;
        background: #f0f2f5;
        color: #555;
        cursor: pointer;
        user-select: none;
        transition: .2s
    }
    .video_msg__placeholder:hover{
        background: #e8ecfa;
        color: var(--blue)
    }
    .video_msg__error{
        margin-top: 6px;
        font-size: 12px;
        color: #888
    }
}
</style>
