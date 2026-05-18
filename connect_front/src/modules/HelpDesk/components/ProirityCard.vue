<template>
    <div :style="`color: ${priority.color};`" class="flex items-center truncate">
        <div class="mr-2 priority_icon">
            <div class="priority_icon__bg" :style="`background: ${priority.color};`" />
            <i class="fi" :class="priority.icon" />
        </div>
        <span class="truncate">{{ priority.name }}</span>
    </div>
</template>

<script>
export default {
    props: {
        priority: {
            type: Object,
            required: true
        }
    }
}
</script>