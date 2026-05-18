<template>
    <a-tag v-if="record.user" color="green" class="mb-2">
        Профиль активен
    </a-tag>
</template>

<script>
export default {
    props: ['record']
}
</script>