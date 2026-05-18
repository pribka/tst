<template>
    <div v-if="isAudio" class="audio_wrap">
        <audio
            v-if="blobUrl"
            ref="audio"
            :src="blobUrl"
            controls
            preload="metadata"
            @loadedmetadata="onMetaLoaded"
            @play="onPlay"
            @ended="onEnded"/>
        <div v-else class="w-full message_loading rounded flex items-center px-3">
            <a-spin size="small" class="w-full" />
        </div>
    </div>
</template>

<script>
import { audioFormats } from '../utils/utils.js'
import axios from '@/config/axiosClear.js'
export default {
    props: {
        audio: { type: Object, required: true },
        onLoaded: { type: Function, default: () => {} },
        onPlayStart: { type: Function, default: () => {} }
    },
    data() {
        return {
            blobUrl: null,
            autoPlayPending: false
        }
    },
    computed: {
        isAudio() {
            return audioFormats.includes(this.audio.extension?.toLowerCase())
        }
    },
    methods: {
        async loadAudio() {
            if (!this.isAudio || !this.audio?.path) return
            try {
                const url = this.audio.path.startsWith('http') ? new URL(this.audio.path).pathname + new URL(this.audio.path).search : this.audio.path
                const res = await axios.get(url, { responseType: 'blob', withCredentials: true })
                const type = res.headers['content-type'] || `audio/${this.audio.extension}`
                const blob = new Blob([res.data], { type })
                this.blobUrl = URL.createObjectURL(blob)
                if (this.autoPlayPending) {
                    this.$nextTick(() => {
                        this.play()
                        this.autoPlayPending = false
                    })
                }
            } catch (e) {
                this.blobUrl = null
            }
        },
        onMetaLoaded() {
            this.$nextTick(() => this.onLoaded())
        },
        play() {
            if (!this.blobUrl) {
                this.autoPlayPending = true
                this.loadAudio()
                return
            }
            this.$refs.audio && this.$refs.audio.play()
        },
        pause() {
            this.$refs.audio && this.$refs.audio.pause()
        },
        stopOthers() {
            const list = window.__chatAudioRegistry || []
            list.forEach(vm => {
                if (vm && vm !== this) vm.pause()
            })
        },
        onPlay() {
            this.stopOthers()
            this.onPlayStart(this.$el)
        },
        onEnded() {
            const list = window.__chatAudioRegistry || []
            const idx = list.indexOf(this)
            const next = idx >= 0 ? list.slice(idx + 1).find(vm => vm && vm.isAudio) : null
            if (next) next.play()
        }
    },
    mounted() {
        if (!window.__chatAudioRegistry) window.__chatAudioRegistry = []
        window.__chatAudioRegistry.push(this)
        this.loadAudio()
    },
    beforeDestroy() {
        if (this.blobUrl) URL.revokeObjectURL(this.blobUrl)
        const list = window.__chatAudioRegistry || []
        const i = list.indexOf(this)
        if (i !== -1) list.splice(i, 1)
    }
}
</script>

<style lang="scss" scoped>
.message_loading{
    background: #F8F9FD;
    min-height: 40px;
}
.audio_wrap{
    &:not(:last-child){
        margin-bottom: 10px
    }
}
</style>




