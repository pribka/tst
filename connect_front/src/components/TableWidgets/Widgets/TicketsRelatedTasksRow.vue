<template>
    <div class="flex flex-wrap gap-x-2 gap-y-1">
        <template v-if="record.related_tasks && record.related_tasks.length">
            <div 
                v-for="(task, index) in record.related_tasks" 
                class="blue_color cursor-pointer"
                :key="task.id"
                @click.stop="openTask(task.id)">
                #{{ task.counter }}<span v-if="index !== record.related_tasks.length - 1">, </span>
            </div>
        </template>
    </div>
</template>

<script>
export default {
    props: {
        record: {
            type: Object,
            required: true
        }
    },
    methods: {
        openTask(id) {
            const query = JSON.parse(JSON.stringify(this.$route.query))
            query.task = id
            this.$router.push({query})
        }
    }
}
</script>