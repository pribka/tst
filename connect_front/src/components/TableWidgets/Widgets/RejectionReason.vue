<template>
    <a-dropdown
        :trigger="['click']"
        :destroyPopupOnHide="true"
        @visibleChange="getRejectionReasonList">
        <div :class="['cursor-pointer', textColor]">
            <a-spin size="small" :spinning="spinning">
                <a-badge 
                    v-if="reason && reason.color !== 'default'" 
                    :color="reason.color" />
                {{ getReason() }}
            </a-spin>
        </div>
        <a-menu slot="overlay">
            <a-menu-item 
                v-if="rejectionReasonListLoader"
                key="menu_loader"
                class="flex justify-center">
                <a-spin size="small" />
            </a-menu-item>
            <template v-if="rejectionReasonList">
                <a-menu-item 
                    v-for="(reason, index) in rejectionReasonList"
                    :key="index"
                    class="flex items-center"
                    @click="changeRejectionReason(reason)">
                    <a-badge 
                        v-if="reason.color !== 'default'" 
                        :color="reason.color" />
                    {{ reason.name }}
                </a-menu-item>
            </template>
        </a-menu>
    </a-dropdown>
</template>

<script>
import { mapState } from 'vuex'
export default {
    props: {
        reason: {
            type: Object,
            default: () => null
        },
        record: {
            type: Object,
            required: true
        },
    },
    computed: {
        ...mapState({
            rejectionReasonList: state => state.task.rejectionReasonList,
            rejectionReasonListLoader: state => state.task.rejectionReasonListLoader,
        })
    },
    data() {
        return {
            textColor: 'text-gray-300',
            spinning: false,
        }
    },
    methods: {
        getReason() {
            if(this.reason) {
                this.textColor = 'text-current'
                return this.reason.name
            }
            return 'Не указана' 
        },
        async getRejectionReasonList() {
            if(this.rejectionReasonList.length === 0) {
                try {
                    await this.$store.dispatch('task/getRejectionReasons')
                } catch(e) {
                    this.$message.error(this.$t('error'))
                }
            }
        },
        async changeRejectionReason(reason) {
            try {
                this.spinning = true
                await this.$store.dispatch('task/changeRejectionReason', {
                    task: this.record, 
                    reason: reason
                })
            } catch(e) {
                this.$message.error(this.$t('error'))
            } finally {
                this.spinning = false
            }
        },
    }
}
</script>
