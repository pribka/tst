<template>
    <div
        class="voice_player"
        :data-chat-uid="chatUid || ''"
        :data-message-uid="messageUid || ''"
        :data-instance-id="instanceId">
        <audio
            ref="audio"
            preload="metadata"
            :src="src"
            @loadedmetadata="onLoadedMetadata"
            @pause="onPause"
            @timeupdate="onTimeUpdate"
            @ended="onEnded"></audio>

        <button type="button" class="voice_player__toggle" @click="togglePlayback">
            <a-icon :type="isPlaying ? 'pause' : 'caret-right'" />
        </button>

        <div class="voice_player__wave" @click="seekByClick">
            <span
                v-for="(bar, index) in bars"
                :key="index"
                class="voice_player__bar"
                :class="{ 'voice_player__bar--played': isPlayed(index) }"
                :style="{ height: `${bar}px` }"></span>
        </div>

        <div class="voice_player__time">
            {{ formattedTime }}
        </div>
    </div>
</template>

<script>
import { buildFallbackVoiceBars, formatVoiceDuration } from '@/utils/voice'
import {
    playNextVoiceMessage,
    registerVoicePlayer,
    requestVoicePlayback,
    unregisterVoicePlayer
} from '@/utils/voicePlayback'

const DEFAULT_BAR_COUNT = 40

export default {
    name: 'VoiceMessagePlayer',
    props: {
        src: {
            type: String,
            required: true
        },
        chatUid: {
            type: [String, Number],
            default: ''
        },
        messageUid: {
            type: [String, Number],
            default: ''
        }
    },
    data() {
        return {
            instanceId: `voice_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`,
            isPlaying: false,
            currentTime: 0,
            duration: 0,
            decodedDuration: 0,
            bars: buildFallbackVoiceBars(DEFAULT_BAR_COUNT)
        }
    },
    computed: {
        playbackDuration() {
            return this.normalizeTime(this.duration) || this.normalizeTime(this.decodedDuration)
        },
        formattedTime() {
            return formatVoiceDuration(this.playbackDuration || this.currentTime)
        }
    },
    mounted() {
        registerVoicePlayer({
            instanceId: this.instanceId,
            chatUid: this.chatUid,
            messageUid: this.messageUid,
            play: this.playAudio,
            pause: this.pauseAudio
        })
        this.generateWaveform()
    },
    beforeDestroy() {
        unregisterVoicePlayer(this.instanceId)
        this.pauseAudio({ reset: true, source: 'destroy' })
    },
    methods: {
        normalizeTime(value) {
            const normalized = Number(value)
            return Number.isFinite(normalized) && normalized > 0 ? normalized : 0
        },
        getResolvedDuration(audio = this.$refs.audio) {
            if (!audio) return 0

            const directDuration = this.normalizeTime(audio.duration)
            if (directDuration) {
                return directDuration
            }

            if (audio.seekable?.length) {
                const seekableDuration = this.normalizeTime(audio.seekable.end(audio.seekable.length - 1))
                if (seekableDuration) {
                    return seekableDuration
                }
            }

            return 0
        },
        onLoadedMetadata() {
            this.duration = this.getResolvedDuration()
        },
        onTimeUpdate() {
            this.currentTime = this.normalizeTime(this.$refs.audio?.currentTime)
            this.duration = this.getResolvedDuration()
        },
        onPause() {
            this.isPlaying = false
        },
        onEnded() {
            this.isPlaying = false
            this.currentTime = 0
            this.$nextTick(() => {
                playNextVoiceMessage(this.instanceId)
            })
        },
        pauseAudio(options = {}) {
            const audio = this.$refs.audio
            if (!audio) return

            if (!audio.paused) {
                audio.pause()
            }

            this.isPlaying = false

            if (options.reset) {
                this.currentTime = 0
                audio.currentTime = 0
                audio.src = ''
            }
        },
        async playAudio() {
            const audio = this.$refs.audio
            if (!audio) return false

            try {
                requestVoicePlayback(this.instanceId)
                await audio.play()
                this.isPlaying = true
                return true
            } catch (error) {
                this.isPlaying = false
                return false
            }
        },
        async togglePlayback() {
            const audio = this.$refs.audio
            if (!audio) return

            if (this.isPlaying && !audio.paused) {
                this.pauseAudio({ source: 'toggle' })
                return
            }

            await this.playAudio()
        },
        isPlayed(index) {
            if (!this.playbackDuration) return false
            return index / this.bars.length <= this.currentTime / this.playbackDuration
        },
        seekByClick(event) {
            const audio = this.$refs.audio
            if (!audio || !this.playbackDuration) return

            const rect = event.currentTarget.getBoundingClientRect()
            if (!rect.width) return

            const ratio = Math.min(1, Math.max(0, (event.clientX - rect.left) / rect.width))
            audio.currentTime = this.playbackDuration * ratio
            this.currentTime = this.normalizeTime(audio.currentTime)
        },
        async generateWaveform() {
            const AudioContextCtor = window.AudioContext || window.webkitAudioContext
            if (!AudioContextCtor) return

            let audioContext = null

            try {
                const response = await fetch(this.src, { credentials: 'include' })
                if (!response.ok) {
                    throw new Error('Failed to load audio')
                }

                const buffer = await response.arrayBuffer()

                audioContext = new AudioContextCtor()
                const decoded = await new Promise((resolve, reject) => {
                    audioContext.decodeAudioData(buffer.slice(0), resolve, reject)
                })
                this.decodedDuration = this.normalizeTime(decoded.duration)

                const channelData = decoded.getChannelData(0)
                const blockSize = Math.max(1, Math.floor(channelData.length / DEFAULT_BAR_COUNT))
                const nextBars = []
                let maxPeak = 0

                for (let i = 0; i < DEFAULT_BAR_COUNT; i += 1) {
                    const start = i * blockSize
                    const end = Math.min(start + blockSize, channelData.length)
                    let peak = 0
                    let sum = 0

                    for (let j = start; j < end; j += 1) {
                        const value = Math.abs(channelData[j])
                        sum += value
                        if (value > peak) {
                            peak = value
                        }
                    }

                    const average = end > start ? sum / (end - start) : 0
                    const combined = (peak * 0.7) + (average * 0.3)

                    if (combined > maxPeak) {
                        maxPeak = combined
                    }

                    nextBars.push(combined)
                }

                if (!maxPeak) {
                    this.bars = buildFallbackVoiceBars(DEFAULT_BAR_COUNT)
                    return
                }

                this.bars = nextBars.map(value => {
                    const normalized = value / maxPeak
                    return Math.max(8, Math.min(36, Math.round(normalized * 36)))
                })
            } catch (error) {
                this.bars = buildFallbackVoiceBars(DEFAULT_BAR_COUNT)
            } finally {
                if (audioContext && typeof audioContext.close === 'function') {
                    audioContext.close().catch(() => {})
                }
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.voice_player{
    width: 100%;
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 0;
    padding: 10px 12px;
    border-radius: 16px;
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(238, 242, 248, 0.98));
    border: 1px solid rgba(15, 23, 42, 0.08);
}

.voice_player__toggle{
    flex: 0 0 auto;
    width: 34px;
    height: 34px;
    border-radius: 50%;
    border: 0;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: #416ce9;
    color: #fff;
    cursor: pointer;
}

.voice_player__wave{
    flex: 1 1 auto;
    min-width: 0;
    height: 40px;
    display: flex;
    align-items: center;
    gap: 3px;
    cursor: pointer;
}

.voice_player__bar{
    flex: 1 1 0;
    min-width: 3px;
    border-radius: 999px;
    background: rgba(65, 108, 233, 0.22);
    transition: background 0.18s ease;
}

.voice_player__bar--played{
    background: #416ce9;
}

.voice_player__time{
    flex: 0 0 auto;
    width: 44px;
    text-align: right;
    font-size: 12px;
    line-height: 1;
    color: #5f6b85;
    font-variant-numeric: tabular-nums;
}

@media (max-width: 640px) {
    .voice_player{
        gap: 8px;
        padding: 8px 10px;
        border-radius: 14px;
    }

    .voice_player__toggle{
        width: 30px;
        height: 30px;
    }

    .voice_player__wave{
        height: 32px;
        gap: 2px;
    }

    .voice_player__bar{
        min-width: 2px;
    }

    .voice_player__time{
        width: 36px;
        font-size: 11px;
    }
}
</style>
