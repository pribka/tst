<template>
    <div 
        class="cursor-pointer flex items-center user_card justify-between"
        @click="selectUser(user)">
        <div class="info flex items-center">
            <div>
                <a-avatar :size="28" icon="user" />
            </div>
            <div class="ml-3">
                {{ user.username }}
            </div>
        </div>
        <div 
            class="radio"
            :class="isChecked && 'ant-radio-checked'">
            <div class="ant-radio-inner"></div>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        user: {
            type: Object,
            required: true
        },
        currentUser: {
            type: Object,
            required: true
        },
        selectUser: {
            type: Function,
            default: () => {}
        },
        selectedUsers: {
            type: Array,
            default: () => []
        },
        partisipants: {
            type: Array,
            default: () => []
        }
    },
    computed: {
        isChecked() {
            const findeP = this.partisipants.find(f => f.member.id === this.user.id)
            if(findeP)
                return true
            else {
                if(this.selectedUsers?.length) {
                    const find = this.selectedUsers.find(f => f.id === this.user.id)
                    if(find)
                        return true
                    else
                        return false
                } else
                    return false
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.user_card{
    padding: 10px 20px;
}
</style>