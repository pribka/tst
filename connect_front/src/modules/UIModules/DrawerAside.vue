<template>
    <div class="drawer_aside">
        <slot />
    </div>
</template>

<style lang="scss" scoped>
.drawer_aside{
    padding: 20px;
    background: #f7f9fc;
    border-radius: 12px;
    color: var(--text);
    &:not(:last-child){
        margin-bottom: 15px;
    }
}
</style>