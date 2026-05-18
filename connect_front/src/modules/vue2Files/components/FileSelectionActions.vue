<template>
    <transition name="file-selection-actions">
        <div
            v-if="visible"
            class="file_selection_actions"
            :class="isMobile && 'mobile'">
            <div class="file_selection_actions__count">
                <div class="file_selection_actions__count_badge">
                    {{ count }}
                </div>
                <div class="file_selection_actions__count_label">
                    {{ title }}
                </div>
            </div>

            <div class="file_selection_actions__divider"></div>

            <div class="file_selection_actions__buttons">
                <button
                    v-if="canDownload"
                    type="button"
                    class="file_selection_actions__button"
                    @click="$emit('download')">
                    <i class="fi fi-rr-download"></i>
                    <span>{{ downloadLabel }}</span>
                </button>

                <button
                    v-if="canMove"
                    type="button"
                    class="file_selection_actions__button"
                    @click="$emit('move')">
                    <i class="fi fi-rr-arrows-repeat"></i>
                    <span>{{ moveLabel }}</span>
                </button>

                <button
                    v-if="canAttach"
                    type="button"
                    class="file_selection_actions__button"
                    @click="$emit('attach')">
                    <i class="fi fi-rr-clip"></i>
                    <span>{{ attachLabel }}</span>
                </button>

                <button
                    v-if="canRestore"
                    type="button"
                    class="file_selection_actions__button"
                    @click="$emit('restore')">
                    <i class="fi fi-rr-time-past"></i>
                    <span>{{ restoreLabel }}</span>
                </button>

                <button
                    v-if="canDelete"
                    type="button"
                    class="file_selection_actions__button file_selection_actions__button--danger"
                    @click="$emit('delete')">
                    <i class="fi fi-rr-trash"></i>
                    <span>{{ deleteLabel }}</span>
                </button>
            </div>

            <button
                type="button"
                class="file_selection_actions__clear"
                @click="$emit('clear')">
                <i class="fi fi-rr-cross"></i>
            </button>
        </div>
    </transition>
</template>

<script>
export default {
    name: 'FileSelectionActions',
    props: {
        visible: {
            type: Boolean,
            default: false
        },
        count: {
            type: Number,
            default: 0
        },
        title: {
            type: String,
            default: ''
        },
        canMove: {
            type: Boolean,
            default: false
        },
        canDelete: {
            type: Boolean,
            default: false
        },
        canRestore: {
            type: Boolean,
            default: false
        },
        canAttach: {
            type: Boolean,
            default: false
        },
        canDownload: {
            type: Boolean,
            default: false
        },
        moveLabel: {
            type: String,
            default: ''
        },
        deleteLabel: {
            type: String,
            default: ''
        },
        restoreLabel: {
            type: String,
            default: ''
        },
        attachLabel: {
            type: String,
            default: ''
        },
        downloadLabel: {
            type: String,
            default: ''
        },
        isMobile: {
            type: Boolean,
            default: false
        }
    }
}
</script>

<style scoped lang="scss">
.file_selection_actions {
    position: fixed;
    z-index: 900;
    bottom: 36px;
    left: 50%;
    display: flex;
    align-items: center;
    gap: 14px;
    min-height: 54px;
    max-width: calc(100vw - 48px);
    padding: 10px 14px;
    border: 1px solid rgba(38, 50, 72, 0.24);
    border-radius: 8px;
    background: #121a2b;
    box-shadow: 0 24px 48px rgba(15, 23, 42, 0.32);
    transform: translateX(-50%);
}

.file_selection_actions.mobile {
    right: 8px;
    left: 8px;
    bottom: 8px;
    gap: 10px;
    flex-wrap: wrap;
    justify-content: space-between;
    max-width: none;
    min-height: auto;
    padding: 10px 12px;
    transform: none;
}

.file_selection_actions__count {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: max-content;
}

.file_selection_actions__count_badge {
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 30px;
    height: 30px;
    padding: 0 8px;
    border-radius: 999px;
    background: #325bff;
    color: #fff;
    font-size: 13px;
    font-weight: 700;
}

.file_selection_actions__count_label {
    font-size: 14px;
    font-weight: 600;
    color: #f8fafc;
    white-space: nowrap;
}

.file_selection_actions__divider {
    width: 1px;
    align-self: stretch;
    background: rgba(255, 255, 255, 0.12);
}

.file_selection_actions.mobile .file_selection_actions__divider {
    display: none;
}

.file_selection_actions__buttons {
    display: flex;
    align-items: center;
    gap: 2px;
    flex-wrap: nowrap;
}

.file_selection_actions.mobile .file_selection_actions__count {
    gap: 6px;
    min-width: 0;
}

.file_selection_actions.mobile .file_selection_actions__count_badge {
    min-width: 28px;
    height: 28px;
    font-size: 12px;
}

.file_selection_actions.mobile .file_selection_actions__count_label {
    font-size: 13px;
}

.file_selection_actions.mobile .file_selection_actions__buttons {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    width: 100%;
    gap: 6px;
    flex: 1 1 100%;
    order: 3;
}

.file_selection_actions__button {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    min-height: 34px;
    padding: 0 10px;
    border: none;
    border-radius: 8px;
    background: transparent;
    color: #e5edf8;
    font-size: 14px;
    white-space: nowrap;
    cursor: pointer;
    transition: background-color 0.2s ease, color 0.2s ease;
}

.file_selection_actions.mobile .file_selection_actions__button {
    justify-content: center;
    min-height: 32px;
    padding: 0 8px;
    background: rgba(255, 255, 255, 0.06);
    font-size: 13px;
}

.file_selection_actions.mobile .file_selection_actions__button span {
    overflow: hidden;
    text-overflow: ellipsis;
}

.file_selection_actions__button:hover {
    background: rgba(255, 255, 255, 0.08);
}

.file_selection_actions__button--danger {
    color: #ffb4b4;
}

.file_selection_actions__clear {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 34px;
    height: 34px;
    border: none;
    border-radius: 8px;
    background: transparent;
    color: #cbd5e1;
    cursor: pointer;
    transition: background-color 0.2s ease, color 0.2s ease;
}

.file_selection_actions__clear:hover {
    background: rgba(255, 255, 255, 0.08);
    color: #fff;
}

.file_selection_actions.mobile .file_selection_actions__clear {
    width: 30px;
    height: 30px;
    margin-left: auto;
}

.file-selection-actions-enter-active,
.file-selection-actions-leave-active {
    transition: opacity 0.2s ease, transform 0.2s ease;
}

.file-selection-actions-enter,
.file-selection-actions-leave-to {
    opacity: 0;
    transform: translate(-50%, 12px);
}

.mobile.file-selection-actions-enter,
.mobile.file-selection-actions-leave-to {
    transform: translateY(12px);
}
</style>
