<template>
    <div class="template" @click="openReportModal" @mouseenter="isHovered = true" @mouseleave="isHovered = false">
        <div v-if="item.app_section_code" class="mb-2">
            <a-tag style="font-size: 12px;padding: 5px 10px;line-height: 12px;">
                {{ $t(`reports_mobule.${item.app_section_code}`) }}
            </a-tag>
        </div>
        <div class="mb-auto">
            <div class="flex items-center">
                <div class="font-semibold">
                    {{ item.name }}
                </div>
            </div>
            <div class="mt-1 template__desc">
                {{ item.description }}
            </div>
        </div>
        <div class="template__footer">
            <a-button 
                :type="isHovered ? 'primary' : 'flat_primary'"
                size="small"
                class="flex items-center"
                :class="isMobile && 'justify-center'"
                style="padding-left: 10px;padding-right: 10px;padding-top: 6px;padding-bottom: 6px;height: 30px;"
                :loading="openReportLoading">
                {{ $t('Open') }}
                <i class="fi fi-rr-arrow-small-right ml-2" />
            </a-button>
            <template v-if="isMyTemplates">
                <div class="template__action">
                    <a-popover
                        v-model="deleteConfirmVisible"
                        trigger="click"
                        placement="top">
                        <template #content>
                            <div>
                                <div class="mb-2">{{ $t('Delete report template?') }}</div>
                                <div class="flex justify-end items-center">
                                    <a-button type="primary" danger size="small" :loading="deleteLoading" @click="deleteTemplate">{{ $t('Delete') }}</a-button>
                                    <a-button size="small" @click="deleteConfirmVisible=false" class="ml-1">{{ $t('Cancel') }}</a-button>
                                </div>
                            </div>
                        </template>
                        <a-button type="ui" ghost flaticon icon="fi-rr-trash" size="small" shape="circle" :loading="deleteLoading" @click.stop />
                    </a-popover>
                </div>
            </template>
        </div>
    </div>

</template>

<script>
import { errorHandler } from '@/utils/index.js'
export default {
    props: {
        item: {
            type: Object,
            required: true
        },
        templatesSource: {
            type: String,
            default: 'templates'
        },
        isMobileTemplate: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        isMobile() { 
            return this.$store.state.isMobile
        },
        activeTemplate() {
            return this.$store.state.reports.activeTemplate
        },
        modelName() {
            return this.activeTemplate.metadata.modelName
        },
        isMyTemplates() {
            return this.templatesSource === 'my_templates'
        },
        isBase() {
            return this.templatesSource === 'templates'
        },

    },
    data() {
        return {
            deleteConfirmVisible: false,
            deleteLoading: false,
            openReportLoading: false,
            isHovered: false,
        }
    },
    methods: {
        openReportModal() {
            const URLs = {
                'my_templates': '/reports/user_report_settings/',
                'templates': '/reports/report_settings/'
            }
            const url = URLs[this.templatesSource] + this.item.id + '/'
            this.openReportLoading = true
            this.$http.get(url)
                .then(({ data }) => {
                    const payload = { 
                        ...data, 
                        appSectionCode: data.app_section_code, 
                        editable: this.templatesSource === 'my_templates',
                    }
                    return this.$store.dispatch('reports/openReportModal', payload)
                })
                .catch(error => {
                    errorHandler({error, show: false})
                })
                .finally(() => {
                    this.openReportLoading = false
                })
        },
        deleteTemplate() {
            const url = `/reports/user_report_settings/${this.item.id}/`
            this.deleteLoading = true
            this.$http.delete(url)
                .then(() => {
                    this.$message.success(this.$t('Template deleted'))
                    this.$store.commit('reports/RESET_TEMPLATES', { listKey: this.templatesSource })
                })
                .catch((error) => {
                    errorHandler({error})
                })
                .finally(() => {
                    this.deleteLoading = false
                })
        }
    }
}
</script>

<style lang="scss" scoped>
.template {
    display: flex;
    flex-direction: column;
    padding: 15px;
    border-radius: 14px;
    background-color: #ffffff;
    transition: box-shadow 0.2s ease;
    user-select: none;
    cursor: pointer;
    &:hover {
        box-shadow: 0px 8px 16px 0px #00000014, 0px 0px 4px 0px #0000000A;
    }
    @media (min-width: 768px) {
        padding: 20px;
    }
}
.template__footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-direction: row;
    margin-top: 16px;
    gap: 8px;
    @media (min-width: 840px) {
        align-items: center;
        flex-direction: row;
        gap: 0;
    }
}
.template__action {
    display: flex;
    align-items: center;
    margin-left: 8px;
    margin-bottom: 0;
    @media (min-width: 840px) {
        margin-left: auto;
        margin-bottom: 0;
    }
}
.template__desc {
    color: #888888
}
</style>
