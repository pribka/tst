<template>
    <div class="network_status">
        <i class="fi fi-rr-exclamation" />
        {{$t('network_error')}}
    </div>
</template>

<script>
export default {
    name: 'NetworkStatus'
}
</script>

<style lang="scss" scoped>
.network_status{
    position: fixed;
    z-index: 99999;
    -webkit-backdrop-filter: saturate(180%) blur(20px);
    backdrop-filter: saturate(180%) blur(20px);
    background: rgba(0,0,0,0.6);
    color: #fff;
    padding: 15px;
    border-radius: 5px;
    bottom: 15px;
    right: 15px;
    display: flex;
    align-items: center;
    @media (max-width: 575.98px) {
        left: 15px;
    }
    @media (min-width: 576px) {
        bottom: 20px;
        right: 20px;
    }
    i{
        margin-right: 8px;
        color: #ff4d4f;
        font-size: 18px;
    }
}
</style>