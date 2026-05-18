<template>
    <div>
        <a-tag color="blue">
            {{ record.tasks }}
        </a-tag>
        <a-tag color="#87d068">
            {{ record.complete_tasks }}
        </a-tag>
    </div>
</template>


<script>
export default {
    props: {
        record: {
            type: Object,
            required: true
        },
    }
}
</script>