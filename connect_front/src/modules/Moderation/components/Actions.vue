<template>
    <div class="flex items-center justify-end">
        <template v-if="showButtons">
            <a-button type="success" :loading="loading" ghost class="mr-2" @click="changeApproved(true)">
                Одобрить
            </a-button>
            <a-button type="danger" :loading="loading" ghost @click="changeApproved(false)">
                Отклонить
            </a-button>
        </template>
        <template v-else>
            <a-tag v-if="record.is_approved" color="green">Одобрено</a-tag>
            <a-tag v-else color="red">Отклонено</a-tag>
        </template>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'
export default {
    props: {
        record: {
            type: Object,
            required: true
        },
        pageName: {
            type: String,
            default: ''
        }
    },
    computed: {
        showButtons() {
            if(!this.record.is_touched)
                return true
            return false
        }
    },
    data() {
        return {
            loading: false
        }
    },
    methods: {
        changeApproved(is_approved) {
            this.$confirm({
                title: is_approved ? this.$t('moderation_approved') : this.$t('moderation_approved2'),
                cancelText: this.$t('no'),
                okText: this.$t('yes'),
                onOk: async () => {
                    try {
                        this.loading = true
                        const { data } = await this.$http.put(`/catalogs/profile_requests/${this.record.id}/`, {
                            is_approved,
                            access_groups: this.record.access_groups
                        })
                        if(data) {
                            this.$message.success(this.$t('approved_updated'))
                            eventBus.$emit(`table_row_${this.pageName}`, {
                                action: 'update',
                                row: data
                            })
                        }
                    } catch(error) {
                        errorHandler({error})
                    } finally {
                        this.loading = false
                    }
                }
            })
            
        }
    }
}
</script>