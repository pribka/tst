<template>
    <span>
        <UserDrawer
            id="changeUser"
            ref="changeUserRef"
            @input="changeUser"
            hide
            :submitButtonText="$t('Save')"
            :title="$t('task.select')"/>
        <a-button
            v-if="dropActions && dropActions.edit && item.editable"
            type="ui"
            ghost
            flaticon
            shape="circle"
            icon="fi-rr-edit"
            class="ml-2"
            @click="editFull()" />
    </span>
</template>

<script>
import mixins from './mixins.js'
export default {
    components: {
        UserDrawer: () => import("@apps/DrawerSelect/index.vue")
    },
    mixins: [
        mixins
    ],
    computed: {
        cStatusFiltered() {
            const changeCooperatorStatuses = this.dropActions?.change_cooperator_status?.available_statuses
            const onlyCooperator = this.dropActions?.change_cooperator_status?.only_coop
            if (onlyCooperator && changeCooperatorStatuses?.length) {
                return changeCooperatorStatuses
            }

            const availableStatuses = this.dropActions?.change_status?.available_statuses
            if (availableStatuses?.length) {
                return availableStatuses
            }
            return []
        },

        currentStatus() {
            const availableStatuses = this.dropActions?.change_status?.available_statuses
            if (availableStatuses) {
                if (availableStatuses.includes('completed')) {
                    return this.filteredList.find(status => status.code === 'completed')
                }
                if (availableStatuses.includes('in_work ')) {
                    return this.filteredList.find(status => status.code === 'in_work ')
                }
                return null
            }

            if(this.filteredList?.length && this.item) {
                if(this.item.status.is_complete)
                    return null
                else {
                    const find = this.filteredList.find(f => f.depends?.find(fn => fn === this.item.status.code))
                    if(find?.is_complete) {
                        if(this.isAuthor)
                            return find ? find : null
                        else
                            return null
                    } else
                        return find ? find : null
                }
            } else
                return null
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    created() {
        this.getTaskActions()
    }
}
</script>

<style lang="scss" scoped>
.edit_icon_wrap {
    display: flex;
    justify-content: center;
    align-items: center;
    
    line-height: 100%;
    font-size: 1rem;
}
</style>