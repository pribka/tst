<template>
    <div class="org_card preview">
        <div class="flex items-center">
            <div class="mr-5">{{ title }}</div>
            <flowy-drag-handle>
                <div class="cursor-move">
                    <i class="fi fi-rr-menu-burger"></i>
                </div>
            </flowy-drag-handle>
        </div>
    </div>
</template>

<script>
export default {
    name: 'TreeNode',
    props: {
        block: {
            type: Object,
            default: () => {}
        },
        title: {
            type: String,
            default: ''
        },
        description: {
            type: String,
            default: ''
        }
    }
}
</script>

<style lang="scss" scoped>
.org_card{
    border: 1px solid var(--border1);
    border-radius: var(--borderRadius);
    padding: 15px;
    position: relative;
    -webkit-user-select: none;
	-khtml-user-select: none;
	-moz-user-select: none;
	-ms-user-select: none;
	user-select: none;
}
</style>