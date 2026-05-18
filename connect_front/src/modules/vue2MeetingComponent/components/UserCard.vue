<template>
    <div 
        class="cursor-pointer flex items-center user_card justify-between" 
        @click="selectUser(user)">
        <Profiler
            :user="user"
            initStatus
            :subtitle="user.job_title ? { text: user.job_title, class: 'text-xs gray', wrapClass: 'leading-4' } : {}"
            :avatarSize="28" />
        <div 
            class="radio" 
            :class="isChecked && 'ant-radio-checked'">
            <div class="ant-radio-inner"></div>
        </div>
    </div>
</template>

<script>
export default {
    name: "MeetingUserCard",
    props: {
        user: {
            type: Object,
            required: true
        },
        selectUser: {
            type: Function,
            default: () => {}
        },
        selected: {
            type: Array,
            default: () => []
        }
    },
    computed: {
        isChecked() {
            if(this.selected?.length) {
                const find = this.selected.find(f => f.id === this.user.id)
                if(find)
                    return true
                else
                    return false
            } else
                return false
        }
    }
}
</script>

<style lang="scss" scoped>
.user_card{
    padding: 10px 15px;
}
</style>