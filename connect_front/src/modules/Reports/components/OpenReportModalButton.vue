<template>
    <a-dropdown 
        :trigger="['click']" 
        destroyPopupOnHide
        placement="bottomLeft"
        @visibleChange="onVisibleChange">
        <slot name="button" :templateLoading="templateLoading">
            <a-button 
                type="flat_primary" 
                flaticon
                :loading="templateLoading"
                v-tippy
                :content="buttonText || $t('Reporting')"
                icon="fi-rr-square-poll-vertical" />
        </slot>
        <template #overlay>
            <a-menu 
                ref="scrollArea"
                class="overflow-y-auto w-[300px] max-h-[306px] truncate"
                @scroll="onScroll">
                <a-menu-item
                    v-for="item in templateList" 
                    :key="item.id"
                    @click="openModal(item)" 
                    class="truncate select-none"
                    :title="item.name">
                    <div class="w-full truncate flex items-center">
                        <span class="truncate">{{ item.name }}</span>
                    </div>
                </a-menu-item>
                <a-menu-item
                    v-if="loading"
                    key="loading">
                    <span class="max-w-full truncate flex items-center justify-center">
                        <a-spin size="small" />
                    </span>
                </a-menu-item>
                <a-menu-item
                    v-else-if="finished && templateList.length === 0"
                    key="no_data">
                    <span class="max-w-full truncate flex items-center justify-center">
                        {{ $t('No data') }}
                    </span>
                </a-menu-item>
                <a-menu-item
                    v-if="showMore && templateList && templateList.length"
                    @click="openAllReports()" 
                    :title="$t('reports_mobule.all_reports')">
                    <span class="w-full truncate items-center flex justify-between">
                        <span class="truncate w-full">{{ $t('reports_mobule.all_reports') }}</span>
                        <i class="fi fi-rr-arrow-up-right-from-square" style="opacity: 0.7;" />
                    </span>
                </a-menu-item>
            </a-menu>
        </template>
    </a-dropdown>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
export default {
    props: {
        sectionCode: {
            type: String,
            required: true
        },
        buttonText: {
            type: String,
            default: null
        },
        baseTemplateId: {
            type: String,
            default: ''
        },
        showMore: {
            type: Boolean,
            default: true
        }
    },
    data() {
        return {
            visible: false,
            templateList: [],
            loading: false,
            templateLoading: null,
            finished: false,
            page: 1,
            pageSize: 8,
            firstLoadDone: false
        }
    },
    methods: {
        openAllReports() {
            this.$router.push({ name: 'reports' })
        },
        onVisibleChange(val) {
            if (val && !this.firstLoadDone) {
                this.loadMore()
                this.firstLoadDone = true
            }
        },
        openModal(item) {
            const url = this.baseTemplateId ? `/reports/user_report_settings/${item.id}/` : `/reports/report_settings/${item.id}/`
            this.templateLoading = true
            this.$http.get(url)
                .then(({ data }) => {
                    const payload = {
                        ...data,
                        appSectionCode: data.app_section_code, 
                    }
                    return this.$store.dispatch('reports/openReportModal', payload)
                })
                .catch(error => {
                    errorHandler({error, show: false})
                })
                .finally(() => {
                    this.templateLoading = false
                })
        },
        async loadMore() {
            if (this.loading || this.finished) return
            this.loading = true

            const url = this.baseTemplateId ? '/reports/user_report_settings/' : '/reports/report_settings/'
            const params = this.baseTemplateId 
                ? {
                    base_report: this.baseTemplateId
                } 
                : {
                    filters: JSON.stringify({
                        category: this.sectionCode
                    })
                }

            this.$http.get(url, { params })
                .then(({ data }) => {
                    this.templateList.push(...data.results)
                    if (data.next) {
                        this.page++
                    } else {
                        this.finished = true
                    }
                })
                .catch((error) => {
                    errorHandler({error, show: false})
                })
                .finally(() => {
                    this.loading = false
                })
        },
        onScroll(e) {
            const el = e.target
            if (el.scrollHeight - el.scrollTop - el.clientHeight < 40) {
                this.loadMore()
            }
        }
    }
}
</script>
