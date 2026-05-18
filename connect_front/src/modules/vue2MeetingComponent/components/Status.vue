<template>
    <div>
        <a-tag 
            v-if="status === 'new'"
            class="m-0"
            color="blue">
            {{ $t('meeting.new') }}
        </a-tag>
        <div 
            v-if="status === 'online'" 
            class="online flex items-center">
            <div class="blob mr-2"></div>
            {{ $t('meeting.online') }}
        </div>
        <a-tag 
            v-if="status === 'ended'"
            class="m-0"
            color="green">
            {{ $t('meeting.ended') }}
        </a-tag>
    </div>
</template>

<script>
export default {
    props: {
        status: {
            type: String,
            default: ''
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