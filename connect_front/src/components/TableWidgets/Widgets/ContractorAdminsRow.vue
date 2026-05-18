<template>
    <div class="flex flex-wrap gap-1">
        <a-tag v-for="item in record.admins" :key="item.id" style="margin-right: 0px;">
            {{ item.name }}
        </a-tag>
    </div>
</template>

<script>
export default {
    props: {
        record: {
            type: Object
        },
        model: {
            type: String
        },
        column: {
            type: Object
        },
    }
}
</script>