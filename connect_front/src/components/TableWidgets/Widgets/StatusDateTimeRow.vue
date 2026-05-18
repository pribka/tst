<template>
    <div>
        <template v-if="text">
            {{$moment(text).format('DD.MM.YYYY в HH:mm')}}
        </template>
        <div v-else style="color: #888888;">
            Нет даты
        </div>
    </div>
</template>

<script>
export default {
    props: {
        text: {
            type: String
        }
    }
}
</script>