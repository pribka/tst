<template>
    <div>
        <div class="visor_more" @click="visible = true">+{{ hiddenVisorsCount }}</div>

        <a-modal
            :visible="visible"
            title="Наблюдатели"
            :footer="null"
            destroyOnClose
            @cancel="visible = false">
            <div class="note_visors_popover">
                <div v-for="visor in hiddenVisors" :key="`hidden_modal_${visor.id}`" class="note_visors_popover__item">
                    <Profiler
                        :user="visor"
                        :avatarSize="24"
                        hideSupportTag />
                </div>
            </div>
        </a-modal>
    </div>
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
        }
    },
    data() {
        return {
            visible: false
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
