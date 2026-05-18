<template>
    <a-popover
        placement="bottomRight"
        :getPopupContainer="getPopupContainer">
        <template slot="content">
            <div class="note_visors_popover">
                <div v-for="visor in hiddenVisors" :key="`hidden_${visor.id}`" class="note_visors_popover__item">
                    <Profiler
                        :user="visor"
                        :avatarSize="24"
                        hideSupportTag />
                </div>
            </div>
        </template>
        <div class="visor_more">+{{ hiddenVisorsCount }}</div>
    </a-popover>
</template>

<script>
export default {
    props: {
        hiddenVisorsCount: {
            type: Number,
            default: 0
        },
        hiddenVisors: {
            type: Array,
            default: () => []
        },
        getPopupContainer: {
            type: Function,
            default: null
        }
    }
}
</script>

<style scoped lang="scss">
.visor_more {
    margin-left: 6px;
    color: var(--text);
    font-size: 14px;
    line-height: 1;
    cursor: pointer;
}

.note_visors_popover {
    max-height: 260px;
    overflow: auto;
    min-width: 180px;
}

.note_visors_popover__item {
    &:not(:last-child) {
        margin-bottom: 8px;
    }
}
</style>
