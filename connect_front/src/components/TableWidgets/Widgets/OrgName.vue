<template>
    <div v-if="text">
        <div class="flex items-center">
            <div :key="text.logo" class="pr-2">
                <a-avatar 
                    :size="30"
                    :src="text.logo"
                    icon="fi-rr-users-alt" 
                    flaticon />
            </div>
            <span>{{ text.name }}</span>
        </div>
    </div>
    <div v-else class='text-gray-300'>
        Не указана
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