<template>
    <!-- <div>

        {{ column }}
    </div> -->
    <a-alert 
        message="Такого виджета не существует" 
        banner />
</template>
<script>
export default {
    props: {
        column: {
            type: Object,
            required: true
        }
    }
}
</script>