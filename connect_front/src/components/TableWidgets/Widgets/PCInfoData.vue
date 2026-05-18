<template>
    <div v-if="text">
        {{$moment(text).format('DD.MM.YYYY')}}
    </div>
</template>

<script>
export default {
    props: {
        text: {
            type: String,
            default: ''
        },
    }
}
</script>