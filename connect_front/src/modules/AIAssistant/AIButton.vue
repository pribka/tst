<template>
    <div class="ai-button-wrap" :class="isMobile || 'mr-6'">
        <div 
            class="ai-button flex items-center cursor-pointer select-none"
            @click="handleAIButtonClick">
            <div v-if="isMobile" :class="isMobile || 'mr-2'">
                <a-avatar 
                    :src="ai_avatar" 
                    avResize
                    class="cursor-pointer"
                    shape="square"
                    :size="32" />
            </div>
            <div
                v-else
                class="flex items-center"
                @mouseenter="playAvatarAnimation"
                @mouseleave="stopAvatarAnimation">
                <div :class="isMobile || 'mr-2'">
                    <div class="ai-avatar-wrap" aria-hidden="true">
                        <video
                            v-if="sparklesAnimationSrc"
                            ref="avatarAnimation"
                            class="ai-avatar-animation"
                            :src="sparklesAnimationSrc"
                            muted
                            loop
                            playsinline
                            @loadedmetadata="setInitialAvatarFrame"
                            preload="auto"></video>
                    </div>
                </div>
                <div v-if="!isMobile" class="bt_wrapper">
                    <div class="bt_wrapper__name">{{ ai_name }}</div>
                    <div class="bt_wrapper__placeholder">{{ ai_placeholder }}</div>
                </div>
            </div>
        </div>

        <transition name="task-tooltip-fade">
            <div
                v-if="showTaskTooltip"
                class="task-tooltip"
                @click="handleTaskTooltipClick">
                <button
                    type="button"
                    class="task-tooltip__close"
                    aria-label="Close"
                    @click.stop="closeTaskTooltip">
                    <i class="fi fi-rr-cross-small"></i>
                </button>
                <video
                    v-if="helloBotAnimationWebmSrc || helloBotAnimationMovSrc"
                    class="task-tooltip__anim"
                    autoplay
                    loop
                    muted
                    playsinline>
                    <source v-if="helloBotAnimationWebmSrc" :src="helloBotAnimationWebmSrc" type="video/webm">
                    <source v-if="helloBotAnimationMovSrc" :src="helloBotAnimationMovSrc" type="video/quicktime">
                </video>
                <div class="task-tooltip__text-wrap">
                    <transition-group
                        name="task-tooltip-text-slide"
                        tag="div"
                        class="task-tooltip__text-group">
                        <div
                            :key="currentTooltipConfig.textKey"
                            class="task-tooltip__text">
                            {{ $t(currentTooltipConfig.textKey) }}
                        </div>
                    </transition-group>
                </div>
            </div>
        </transition>
    </div>
</template>

<script>
import axios from '@/config/axios'
import { vars } from './utils.js'

const CHAT_AI_TOOLTIP_SYNC_KEY = 'chat_ai_tooltip_sync'

export default {
    data() {
        return {
            ai_name: vars.ai_name,
            ai_placeholder: vars.ai_placeholder,
            sparklesAnimationSrc: '',
            helloBotAnimationWebmSrc: '',
            helloBotAnimationMovSrc: '',
            taskTooltipUpdating: false,
            ai_avatar: vars.ai_avatar
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        user() {
            return this.$store.state.user.user || {}
        },
        currentTooltipConfig() {
            const tooltipConfigByRoute = {
                tasks: {
                    tooltipKey: 'task',
                    textKey: 'ai_assistant.task_tooltip'
                },
                meetings: {
                    tooltipKey: 'meeting',
                    textKey: 'ai_assistant.meeting_tooltip'
                },
                calendar: {
                    tooltipKey: 'event',
                    textKey: 'ai_assistant.event_tooltip'
                },
                reports: {
                    tooltipKey: 'reports',
                    textKey: 'ai_assistant.reports_tooltip'
                },
                'reports-dashboards': {
                    tooltipKey: 'reports',
                    textKey: 'ai_assistant.reports_tooltip'
                },
                'reports-templates': {
                    tooltipKey: 'reports',
                    textKey: 'ai_assistant.reports_tooltip'
                }
            }

            return tooltipConfigByRoute[this.$route?.name] || null
        },
        showTaskTooltip() {
            if (!this.currentTooltipConfig) {
                return false
            }

            if (
                this.currentTooltipConfig.tooltipKey === 'reports' &&
                this.$route?.query?.ai_chat
            ) {
                return false
            }

            const tooltipKey = this.currentTooltipConfig.tooltipKey
            return this.user?.chat_ai_tooltip?.[tooltipKey] === false
        }
    },
    mounted() {
        this.loadSparklesAnimation()
        this.loadHelloBotAnimation()
        this.stopAvatarAnimation()
        window.addEventListener('storage', this.handleTooltipStorageSync)
    },
    beforeDestroy() {
        window.removeEventListener('storage', this.handleTooltipStorageSync)
    },
    methods: {
        async loadSparklesAnimation() {
            try {
                if (this.$store.state.isSafari) {
                    this.sparklesAnimationSrc = `${process.env.BASE_URL}animate/sparkles_loop.mov`
                    return
                }
                const animationModule = await import('@/assets/animate/sparkles_loop.webm')
                this.sparklesAnimationSrc = animationModule?.default || animationModule || ''
            } catch (error) {
                this.sparklesAnimationSrc = ''
            }
        },
        async loadHelloBotAnimation() {
            this.helloBotAnimationMovSrc = `${process.env.BASE_URL}animate/hello_bot.mov`

            try {
                const animationModule = await import('@/assets/animate/hello_bot.webm')
                this.helloBotAnimationWebmSrc = animationModule?.default || animationModule || ''
            } catch (error) {
                this.helloBotAnimationWebmSrc = ''
            }
        },
        playAvatarAnimation() {
            if (this.isMobile) {
                return
            }

            const animation = this.$refs.avatarAnimation

            if (!animation) {
                return
            }

            animation.play().catch(() => {})
        },
        stopAvatarAnimation() {
            const animation = this.$refs.avatarAnimation

            if (!animation) {
                return
            }

            animation.pause()
        },
        setInitialAvatarFrame() {
            const animation = this.$refs.avatarAnimation

            if (!animation || !Number.isFinite(animation.duration) || animation.duration <= 0) {
                return
            }

            animation.currentTime = 0.6
            animation.pause()
        },
        openAIDrawer() {
            const query = Object.assign({}, this.$route.query)
            if(!query.ai_chat) {
                query.ai_chat = true
                this.$router.push({query})
            }
        },
        syncTooltipState(tooltipKey) {
            try {
                localStorage.setItem(CHAT_AI_TOOLTIP_SYNC_KEY, JSON.stringify({
                    tooltipKey,
                    value: true,
                    ts: Date.now()
                }))
            } catch (error) {
                console.error('Failed to sync chat_ai_tooltip across tabs', error)
            }
        },
        handleTooltipStorageSync(event) {
            if (event.key !== CHAT_AI_TOOLTIP_SYNC_KEY || !event.newValue) {
                return
            }

            try {
                const payload = JSON.parse(event.newValue)
                const tooltipKey = payload?.tooltipKey

                if (!tooltipKey || payload?.value !== true) {
                    return
                }

                const chatAiTooltip = {
                    ...(this.user?.chat_ai_tooltip || {}),
                    [tooltipKey]: true
                }

                this.$store.commit('user/SET_USER', {
                    chat_ai_tooltip: chatAiTooltip
                })
            } catch (error) {
                console.error('Failed to apply chat_ai_tooltip sync', error)
            }
        },
        async handleAIButtonClick() {
            this.openAIDrawer()

            if (this.showTaskTooltip) {
                await this.markTaskTooltipAsSeen()
            }
        },
        async markTaskTooltipAsSeen() {
            const tooltipKey = this.currentTooltipConfig?.tooltipKey

            if (!tooltipKey || this.taskTooltipUpdating || this.user?.chat_ai_tooltip?.[tooltipKey] === true) {
                return
            }

            this.taskTooltipUpdating = true

            const chatAiTooltip = {
                ...(this.user?.chat_ai_tooltip || {}),
                [tooltipKey]: true
            }

            this.$store.commit('user/SET_USER', {
                chat_ai_tooltip: chatAiTooltip
            })
            this.syncTooltipState(tooltipKey)

            try {
                await axios.patch('/users/chat_ai_tooltip/', {
                    [tooltipKey]: true
                })
            } catch (error) {
                console.error(`Failed to update chat_ai_tooltip.${tooltipKey}`, error)
            } finally {
                this.taskTooltipUpdating = false
            }
        },
        async handleTaskTooltipClick() {
            this.openAIDrawer()
            await this.markTaskTooltipAsSeen()
        },
        async closeTaskTooltip() {
            await this.markTaskTooltipAsSeen()
        }
    },
}
</script>

<style lang="scss" scoped>
.ai-button-wrap {
    position: relative;
}

.ai-avatar-wrap {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    overflow: hidden;
    background: linear-gradient(135deg, #5f84ff 0%, #e1a34b 100%);
}

.ai-avatar-animation {
    display: block;
    width: 100%;
    height: 100%;
    object-fit: cover;
    mix-blend-mode: screen;
    transform: scale(1.5);
    transform-origin: center;
}

.bt_wrapper{
    &__name{
        font-size: 14px;
        line-height: 16px;
    }
    &__placeholder{
        color: #888888;
        font-size: 12px;
        line-height: 16px;
    }
}

@media (max-width: 1280px) {
    .ai-button-wrap.mr-6{
        margin-right: 0.75rem;
    }

    .bt_wrapper{
        display: none;
    }

    .ai-button > .flex > .mr-2{
        margin-right: 0;
    }
}

.task-tooltip {
    position: absolute;
    top: calc(100% + 12px);
    left: 50%;
    z-index: 20;
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 245px;
    max-width: 320px;
    padding: 12px 24px 12px 12px;
    border: 1px solid #d9e1ff;
    border-radius: 18px;
    background: linear-gradient(180deg, #ffffff 0%, #f5f8ff 100%);
    box-shadow: 0 12px 30px rgba(66, 85, 141, 0.16);
    cursor: pointer;
    transform: translateX(-50%);

    &::before {
        content: '';
        position: absolute;
        top: -8px;
        left: 50%;
        width: 16px;
        height: 16px;
        background: #ffffff;
        border-top: 1px solid #d9e1ff;
        border-left: 1px solid #d9e1ff;
        transform: translateX(-50%) rotate(45deg);
    }

    &__anim {
        position: relative;
        z-index: 1;
        width: 66px;
        min-width: 66px;
        height: 66px;
        object-fit: cover;
    }

    &__text-wrap {
        position: relative;
        z-index: 1;
        width: 170px;
        max-width: 170px;
        overflow: hidden;
    }

    &__text-group {
        position: relative;
    }

    &__text {
        position: relative;
        color: #2f3a58;
        font-size: 13px;
        line-height: 19px;
        font-weight: 500;
        width: 100%;
    }

    &__close {
        position: absolute;
        top: 10px;
        right: 10px;
        z-index: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 18px;
        height: 18px;
        padding: 0;
        border: none;
        border-radius: 50%;
        background: transparent;
        color: #7480a5;
        cursor: pointer;
        font-size: 16px;
    }
}

.task-tooltip-fade-enter-active,
.task-tooltip-fade-leave-active {
    transition: opacity .2s ease, transform .2s ease;
}

.task-tooltip-fade-enter,
.task-tooltip-fade-leave-to {
    opacity: 0;
    transform: translateX(-50%) translateY(-4px);
}

.task-tooltip-text-slide-enter-active,
.task-tooltip-text-slide-leave-active {
    transition: transform .28s ease, opacity .28s ease;
}

.task-tooltip-text-slide-enter {
    opacity: 0;
    transform: translateX(-18px);
}

.task-tooltip-text-slide-leave-to {
    opacity: 0;
    transform: translateX(18px);
}

.task-tooltip-text-slide-leave-active {
    position: absolute;
    top: 0;
    left: 0;
}
</style>
