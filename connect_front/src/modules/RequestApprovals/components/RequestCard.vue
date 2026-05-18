<template>
    <div
        class="request_card"
        v-touch:longtap="longtapHandler"
        @click="open()">
        <div class="request_card__name mb-2 truncate flex items-center justify-between">
            <div class="blue_color truncate">
                #{{ item.number }} <template v-if="item.request_type">{{ item.request_type.name }}</template>
            </div>
            <div v-if="item.amount_requested" class="font-semibold ml-2">
                {{ formattedAmount }} &#8376;
            </div>
        </div>

        <div v-if="issuedAmount" class="card_row">
            <div class="card_row__label">{{ $t('approvals.issued') }}</div>
            <div class="card_row__value">
                {{ formatMoney(issuedAmount) }}
            </div>
        </div>

        <div v-if="hasReportedAmount" class="card_row">
            <div class="card_row__label">{{ $t('approvals.reported') }}</div>
            <div class="card_row__value">
                {{ formatMoney(reportedAmount) }}
            </div>
        </div>

        <div v-if="hasBalance" class="card_row">
            <div class="card_row__label">{{ toReturnLabel }}</div>
            <div class="card_row__value" :class="{ text_red: toReturnAmount > 0, green: toReturnAmount < 0 }">
                {{ formatMoney(toReturnAmount) }}
            </div>
        </div>

        <div v-if="item.project" class="card_row">
            <div class="card_row__label">{{ $t('approvals.project') }}</div>
            <div class="card_row__value">
                <div class="flex items-center cursor-pointer row_name">
                    <div class="pr-2">
                        <a-avatar
                            :size="22"
                            icon="fi-rr-users-alt"
                            flaticon
                            :key="workgroupLogoPath"
                            :src="workgroupLogoPath" />
                    </div>
                    <div class="line-clamp-2 break-words" style="line-height: 18px;">
                        {{ item.project.name }}
                    </div>
                </div>
            </div>
        </div>

        <div v-if="item.organization" class="card_row">
            <div class="card_row__label">{{ $t('Organization') }}</div>
            <div class="card_row__value">
                <div class="flex items-center cursor-pointer row_name">
                    <div class="pr-2">
                        <a-avatar
                            :size="22"
                            icon="fi-rr-users-alt"
                            flaticon
                            :key="orgLogoPath"
                            :src="orgLogoPath" />
                    </div>
                    <div class="line-clamp-2 break-words" style="line-height: 18px;">
                        {{ item.organization.name }}
                    </div>
                </div>
            </div>
        </div>

        <div v-if="item.status" class="card_row">
            <div class="flex items-center justify-between">
                <div class="w-full">
                    <a-tag block :color="item.status.color" size="large">
                        {{ item.status.name }}
                    </a-tag>
                </div>
                <div v-if="item.author" class="ml-2">
                    <Profiler
                        :showUserName="false"
                        :avatarSize="30"
                        :user="item.author" />
                </div>
            </div>
            
            <div v-if="showNewComments" class="new_comments">
                <i class="fi fi-rr-comment-dots"></i>
                <span>{{ $t('workplan.new_comments') }}</span>
            </div>
        </div>

        <ActionsList ref="actionList" :item="item" :open="open" :page_name="page_name" :pageModel="pageModel" />
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'

export default {
    sockets: {
        notify({ data }) {
            if (
                data?.event_type === 'new_comment_from_object'
                && data?.obj === this.item?.id
            ) {
                if (this.isCurrentApprovalOpen) {
                    this.hasSocketNewComment = false
                    return
                }
                this.hasSocketNewComment = true
            }
        }
    },
    props: {
        actionsEnabled: {
            type: Boolean,
            default: true
        },
        item: {
            type: Object,
            required: true
        },
        page_name: {
            type: String,
            required: true
        },
        pageModel: {
            type: String,
            required: true
        }
    },
    components: {
        ActionsList: () => import('./ActionsList.vue')
    },
    computed: {
        isCurrentApprovalOpen() {
            return this.$route.query?.approvals === this.item?.id
        },
        showNewComments() {
            return !this.isCurrentApprovalOpen
                && Boolean(this.item?.has_new_comments || this.hasSocketNewComment)
        },
        toReturnLabel() {
            return this.toReturnAmount < 0 ? this.$t('approvals.overspending') : this.$t('approvals.to_return')
        },

        hasIssuedAmount() {
            return this.item?.amount_paid !== null && this.item?.amount_paid !== undefined
        },

        hasBalance() {
            return this.item?.balance !== null && this.item?.balance !== undefined
        },

        hasReportedAmount() {
            return this.hasIssuedAmount && this.hasBalance
        },

        issuedAmount() {
            return this.toNumber(this.item?.amount_paid)
        },

        toReturnAmount() {
            return this.toNumber(this.item?.balance)
        },

        reportedAmount() {
            if (!this.hasReportedAmount) return 0
            return this.issuedAmount - this.toReturnAmount
        },

        orgLogoPath() {
            return this.item.organization?.logo || ''
        },

        workgroupLogoPath() {
            return this.item.project?.workgroup_logo?.path || ''
        },

        formattedAmount() {
            if (!this.item?.amount_requested) return ''

            const value = String(this.item.amount_requested)
            const [intPart, decimalPart] = value.split('.')
            const formattedInt = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')

            if (decimalPart && Number(decimalPart) !== 0) {
                return `${formattedInt}.${decimalPart}`
            }

            return formattedInt
        }
    },
    watch: {
        'item.id'() {
            this.hasSocketNewComment = false
        },
        isCurrentApprovalOpen(value) {
            if (value) {
                this.hasSocketNewComment = false
            }
        }
    },
    data() {
        return {
            hasSocketNewComment: false
        }
    },
    mounted() {
        eventBus.$on('request_approvals_comments_seen', this.markNewCommentsSeen)
    },
    beforeDestroy() {
        eventBus.$off('request_approvals_comments_seen', this.markNewCommentsSeen)
    },
    methods: {
        markNewCommentsSeen(data) {
            if (String(data?.id) !== String(this.item.id)) return
            this.hasSocketNewComment = false
            this.$set(this.item, 'has_new_comments', false)
        },

        toNumber(v) {
            if (v === null || v === undefined) return 0
            const n = Number(String(v).replace(/\s/g, '').replace(',', '.'))
            return Number.isFinite(n) ? n : 0
        },

        formatMoney(v) {
            const n = this.toNumber(v)
            const hasFrac = Math.round(n * 100) % 100 !== 0
            const opts = hasFrac
                ? { minimumFractionDigits: 2, maximumFractionDigits: 2 }
                : { minimumFractionDigits: 0, maximumFractionDigits: 0 }

            return new Intl.NumberFormat('ru-RU', opts).format(n) + ' ₸'
        },

        open() {
            const query = JSON.parse(JSON.stringify(this.$route.query))
            if (!query.approvals) {
                query.approvals = this.item.id
                this.$router.push({ query })
            } else {
                eventBus.$emit('approvals_drawer_close')
                setTimeout(() => {
                    query.approvals = this.item.id
                    this.$router.push({ query })
                }, 500)
            }
        },

        longtapHandler() {
            if (this.actionsEnabled) {
                this.$refs.actionList.openActionsDrawer()
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.new_comments{
    display: flex;
    align-items: center;
    color: #4777ff;
    margin-top: 10px;
    i{
        line-height: 1;
        margin-right: 8px;
    }
}
.card_row{
    &__label{
        opacity: 0.6;
        margin-bottom: 5px;
    }
    &:not(:last-child){
        margin-bottom: 10px;
    }
    &__value{
        &.green{
            color: #16a34a;
        }
        &.text_red{
            color: #ef4444;
        }
    }
}
.request_card{
    padding: 12px;
    zoom: 1;
    font-size: 14px;
    font-variant: tabular-nums;
    line-height: 1.5;
    list-style: none;
    font-feature-settings: 'tnum';
    background: #ffffff;
    border-radius: var(--borderRadius);
    margin-bottom: 10px;
    -webkit-user-select: none;
    -khtml-user-select: none;
    -moz-user-select: none;
    -ms-user-select: none;
    user-select: none;
    transition: all 0.5s cubic-bezier(0.645, 0.045, 0.355, 1);
    cursor: pointer;
    &.touch{
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
        transform: scale(0.97);
    }
}
</style>
