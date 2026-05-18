<template>
    <a-spin :spinning="loading" size="small" :class="block && 'w-full'" class="ai_btn_spinner">
        <button
            v-bind="forwardedAttrs"
            :type="htmlType"
            :disabled="disabled || loading"
            class="ai-button"
            :class="buttonClasses"
            @click="handleClick">
            <span class="ai-button__content">
                <svg class="ai-button__icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                    <path d="M14.187 8.096L15 5.25L15.813 8.096C16.0231 8.83114 16.4171 9.50062 16.9577 10.0413C17.4984 10.5819 18.1679 10.9759 18.903 11.186L21.75 12L18.904 12.813C18.1689 13.0231 17.4994 13.4171 16.9587 13.9577C16.4181 14.4984 16.0241 15.1679 15.814 15.903L15 18.75L14.187 15.904C13.9769 15.1689 13.5829 14.4994 13.0423 13.9587C12.5016 13.4181 11.8321 13.0241 11.097 12.814L8.25 12L11.096 11.187C11.8311 10.9769 12.5006 10.5829 13.0413 10.0423C13.5819 9.50162 13.9759 8.83214 14.186 8.097L14.187 8.096Z" />
                    <path d="M6 14.25L5.741 15.285C5.59267 15.8785 5.28579 16.4206 4.85319 16.8532C4.42059 17.2858 3.87853 17.5927 3.285 17.741L2.25 18L3.285 18.259C3.87853 18.4073 4.42059 18.7142 4.85319 19.1468C5.28579 19.5794 5.59267 20.1215 5.741 20.715L6 21.75L6.259 20.715C6.40725 20.1216 6.71398 19.5796 7.14639 19.147C7.5788 18.7144 8.12065 18.4075 8.714 18.259L9.75 18L8.714 17.741C8.12065 17.5925 7.5788 17.2856 7.14639 16.853C6.71398 16.4204 6.40725 15.8784 6.259 15.285L6 14.25Z" />
                    <path d="M6.5 4L6.303 4.5915C6.24777 4.75718 6.15472 4.90774 6.03123 5.03123C5.90774 5.15472 5.75718 5.24777 5.5915 5.303L5 5.5L5.5915 5.697C5.75718 5.75223 5.90774 5.84528 6.03123 5.96877C6.15472 6.09226 6.24777 6.24282 6.303 6.4085L6.5 7L6.697 6.4085C6.75223 6.24282 6.84528 6.09226 6.96877 5.96877C7.09226 5.84528 7.24282 5.75223 7.4085 5.697L8 5.5L7.4085 5.303C7.24282 5.24777 7.09226 5.15472 6.96877 5.03123C6.84528 4.90774 6.75223 4.75718 6.697 4.5915L6.5 4Z" />
                </svg>
                <span class="ai-button__text"><slot /></span>
            </span>
        </button>
    </a-spin>
</template>

<script>
export default {
    name: 'AiButton',
    inheritAttrs: false,
    props: {
        type: {
            type: String,
            default: 'ui',
            validator: value => ['ui', 'primary'].includes(value)
        },
        size: {
            type: String,
            default: 'default',
            validator: value => ['small', 'default', 'large'].includes(value)
        },
        ghost: {
            type: Boolean,
            default: false
        },
        block: {
            type: Boolean,
            default: false
        },
        disabled: {
            type: Boolean,
            default: false
        },
        loading: {
            type: Boolean,
            default: false
        },
        htmlType: {
            type: String,
            default: 'button'
        }
    },
    computed: {
        buttonClasses() {
            return [
                `ai-button--${this.type}`,
                `ai-button--${this.size}`,
                this.ghost && 'ai-button--ghost',
                this.block && 'ai-button--block',
                this.loading && 'ai-button--loading'
            ]
        },
        forwardedAttrs() {
            const attrs = { ...this.$attrs }
            delete attrs.type
            return attrs
        }
    },
    methods: {
        handleClick(event) {
            if (this.disabled || this.loading) return
            this.$emit('click', event)
        }
    }
}
</script>

<style lang="scss" scoped>
.ai_btn_spinner{
    &.w-full{
        &::v-deep{
            .ant-spin-container{
                width: 100%;
            }
        }
    }
}
.ai-button {
    --ai-bg: #f0f1f6;
    --ai-bg-hover: var(--blue);
    --ai-color: var(--text);
    --ai-color-hover: #fff;
    --ai-border: #f0f1f6;
    --ai-border-hover: var(--blue);
    --ai-glow: rgba(71, 119, 255, 0.45);
    --ai-radius: 8px;
    --ai-transition: 0.25s;

    width: auto;
    max-width: 100%;
    border-radius: var(--ai-radius);
    border: 1px solid var(--ai-border);
    background: var(--ai-bg);
    color: var(--ai-color);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    cursor: pointer;
    position: relative;
    overflow: hidden;
    white-space: nowrap;
    user-select: none;
    transition: background-color var(--ai-transition), border-color var(--ai-transition), color var(--ai-transition), box-shadow var(--ai-transition);

    &:focus {
        outline: none;
    }

    &:focus-visible {
        box-shadow: 0 0 0 3px rgba(71, 119, 255, 0.2);
    }

    &:disabled:not(.ai-button--loading) {
        cursor: not-allowed;
        opacity: 0.6;
    }
}

.ai-button--small {
    min-height: 32px;
    padding: 0 12px;
    font-size: 13px;
    line-height: 1;
}

.ai-button--default {
    min-height: 36px;
    padding: 0 14px;
    font-size: 14px;
    line-height: 1;
}

.ai-button--large {
    min-height: 40px;
    padding: 0 16px;
    font-size: 15px;
    line-height: 1;
}

.ai-button--block {
    width: 100%;
}

.ai-button--ui {
    --ai-bg: #f0f1f6;
    --ai-color: var(--text);
    --ai-border: #f0f1f6;
    --ai-bg-hover: var(--blue);
    --ai-border-hover: var(--blue);
    --ai-color-hover: #fff;
}

.ai-button--primary {
    --ai-bg: var(--blue);
    --ai-color: #fff;
    --ai-border: var(--blue);
    --ai-bg-hover: var(--blue);
    --ai-border-hover: var(--blue);
    --ai-color-hover: #fff;
}

.ai-button--ghost {
    --ai-bg: transparent;
}

.ai-button--ui.ai-button--ghost {
    --ai-color: #888888;
    --ai-border: transparent;
}

.ai-button--primary.ai-button--ghost {
    --ai-color: var(--blue);
    --ai-border: rgba(71, 119, 255, 0.35);
}

.ai-button:not(:disabled):is(:hover, :focus-visible) {
    background: var(--ai-bg-hover);
    border-color: var(--ai-border-hover);
    color: var(--ai-color-hover);
    box-shadow: 0 10px 24px -16px var(--ai-glow);
}

.ai-button__content {
    position: relative;
    z-index: 2;
    display: inline-flex;
    align-items: center;
    gap: 8px;
}

.ai-button__text {
    display: inline-flex;
    align-items: center;
}

.ai-button__icon {
    width: 1.15em;
    height: 1.15em;
    flex: 0 0 1.15em;
}

.ai-button__icon path {
    fill: currentColor;
    stroke: currentColor;
    stroke-linecap: round;
    stroke-linejoin: round;
    transform-origin: center;
    transform-box: fill-box;
    transition: color var(--ai-transition);
}

.ai-button:not(:disabled):is(:hover, :focus-visible) .ai-button__icon path {
    animation-name: ai-bounce;
    animation-duration: 0.6s;
    animation-fill-mode: both;
}

.ai-button__icon path:nth-of-type(1) {
    --scale: 0.5;
    animation-delay: 0.12s;
}

.ai-button__icon path:nth-of-type(2) {
    --scale: 1.45;
    animation-delay: 0.22s;
}

.ai-button__icon path:nth-of-type(3) {
    --scale: 2.3;
    animation-delay: 0.34s;
}

@keyframes ai-bounce {
    35%,
    65% {
        transform: scale(var(--scale));
    }
}

</style>
