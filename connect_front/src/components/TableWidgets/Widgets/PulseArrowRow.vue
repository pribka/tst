<template>
    <div class="cursor-pointer" @click="openHandler(record)">
        <a-button 
            type="flat_primary"
            shape="circle"
            v-tippy
            :content="$t('open')"
            flaticon
            icon="fi-rr-arrow-right" />
    </div>
</template>

<script>
export default {
    props: {
        text: {
            type: [String, Number, Boolean, Object]
        },
        record: {
            type: Object
        },
        model: {
            type: String
        },
        column: {
            type: Object
        },
        openHandler: {
            type: Function,
            default: () => {}
        }  
    }
}
</script>