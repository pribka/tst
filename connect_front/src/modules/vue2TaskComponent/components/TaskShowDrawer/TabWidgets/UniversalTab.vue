<template>
    <div>
        <div 
            v-if="loading" 
            class="flex justify-center">
            <a-spin />
        </div>
        <template v-if="tab">
            <component 
                :is="headerActions" 
                v-if="!isInterestNeeds"
                :tab="tab"
                :task="task"
                :code="code"
                v-model="visible" />
            <component 
                :is="checkModal" 
                :tab="tab"
                :task="task"
                :code="code"
                v-model="visible" />
            <div
                v-if="isInterestNeeds"
                class="interest_needs_tools mb-4 flex items-center">
                <div class="interest_needs_tools__title">
                    Потребности клиента
                </div>
                <a-button
                    v-if="canManageInterestNeeds"
                    type="default"
                    icon="plus"
                    data-guide-id="interest-needs-add"
                    @click="visible = true">
                    Добавить потребность
                </a-button>
                <a-tooltip :title="interestAnalyzeTooltip">
                    <span
                        data-guide-id="interest-needs-llm"
                        class="interest_needs_tools__button_wrap">
                        <a-button
                            type="primary"
                            ghost
                            :disabled="!canAnalyzeInterestNeeds"
                            :loading="llmLoading"
                            @click="analyzeInterestNeeds">
                            <i class="fi fi-ai-rr-sparkles mr-1"></i>
                            LLM-анализ
                        </a-button>
                    </span>
                </a-tooltip>
            </div>
            <component 
                :is="listWidget"
                v-if="getTab"
                :key="listKey"
                :data-guide-id="isInterestNeeds ? 'interest-needs-table' : null"
                :task="task"
                :code="code" />
        </template>
    </div>
</template>

<script>
import { mapActions, mapGetters } from 'vuex'
import List from './UniversalTabWidgets/List.vue'
import accessMixins from './UniversalTabWidgets/accessMixins.js'
export default {
    components: {
        List
    },
    mixins: [
        accessMixins
    ],
    props: {
        task: {
            type: Object,
            default: () => null
        },
        code: {
            type: [String, Number],
            required: true
        },
        reloadTask: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        ...mapGetters({
            getTab: 'task/getTab'
        }),
        tab() {
            return this.getTab(this.task.id, this.code)
        },
        headerActions() {
            if(this.tab?.headerButtons && Object.keys(this.tab.headerButtons).length)
                return () => import('./UniversalTabWidgets/HeaderActions.vue')
            else
                return null
        },
        checkModal() {
            if(this.tab?.modal && Object.keys(this.tab.modal).length && this.tab?.formInfo)
                return () => import('./UniversalTabWidgets/FormModal.vue')
            else
                return null
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        listWidget() {
            if(this.isMobile)
                return () => import('./UniversalTabWidgets/ListMobile.vue')
            return () => import('./UniversalTabWidgets/List.vue')
        },
        isInterestNeeds() {
            return this.task?.task_type === 'interest' && this.code === 'interest_needs'
        },
        canManageInterestNeeds() {
            return this.isInterestNeeds && this.checkAccess
        },
        canAnalyzeInterestNeeds() {
            if(!this.isInterestNeeds)
                return false
            if(typeof this.task?.can_analyze_interest === 'boolean')
                return this.task.can_analyze_interest
            if(typeof this.task?.editable === 'boolean')
                return this.task.editable
            return this.canManageInterestNeeds
        },
        interestAnalyzePermissionMessage() {
            return this.task?.analyze_interest_permission_message
                || 'LLM-анализ изменяет интерес и потребности клиента. Запуск доступен постановщику интереса или модератору проекта.'
        },
        interestAnalyzeTooltip() {
            return this.canAnalyzeInterestNeeds
                ? 'Выявить потребности клиента и сопоставить их с каталогом'
                : this.interestAnalyzePermissionMessage
        }
    },
    data() {
        return {
            loading: false,
            visible: false,
            llmLoading: false,
            listKey: 0
        }
    },
    created() {
        this.getInfo()
    },
    methods: {
        ...mapActions({
            getTabInfo: 'task/getTabInfo'
        }),
        async getInfo() {
            try {
                this.loading = true
                this.getTabInfo({
                    part: this.code,
                    task: this.task
                })
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        },
        async analyzeInterestNeeds() {
            if(this.llmLoading)
                return
            if(!this.canAnalyzeInterestNeeds) {
                this.$message?.warning(this.interestAnalyzePermissionMessage)
                return
            }
            try {
                this.llmLoading = true
                const { data } = await this.$http.post(`/tasks/task/${this.task.id}/analyze_interest/`, {
                    force_create: true
                })
                this.listKey += 1
                this.reloadTask({ id: this.task.id }, false)
                if(data?.analysis)
                    this.$message?.success('Потребности выявлены и сопоставлены с каталогом')
                else if(data?.needs?.length)
                    this.$message?.info('Потребности уже заполнены')
                else
                    this.$message?.warning('LLM не нашла явных потребностей')
            } catch(e) {
                const message = this.getInterestAnalyzeErrorMessage(e)
                this.$message?.error(message)
            } finally {
                this.llmLoading = false
            }
        },
        getInterestAnalyzeErrorMessage(error) {
            const data = error?.response?.data
            if(typeof data === 'string')
                return data
            if(typeof data?.message === 'string')
                return data.message
            if(typeof data?.detail === 'string')
                return data.detail
            if(typeof data?.detail?.message === 'string')
                return data.detail.message
            return 'Не удалось разобрать потребности'
        }
    }
}
</script>

<style lang="scss" scoped>
.interest_needs_tools{
    justify-content: flex-end;
    gap: 10px;
    padding: 12px 14px;
    border: 1px solid var(--borderColor);
    border-radius: 6px;
    background: #fafafa;

    &__title{
        margin-right: auto;
        font-weight: 600;
        color: var(--textColor);
    }

    &__button_wrap{
        display: inline-flex;
    }
}
</style>
