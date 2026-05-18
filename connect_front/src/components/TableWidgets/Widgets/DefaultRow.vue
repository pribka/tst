<template>
    <div>
        <a-tooltip 
            v-if="record.rejected" 
            destroyTooltipOnHide
            title="Проблемная задача">
            <span
                class="cursor-pointer counter_rejected"
                @click="openTask(record)">
                {{ record.counter }}
            </span>
        </a-tooltip>
        <span
            v-else
            class="cursor-pointer"
            @click="openTask(record)">
            {{ record.counter }}
        </span>
    </div>
</template>

<script>
export default {
    props: {
        record: {
            type: Object,
            required: true
        },
        openTask: {
            type: Function,
            default: () => {}
        },
    }
}
</script>

<!-- <a-tooltip 
    v-if="record.rejected" 
    destroyTooltipOnHide
    title="Проблемная задача">
    <span
        class="cursor-pointer counter_rejected"
        @click="openTask(record)">
        {{ record.counter }}
    </span>
</a-tooltip>
<span
    v-else
    class="cursor-pointer"
    @click="openTask(record)">
    {{ record.counter }}
</span> -->