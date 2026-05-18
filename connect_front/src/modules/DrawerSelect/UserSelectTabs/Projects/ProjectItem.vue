<template>
    <div class="project-item-wrap">
        <div class="project-panel" :class="selectedProjectID === project.id && 'selected'">
            <div class="logo">
                <a-avatar
                    icon="team"
                    :size="24"
                    :src="project.logo" />
            </div>
            <div
                class="project-name"
                @click.stop="toggleSelect">
                <span>{{ project.name || $t('Not specified') }}</span>
            </div>
        </div>
    </div>
</template>
  
<script>
export default {
    name: 'ProjectItem',
    props: {
        project: {
            type: Object,
            required: true
        },
        selectedProjectID: {
            type: [String, null],
            default: null
        }
    },
    data() {
        return {
            selected: false,
            loading: false
        }
    },
    methods: {
        toggleSelect() {
            this.selected = !this.selected
            this.$emit('select', { key: this.project.id, selected: this.selected })
        }
    }
}
</script>
  
<style lang="scss" scoped>
.project-item-wrap {
    margin: 6px 0;
}
.project-panel {
    display: flex;
    align-items: center;
    padding: 8px;
    border-radius: 8px;
    gap: 8px;
    &:hover{
        background: rgb(240, 241, 247, 1);
    }
    &:not(:last-child){
        margin-bottom: 4px;
    }
}
  .project-name {
    flex: 1;
    cursor: pointer;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 1.5;
    max-height: calc(2 * 1.5em);
    word-break: break-word;
}
.project-panel.selected {
    background: rgba(240, 241, 247, 1);
}
.children {
    margin-left: 28px;
    margin-top: 4px;
    transition: height 0.15s;
}
</style>
  