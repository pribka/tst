<template>
    <a-drawer
        :title="$t('inquiries.inc_view')"
        placement="right"
        :visible="visible"
        wrapClassName="inquiries_view_drawer"
        :width="drawerWidth"
        :after-visible-change="afterVisibleChange"
        @close="visible = false">
        <div class="drawer_header">
            <a-tabs v-model="tabActive">
                <a-tab-pane key="info" :tab="$t('inquiries.information')" /> 
                <a-tab-pane key="history" :tab="$t('inquiries.history_changes')" />
            </a-tabs>
        </div>
        <div class="drawer_body">
            <a-tabs v-model="tabActive">
                <a-tab-pane key="info" :tab="$t('inquiries.information')">
                    <a-spin :spinning="loading" class="w-full">
                        <div v-if="assessmentDetail" class="assessment_detail">
                            <div class="info_card md:flex items-center justify-between">
                                <div class="md:flex items-center flex-wrap mb-3 md:mb-0">
                                    <div v-if="assessmentDetail.issue.number" class="info_card__item mb-3 md:mb-0">
                                        <div class="item_label">{{ $t('inquiries.resNumber') }}</div>
                                        <div class="item_value">{{ assessmentDetail.issue.number }}</div>
                                    </div>
                                    <div v-if="assessmentDetail.organization" class="info_card__item">
                                        <div class="item_label">{{ $t('inquiries.organization') }}:</div>
                                        <div class="item_value">{{ assessmentDetail.organization.name }}</div>
                                    </div>
                                </div>
                                <div class="flex items-center">
                                    <div class="issue_status">
                                        <a-tag :color="assessmentDetail.status.color">
                                            {{ assessmentDetail.status.name }}
                                        </a-tag>
                                    </div>
                                    <div class="total_value">
                                        <div class="circle" :style="{ backgroundColor: circleColor(assessmentDetail) }">
                                            <span>{{ assessmentDetail.total_value }}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="info_card">
                                <div class="xl:flex items-start justify-between info_card_top">
                                    <div class="md:flex items-start flex-wrap mb-4 xl:mb-0">
                                        <div v-if="assessmentDetail.issue.issue_date" class="info_card__item mb-3 md:mb-0">
                                            <div class="item_label">{{ $t('inquiries.inc_date') }}:</div>
                                            <div class="item_value">{{ $moment(assessmentDetail.issue.issue_date).format('DD MMMM YYYY') }}</div>
                                        </div>
                                        <div class="info_card__item mb-3 md:md-0">
                                            <div class="item_label">{{ $t('inquiries.issue_category') }}:</div>
                                            <div class="item_value">
                                                <template v-if="assessmentDetail.issue">
                                                    <template v-if="assessmentDetail.issue.issue_category">
                                                        {{ fullCategoryName(assessmentDetail.issue.issue_category) }}
                                                    </template>
                                                    <template v-else>
                                                        {{ assessmentDetail?.issue?.summary }}
                                                    </template>
                                                </template>
                                            </div>
                                        </div>
                                        <div v-if="assessmentDetail.issue.issue_date" class="info_card__item">
                                            <div class="item_label">{{ $t('inquiries.sent_to') }}:</div>
                                            <div class="item_value">{{ getRecipient(assessmentDetail) }}</div>
                                        </div>
                                    </div>
                                    <div class="md:flex items-center">
                                        <div class="info_card__item mb-3 md:mb-0">
                                            <div class="item_label">{{ $t('inquiries.spec') }}:</div>
                                            <div class="item_value"><Profiler :user="assessmentDetail?.author" /></div>
                                        </div>
                                    </div>
                                </div>
                                <div>
                                    <div class="info_card__item">
                                        <div class="item_label">{{ $t('inquiries.inquiry_text') }}:</div>
                                        <div class="item_value">
                                            <template v-if="assessmentDetail?.issue?.text">
                                                <TextViewer
                                                    :body="assessmentDetail?.issue?.text"/>
                                            </template>
                                            <template v-else>
                                                <div class="no-data">{{ $t('inquiries.no_data') }}</div>
                                            </template>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div 
                                v-if="assessmentDetail.location_points && assessmentDetail.location_points.length" 
                                class="mb-4 grid gap-4"
                                :class="assessmentDetail.location_points.length === 1 ? 'grid-cols-1' : 'grid-cols-1 lg:grid-cols-2'">
                                <div v-for="point in assessmentDetail.location_points" :key="point.id" class="point_card">
                                    <div v-if="point.name" class="point_name">
                                        {{ point.name }}
                                    </div>
                                    <div v-if="point.address" class="point_address">
                                        {{ point.address }}
                                    </div>
                                    <div v-if="point.lat && point.lon" class="point_address mt-1">
                                        {{ point.lat }}, {{ point.lon }}
                                    </div>
                                </div>
                            </div>
                            <div class="criterions">
                                <div class="mb-3">{{ $t('inquiries.assessment_criteria') }}:</div>
                                <div v-for="item in assessmentDetail.risk_assessment_criteria" :key="item.criteria.id" class="risk_assessment_criteria_list">
                                    <i v-if="item.value === 1" class="fi fi-rr-check" />
                                    <i v-else class="fi fi-rr-cross" />
                                    <span class="ml-3" :class="item.value === 1 && 'active'">{{ item.criteria.name }}</span>
                                </div>
                            </div>
                        </div>
                    </a-spin>
                </a-tab-pane>
                <a-tab-pane key="history" :tab="$t('inquiries.history_changes')">
                    <History 
                        v-if="assessmentDetail"
                        :related_object="assessmentDetail.id" 
                        injectContainer
                        filterPrefix="risk_assessment"
                        modelLabel="risk_assessment.RiskAssessmentModel" />
                </a-tab-pane>
            </a-tabs>
        </div>
    </a-drawer>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    components: {
        TextViewer: () => import('@apps/CKEditor/TextViewer.vue'),
        History: () => import('@apps/History/index.vue')
    },
    data() {
        return {
            visible: false,
            loading: false,
            assessmentDetail: null,
            tabActive: 'info'
        }
    },
    computed: {
        windowWidth() {
            return this.$store.state.windowWidth
        },
        drawerWidth() {
            if(this.windowWidth > 1200)
                return 1107
            else if(this.windowWidth <= 1200 && this.windowWidth > 700) {
                return '95%'
            } else {
                return '100%'
            }
        },
    },
    methods: {
        circleColor(assessment) {
            if (assessment.total_value >= 1 && assessment.total_value <= 2) {
                return '#fee933'
            } else if (assessment.total_value >= 3 && assessment.total_value <= 5) {
                return '#ff8812'
            } else if (assessment.total_value > 5) {
                return '#ff4e46'
            } else {
                return '#A9B3BF'
            }
        },
        getRecipient(assessment) {
            const recipient = assessment.sent_for === 1 
                ? this.$t('inquiries.head_of_apparatus') 
                : this.$t('inquiries.main_leader_or_deputies');
            return recipient;
        },
        fullCategoryName(issue_category) {
            const buildFullName = (category, names = []) => {
                if (!category) {
                    return names
                }
                names.unshift(category.name)
                return buildFullName(category.issue_category, names)
            }
            return buildFullName(issue_category).join('/')
        },
        afterVisibleChange(vis) {
            if(!vis) {
                this.assessmentDetail = null
            }
        },
        async getInquiries(inquiries) {
            try {
                this.loading = true
                const { data } = await this.$http.get(`/risk_assessment/${inquiries.id}/`)
                if(data) {
                    this.assessmentDetail = data
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        }
    },
    mounted() {
        eventBus.$on('view_inquiries', inquiries => {
            this.visible = true
            this.getInquiries(inquiries)
        })
    },
    beforeDestroy() {
        eventBus.$off('view_inquiries')
    }
}
</script>

<style lang="scss" scoped>
.inquiries_view_drawer{
    &::v-deep{
        .ant-drawer-wrapper-body,
        .ant-drawer-content{
            overflow: hidden;
        }
        .ant-drawer-body{
            padding: 0px;
            height: calc(100% - 40px);
        }
        .ant-tabs-bar{
            margin: 0px;
        }
        .drawer_header{
            .ant-tabs-content{
                display: none;
            }
        }
        .drawer_body{
            height: calc(100% - 44px);
            overflow-y: auto;
            padding: 15px;
            .ant-tabs-bar{
                display: none;
            }
        }
    }
}
.circle {
    min-width: 40px;
    padding: 2px 8px;
    border-radius: 99999px;
    font-weight: 500;
    text-align: center;
    font-size: 0.875rem;
    position: relative;
    overflow: hidden;
    border: 1px solid transparent;
    -webkit-user-select: none;
    -moz-user-select: none;
    user-select: none;
    cursor: pointer;
    color: #000;
    border: 1px solid transparent;
}
.issue_status {
    display: flex;
    justify-content: flex-end;
    &::v-deep{
        .ant-tag{
            height: 27px;
            line-height: 25px;
            border-radius: 20px;
            padding-left: 10px;
            padding-right: 10px;
        }
    }
}
.criterions {
    .risk_assessment_criteria_list {
        padding: 10px 0;
        &:not(:last-child){
            border-bottom: 1px solid #D9D9D9;
        }
        .fi-rr-check{
            color: #4DAE00;
        }
        .fi-rr-cross{
            color: #F94A1D;
        }
        span{
            opacity: 0.6;
            color: #000;
            &.active{
                opacity: 1;
            }
        }
    }
}
.point_card{
    border: 1px solid #d9d9d9;
    padding: 20px;
    border-radius: 8px;
    color: #000;
    .point_name{
        font-size: 16px;
        margin-bottom: 5px;
    }
    .point_address{
        opacity: 0.6;
    }
}
.info_card{
    border: 1px solid #d9d9d9;
    padding: 20px;
    border-radius: 8px;
    &:not(:last-child){
        margin-bottom: 15px;
    }
    .info_card_top{
        border-bottom: 1px solid #d9d9d9;
        padding-bottom: 20px;
        margin-bottom: 20px;
    }
    .info_card__item{
        color: #000;
        max-width: 400px;
        &:not(:last-child){
            margin-right: 40px;
        }
        .item_label{
            opacity: 0.6;
            margin-bottom: 8px;
        }
        .item_value{
            font-size: 16px;
        }
    }
}
</style>