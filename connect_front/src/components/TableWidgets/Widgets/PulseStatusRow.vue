<template>
    <a-tag 
        block
        size="large"
        :color="statusColor"
        @click="openHandler(record)">{{ statusText }}</a-tag>
</template>

<script>
export default {
    props: {
        text: {
            type: [Object, Boolean, String, Array]
        },
        record: {
            type: Object,
            required: true
        },
        model: {
            type: String
        },
        openHandler: {
            type: Function,
            default: () => {}
        }    
    },
    computed: {
        statusText() {
            return this.text?.name
        },
        statusColor() {
            return this.text?.color
        }
    }
}
</script>

<style lang="scss" scoped>
@keyframes pulse-red {
  0% {
    transform: scale(0.95);
    box-shadow: 0 0 0 0 rgba(255, 82, 82, 0.7);
  }
  
  70% {
    transform: scale(1);
    box-shadow: 0 0 0 10px rgba(255, 82, 82, 0);
  }
  
  100% {
    transform: scale(0.95);
    box-shadow: 0 0 0 0 rgba(255, 82, 82, 0);
  }
}
.online{
    color: rgba(255, 82, 82, 1);
    .blob{
        border-radius: 50%;
        height: 8px;
        width: 8px;
        transform: scale(1);
        background: rgba(255, 82, 82, 1);
        box-shadow: 0 0 0 0 rgba(255, 82, 82, 1);
        animation: pulse-red 2s infinite;
    }
}
</style>