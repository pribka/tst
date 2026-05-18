<template>
    <li class="activity_item">
        <div 
            class="link" 
            :class="redLink && 'red_link'"
            @click="$emit('click')">
            <i 
                v-if="icon.length"
                class="fi" 
                :class="icon" />
            <slot />
        </div>
    </li>
</template>

<script>
export default {
    name:'ActivityItem',
    props: {
        redLink: {
            type: Boolean,
            default: false
        },
        icon: {
            type: String,
            default: ''
        }
    }
}
</script>

<style lang="scss" scoped>
.activity_item{
    list-style: none;
    color: #000;
    user-select: none;
    .link{
        display: flex;
        align-items: center;
        font-weight: 300;
        background: rgba(255, 255, 255, 0.8);
        padding: 13px 15px;
        -webkit-backdrop-filter: saturate(180%) blur(20px);
        backdrop-filter: saturate(180%) blur(20px);
        &.red_link{
            color: var(--red);
        }
        .fi,
        .icon{
            margin-right: 10px;
            font-size: 22px;
            min-width: 22px;
            max-width: 22px;
        }
        span{
            font-size: 18px;
        }
    }
    &:not(:last-child){
        border-bottom: 1px solid var(--borderColor);
    }
}
</style>