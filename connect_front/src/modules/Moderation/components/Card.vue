<template>
    <div class="card">
        <div class="mb-2">
            <Profiler :avatarSize="28" :user="item.user" />
        </div>
        <div 
            v-if="item.organization"
            class="flex items-center cursor-pointer mb-2" 
            @click="clickHandler()">
            <div class="pr-2">
                <a-avatar 
                    :size="28" 
                    icon="team" 
                    :src="item.organization.logo ? item.organization.logo : null" />
            </div>
            <span class="blue_color group_name truncate">
                {{ item.organization.name }}
            </span>
        </div>
        <div class="mb-2">
            <span class="gray">Дата создания:</span> {{ $moment(item.created_at).format('DD.MM.YYYY HH:mm') }}
        </div>
        <div class="mb-2">
            <span class="gray">Дата обновления:</span> {{ $moment(item.updated_at).format('DD.MM.YYYY HH:mm') }}
        </div>
        <AccessGroupSelectRow :record="item" class="mb-1 group_selected" />
        <template v-if="item.is_touched">
            <a-tag v-if="item.is_approved" color="green">
                Одобрено
            </a-tag>
            <a-tag v-else color="red">
                Отклонено
            </a-tag>
        </template>
        <div v-else class="grid gap-2 grid-cols-2 mt-2">
            <a-button type="primary" :loading="loading" block @click="changeApproved(true)">
                Одобрить
            </a-button>
            <a-button type="flat_danger" :loading="loading" block @click="changeApproved(false)">
                Отклонить
            </a-button>
        </div>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'
export default {
    components: {
        AccessGroupSelectRow: () => import('@/components/TableWidgets/Widgets/AccessGroupSelectRow.vue')
    },
    props: {
        item: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            loading: false
        }
    },
    methods: {
        clickHandler() {
            const query = JSON.parse(JSON.stringify(this.$route.query))
            if(!query?.organization_drawer) {
                query.organization_drawer = 'detail'
                query.organization_id = this.item.organization.id
                this.$router.replace({query})
            }
        },
        async changeApproved(is_approved) {
            try {
                this.loading = true
                const { data } = await this.$http.put(`/catalogs/profile_requests/${this.item.id}/`, {
                    is_approved
                })
                if(data) {
                    this.$message.success('Заявка обновлена')
                    eventBus.$emit('update_moderation_list')
                }
            } catch(error) {
                errorHandler({error})
            } finally {
                this.loading = false
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.card{
    padding: 12px;
    background: #ffffff;
    border-radius: var(--borderRadius);
    .group_selected{
        &::v-deep{
            .flex.flex-wrap,
            .ant-tag{
                width: 100%!important;
                max-width: 100%!important;
            }
        }
    }
}
</style>