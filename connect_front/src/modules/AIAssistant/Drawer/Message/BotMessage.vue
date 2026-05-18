<template>
    <div class="chat_message w-full">
        <div
            v-if="displayText"
            class="message_text"
            :class="isLive && 'message_text--live'">
            <video
                v-if="isLive && liveAnimationSrc"
                class="message_text__anim"
                :src="liveAnimationSrc"
                autoplay
                loop
                muted
                playsinline />
            <span v-html="displayText" />
        </div>
        <div v-else-if="isLive" class="message_text message_text--live">
            ...
        </div>

        <template v-if="message.intents && message.intents.length">
            <IntentsSwitch
                v-for="(intents, index) in message.intents"
                :key="intents.id"
                :messageIndex="messageIndex"
                :intents="intents"
                :intentIndex="index"
                :message="message" />
        </template>
    </div>
</template>

<script>
import IntentsSwitch from './IntentsSwitch.vue'

export default {
    components: {
        IntentsSwitch
    },
    data() {
        return {
            liveAnimationSrc: ''
        }
    },
    props: {
        message: {
            type: Object,
            required: true
        },
        messageIndex: {
            type: Number,
            default: 0
        }
    },
    computed: {
        liveStageText() {
            const stageLabels = {
                classify: '\u041F\u043E\u043D\u0438\u043C\u0430\u044E \u0437\u0430\u043F\u0440\u043E\u0441',
                parse_intents: '\u0418\u0437\u0432\u043B\u0435\u043A\u0430\u044E \u0434\u0435\u0442\u0430\u043B\u0438',
                generate_reply: '\u0424\u043E\u0440\u043C\u0438\u0440\u0443\u044E \u043E\u0442\u0432\u0435\u0442'
            }
            const statusLabels = {
                processing_classify: stageLabels.classify,
                processing_intent: stageLabels.parse_intents,
                generating_reply: stageLabels.generate_reply
            }

            return stageLabels[this.message.stream_stage]
                || statusLabels[this.message.status]
                || this.message.stream_stage_text
                || (this.isLive ? this.$t('ai_assistant.thinking') : '')
        },
        displayText() {
            return this.message.text || this.liveStageText
        },
        isLive() {
            return ['accepted', 'stage', 'streaming'].includes(this.message.stream_state)
                || ['queued', 'processing_classify', 'processing_intent', 'generating_reply'].includes(this.message.status)
        }
    },
    created() {
        this.loadLiveAnimation()
    },
    methods: {
        async loadLiveAnimation() {
            try {
                if (this.$store.state.isSafari) {
                    this.liveAnimationSrc = `${process.env.BASE_URL}animate/AI_mov.mov`
                    return
                }

                const animationModule = await import('@/assets/animate/AI.webm')
                this.liveAnimationSrc = animationModule?.default || animationModule || ''
            } catch (error) {
                this.liveAnimationSrc = ''
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.message_text{
    display: inline-flex;
    align-items: center;
    font-size: 14px;
    word-break: break-word;
    line-height: 22px;
    margin-bottom: 10px;

    &__anim{
        width: 20px;
        min-width: 20px;
        height: 20px;
        margin-right: 8px;
        object-fit: contain;
    }

    &--live{
        color: #5c6470;
        position: relative;
    }
}

@keyframes ai-live-pulse {
    0%, 100% {
        opacity: .25;
        transform: scale(.9);
    }
    50% {
        opacity: 1;
        transform: scale(1.1);
    }
}
</style>
