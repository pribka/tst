<template>
    <div>
        {{ text ? 'Закрытый' : 'Открытый' }}
    </div>
</template>

<script>
export default {
    props: {
        text: {
            type: Boolean
        },
    },
}
</script>