<template>
    <div class="org-card">
        <div class="name">
            {{ organization.name || 'Не указано' }}
        </div>
        <div class="info-item">
            <span class="label">Адрес: </span>
            <span class="value" :class="{ 'no-data': !organization.delivery_address}">{{ organization.delivery_address || 'Не указан' }}</span>
        </div>
        <div class="info-item">
            <span class="label">БИН/ИИН: </span>
            <span class="value" :class="{ 'no-data': !organization.inn}">{{ organization.inn || 'Не указан' }}</span>
        </div>
        <div class="all-details">
            <a-collapse>
                <a-collapse-panel key="1" header="Все реквизиты">
                    <div class="info-item">
                        <span class="label">Краткое наименование: </span>
                        <span class="value" :class="{ 'no-data': !organization.name}">{{ organization.name || 'Не указано' }}</span>
                    </div>
                    <div class="info-item">
                        <span class="label">Полное наименование: </span>
                        <span class="value" :class="{ 'no-data': !organization.full_name}">{{ organization.full_name || 'Не указано' }}</span>
                    </div>
                    <div v-if="organization.director" class="info-item">
                        <span class="label">Руководитель: </span>
                        <Profiler
                            :avatarSize="32"
                            :user="organization.director"
                            showUserName />
                    </div>
                    <div v-else class="info-item">
                        <span class="label">Руководитель: </span>
                        <span class="value" :class="{ 'no-data': !organization.director}">Не указан</span>
                    </div>
                </a-collapse-panel>
            </a-collapse>
        </div>
        <a-button
            v-if="showSelectButton"
            class="select-button"
            size="large"
            @click="selectOrg">
            Выбрать организацию
        </a-button>
    </div>
</template>
<script>
export default {
    name: 'OrganizationCard',
    props: {
        organization: {
            type: Object,
            required: true
        },
        select: {
            type: Function,
            default: () => {}
        },
        showSelectButton: {
            type: Boolean,
            default: true
        }
    },
    methods: {
        selectOrg() {
            this.$emit('select', { organization: this.organization }, true, false)
        }
    }
}
</script>
<style lang="scss" scoped>
.org-card{
    border: 1px solid rgba(217, 217, 217, 1);
    border-radius: 8px;
    padding: 20px;
    font-weight: 400;
    font-size: 14px;
    .name {
        color: rgba(0, 0, 0, 1);
        font-size: 16px;
        line-height: 100%;
        margin-bottom: 10px;
    }
    .info-item {
        line-height: 1.3rem;
        color: rgba(0, 0, 0, 1);
        .label {
            opacity: 0.6;
        }
        .value {}
    }
    .all-details {
        margin-top: 10px;
        line-height: 100%;
        color: rgba(29, 101, 192, 1);
    }
    .all-details::v-deep {
        width: max-content;
        .ant-collapse {
            border: 0;
            background-color: #fff;
            .ant-collapse-item {
                border: 0;
                .ant-collapse-header {
                    padding: 0;
                    padding-left: 24px;
                    .ant-collapse-arrow {
                        left: 0;
                    }
                }
            }
            .ant-collapse-content {
                border-bottom: 0;
                border-top: 0;
            }
        }
    }
    .select-button {
        margin-top: 25px;
    }
    .no-data {
        opacity: 0.6;
    }
}
</style>