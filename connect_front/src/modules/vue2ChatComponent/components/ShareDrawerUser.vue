<template>
    <div class="flex items-center truncate" :title="dialog.name">
        <div class="mr-2">
            <a-badge :color="statusColor" class="user_badge">
                <a-avatar
                    :src="dialog.recipient && dialog.recipient.avatar && dialog.recipient.avatar.path ? dialog.recipient.avatar.path : null"
                    :style="dialog.color ? `backgroundColor:${dialog.color}!important;color:#fff!important;` : 'backgroundColor: #cccccc'">
                    {{ avatarText }}
                </a-avatar>
            </a-badge>
        </div>
        <div class="truncate">
            <div class="text-sm font-semibold truncate">
                {{dialog.name}}
            </div>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        dialog: {
            type: Object,
            required: true
        }
    },
    computed: {
        isOnline() {
            return this.$store.getters['user/getUserStatus'](this.dialog.recipient.id)
        },
        firstCheck() {
            return this.$store.getters['user/getUserFirstCheck'](this.dialog.recipient.id)
        },
        statusColor() {
            if(this.dialog.recipient?.last_activity) {
                if(this.isOnline)
                    return '#52c41a'
                else
                    return '#f5222d'
            } else
                return '#808080'
        },
        avatarText() {
            if(this.dialog) {
                if(this.dialog.is_public) {
                    return this.dialog.name.charAt(0).toUpperCase()
                } else {
                    const n = this.dialog.name.split(' ')
                    return `${n[0].charAt(0).toUpperCase()}${n[1] ? n[1].charAt(0).toUpperCase() : ''}${n[2] ? n[2].charAt(0).toUpperCase() : ''}`
                }
            }
            return ''
        },
    },
    created() {
        if(!this.firstCheck && this.dialog?.recipient.last_activity) {
            this.$store.commit('user/SET_ONLINE_USER_EVENT', this.dialog.recipient)
        }
    }
}
</script>

<style lang="scss" scoped>
.user_badge{
    &::v-deep{
        .ant-badge-dot{
            top: 5px;
            right: 5px;
        }
    }
}
</style>