<template>
    <div>
        <div 
            v-if="driver.disconnected" 
            class="driver_contractor_cluster disconnected">
            <div class="circle_wrapper">
                <a-icon 
                    type="car" 
                    theme="filled" />
                <div 
                    v-if="checkDriverAvatar(driver)" 
                    class="driver_avatar">
                    <a-avatar
                        :src="checkDriverAvatar(driver)"
                        :size="18"
                        icon="user" />
                </div>
            </div>
        </div>
        <div 
            v-else 
            class="driver_contractor_cluster">
            <div class="circle_wrapper">
                <a-icon 
                    type="car" 
                    theme="filled" />
                <div 
                    v-if="checkDriverAvatar(driver)" 
                    class="driver_avatar">
                    <a-avatar
                        :src="checkDriverAvatar(driver)"
                        :size="18"
                        icon="user" />
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        driver: {
            type: Object,
            required: true
        }
    },
    watch: {
        'driver.location': {
            handler: function() {
                clearTimeout(this.timer)
                this.timer = setTimeout(() => {
                    this.$store.commit('monitor/SET_USER_LOCATION_DISCONNECT', this.driver)
                }, 300000)
            },
            deep: true
        }
    },
    data() {
        return {
            timer: null
        }
    },
    methods: {
        checkDriverAvatar(driver) {
            if(driver?.user?.avatar) {
                return `//${window.location.host}/media/${driver.user.avatar}`
            } else
                return null
        }
    }
}
</script>

<style lang="scss" scoped>
.driver_contractor_cluster{
    width: 30px;
    height: 30px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-size: 14px;
    font-weight: 600;
    box-shadow: 0 2px 8px rgb(0 0 0 / 15%);
    border: 2px solid var(--blue);
    .circle_wrapper{
        background: var(--blue);
        width: 23px;
        height: 23px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
    }
    .driver_avatar{
        position: absolute;
        bottom: -8px;
        right: -8px;
    }
    &.disconnected{
        border: 2px solid #52575b;
        .circle_wrapper{
            background: #52575b;
        }
    }
}
</style>