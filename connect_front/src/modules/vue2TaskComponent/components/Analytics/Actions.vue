<template>
    <div class="flex items-center"> 
        <a-button
            type="link"
            :disabled="record.description && record.description.length ? false : true"
            class="ant-btn-icon-only mr-2"
            @click="openDescModal(record)">
            <i class="fi fi-rr-envelope-open-text"></i>
        </a-button>
        <a-button 
            type="link"
            class="ant-btn-icon-only"
            @click="openModalStat(text)">
            <i class="fi fi-rr-chart-histogram"></i>
        </a-button>
    </div>
</template>

<script>
export default {
    props: {
        record: {
            type: Object,
            required: true
        },
        text: {
            type: [Object, Boolean, String]
        },
        openDescModal: {
            type: Function,
            required: true
        },
        openModalStat: {
            type: Function,
            required: true
        },
    }
}
</script>