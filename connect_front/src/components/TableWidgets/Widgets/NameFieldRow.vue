<template>
    <div v-if="text?.name" class="flex items-center truncate">
        <span class="truncate">{{ text.name }}</span>
    </div>
    <div v-else class='text-gray-300'>
        Не указано
    </div>
</template>

<script>
export default {
    props: {
        text: {
            type: Object,
            default: () => null
        },
    },
}
</script>