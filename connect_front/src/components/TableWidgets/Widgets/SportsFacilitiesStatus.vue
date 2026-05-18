<template>
    <div class="flex items-center">
        <a-tag 
            :color="record.status.hex_color" 
            class="status_tag"
            :style="record.status.code === 'draft' && 'color: #000;'">
            {{ record.status.name }}
        </a-tag>
        <a-button 
            v-if="record.repub_comp"
            type="success" 
            class="ml-2"
            size="small"
            v-tippy="{ inertia : true, duration : '[600,300]'}"
            :content="$t('sports.message_compliance')"
            flaticon 
            icon="fi-rr-check" />
    </div>
</template>

<script>
export default {
    props: {
        record: {
            type: Object,
            default: () => null
        }
    }
}
</script>