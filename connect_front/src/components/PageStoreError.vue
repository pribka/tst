<template>
    <div class="p-5">
        <a-alert
            message="Ошибка"
            type="error"
            show-icon>
            <template slot="description">
                В <strong>injectInit</strong> нет модуля <strong>{{ storeName }}</strong>
            </template>
        </a-alert>
    </div>
</template>

<script>
export default {
    props: {
        storeName: {
            type: String,
            required: true
        }
    }
}
</script>