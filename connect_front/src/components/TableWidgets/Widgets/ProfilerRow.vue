<template>
    <div class="h-full flex items-center">
        <template v-if="isAuction">
            <a-popconfirm
                title="Вы действительно хотите взять задачу?"
                ok-text="Да"
                cancel-text="Нет"
                @confirm="takeTask(record)">
                <a-button 
                    size="small"
                    type="primary"
                    ghost
                    class="flex items-center">
                    <i class="fi fi-rr-user-add mr-2"></i>
                    Взять
                </a-button>
            </a-popconfirm>
        </template>
        <template v-else>
            <Profiler 
                v-if="text"
                :avatarSize="22"
                nameClass="text-sm"
                :user="text"
                :showUserName="showUserName" />
        </template>
    </div>
</template>

<script>
export default {
    props: {
        text: {
            type: [Object, String]
        },
        record: {
            type: Object
        },
        column: {
            type: Object
        },
        tableType: {
            type: String
        },
        takeTask: {
            type: Function,
            default: () => {}    
        }
    },
    computed: {
        showUserName() {
            return true
        },
        isInterest() {
            return this.tableType === 'interests'
        },
        isOperatorField() {
            return this.column?.key === 'operator'
        },
        isAuction() {
            return this.isOperatorField && this.record.is_auction
        }
    }

}
</script>