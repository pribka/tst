<template>
    <div class="card_main" :class="isExpand && 'card_active'">
        <div 
            class="header items-center"
            :class="isExpand && 'border-b'">
            <div class="flex items-center">
                <div 
                    class="number flex items-center cursor-pointer" 
                    @click="openAssessmentis()">
                    <div 
                        class="button mr-3"
                        :class="isExpand && 'rotate-90'">
                        <a-button 
                            type="ui" 
                            ghost 
                            size="small"
                            shape="circle"
                            class="flex items-center justify-center">
                            <i class="fi fi-rr-angle-right" />
                        </a-button>
                    </div>
                    <span class="mr-7">
                        {{ $moment(assessment.issue.issue_date).format('DD.MM.YYYY') }}
                    </span>
                    {{ assessment.issue.number }}
                </div>
                <div 
                    class="organization cursor-pointer" 
                    @click="openAssessmentis()">
                    <span class="break-all">
                        {{ assessment?.organization?.name }}
                    </span>
                </div>
            </div>
            <div class="flex items-center pr-3">
                <div class="flex items-center mr-5">
                    <div class="delete_button">
                        <a-button
                            v-if="deleteAvailability"
                            type="ui"
                            shape="circle"
                            @click="deleteAssessment()"
                            ghost
                            class="flex items-center justify-center">
                            <i class="fi fi-rr-trash text-red-500" />
                        </a-button>
                    </div>
                    <div class="edit_button">
                        <a-button
                            v-if="editAvailability"
                            type="ui" 
                            shape="circle"
                            @click="editAssessment()"
                            flaticon
                            icon="fi-rr-edit"
                            ghost
                            class="flex items-center justify-center" />
                    </div>
                </div>
                <div class="issue_status">
                    <a-tag :color="assessment.status.color">
                        {{ assessment.status.name }}
                    </a-tag>
                </div>
                <div class="total_value">
                    <div class="circle" :style="{ backgroundColor: circleColor }">
                        <span>{{ assessment.total_value }}</span>
                    </div>
                </div>
            </div>
        </div>
        <a-spin :spinning="assessmentLoading">
            <div class="item_body " v-show="isExpand">
                <template v-if="assessmentDetail">
                    <div class="info_card">
                        <div class="xl:flex items-start justify-between info_card_section">
                            <div class="md:flex items-start flex-wrap mb-4 xl:mb-0">
                                <div v-if="assessmentDetail.issue.issue_date" class="info_card__item mb-3 md:md-0">
                                    <div class="item_label">{{ $t('inquiries.inc_date') }}:</div>
                                    <div class="item_value">{{ $moment(assessmentDetail.issue.issue_date).format('DD MMMM YYYY') }}</div>
                                </div>
                                <div class="info_card__item mb-3 md:md-0">
                                    <div class="item_label">{{ $t('inquiries.issue_category') }}:</div>
                                    <div class="item_value">
                                        <template v-if="assessmentDetail.issue">
                                            <template v-if="assessmentDetail.issue.issue_category">
                                                {{ fullCategoryName }}
                                            </template>
                                            <template v-else>
                                                {{ assessmentDetail?.issue?.summary }}
                                            </template>
                                        </template>
                                    </div>
                                </div>
                                <div v-if="assessmentDetail.issue.issue_date" class="info_card__item">
                                    <div class="item_label">{{ $t('inquiries.sent_to') }}:</div>
                                    <div class="item_value">{{ getRecipient }}</div>
                                </div>
                            </div>
                            <div class="md:flex items-center">
                                <div class="info_card__item mb-3 md:md-0">
                                    <div class="item_label">{{ $t('inquiries.spec') }}:</div>
                                    <div class="item_value"><Profiler :user="assessmentDetail?.author" /></div>
                                </div>
                                <div class="info_card__item">
                                    <a-button type="primary" size="large" ghost class="mb-2" @click="visible = true">
                                        {{ $t('inquiries.history_changes') }}
                                    </a-button>
                                </div>
                            </div>
                        </div>
                        <div v-if="showPersonalReception" class="xl:flex items-start gap-10 info_card_section">
                            <div class="info_card__item">
                                <div class="item_label">{{ $t('inquiries.social_status') }}:</div>
                                <div class="item_value">
                                    {{ assessmentDetail.issue.personal_reception.social_status.name || 'Не указан' }}
                                </div>
                            </div>
                            <div class="info_card__item">
                                <div class="item_label">{{ $t('inquiries.status') }}:</div>
                                <div class="item_value">
                                    {{ assessmentDetail.issue.personal_reception.status.name || 'Не указан' }}
                                </div>
                            </div>
                        </div>
                        <div class="info_card__item full_item">
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
                </template>
                <template v-if="empty">
                    <a-empty :description="false" />
                </template>
            </div>
        </a-spin>
        <DrawerTemplate
            placement="right"
            :width="isMobile ? '100%' : 800"
            v-model="visible"
            @close="visible = false">
            <template #title>
                <div class="drawer_title">
                    {{ $t('inquiries.history_changes') }}
                </div>
            </template>
            <History 
                v-if="visible"
                :related_object="assessment.id" 
                :popoverMaxWidth="600"
                injectContainer
                filterPrefix="risk_assessment"
                modelLabel="risk_assessment.RiskAssessmentModel" />
        </DrawerTemplate>
    </div>
</template>
  
<script>
import TextViewer from '@apps/CKEditor/TextViewer.vue'
import eventBus from '@/utils/eventBus'
import History from '@apps/History/index.vue'
import DrawerTemplate from '@/components/DrawerTemplate.vue'
export default {
    name: 'RiskAssessment',
    components: {
        TextViewer,
        History,
        DrawerTemplate
    },
    props: {
        assessment: {
            type: Object,
            required: true
        },
    },
    data() {
        return {
            isExpand: false,
            assessmentLoading: false,
            assessmentDetail: null,
            empty: false,
            visible: false
        }
    },
    computed: {
        showPersonalReception() {
            return Object.hasOwn(this.assessmentDetail.issue, 'personal_reception')
        },
        fullCategoryName() {
            const buildFullName = (category, names = []) => {
                if (!category) {
                    return names
                }
                names.unshift(category.name)
                return buildFullName(category.issue_category, names)
            }
            return buildFullName(this.assessmentDetail.issue.issue_category).join('/')
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        circleColor() {
            if (this.assessment.total_value >= 1 && this.assessment.total_value <= 2) {
                return '#fee933'
            } else if (this.assessment.total_value >= 3 && this.assessment.total_value <= 5) {
                return '#ff8812'
            } else if (this.assessment.total_value > 5) {
                return '#ff4e46'
            } else {
                return '#A9B3BF'
            }
        },
        getRecipient() {
            const recipients = {
                0: this.$t('inquiries.main_leader'),
                1: this.$t('inquiries.head_of_apparatus'),
                2: this.$t('inquiries.deputies')
            }
            return recipients[this.assessmentDetail.sent_for] || this.$t('inquiries.noData')
        },
        deleteAvailability() {
            if ('delete' in this.assessment && 'availability' in this.assessment.delete) {
                return this.assessment.delete['availability']
            } else {
                return false
            }
        },
        editAvailability() {
            if ('edit' in this.assessment && 'availability' in this.assessment.edit) {
                return this.assessment.edit['availability']
            } else {
                return false
            }
        }
    },
    created() {
        eventBus.$on('update_assessment_details', id => {
            if (this.assessment.id === id) {
                this.getAssessmentDetail()
            }
        })
    },
    beforeDestroy() {
        eventBus.$off('update_assessment_details')
    },
    methods: {
        async openAssessmentis() {
            this.isExpand = !this.isExpand
            if (this.isExpand) {
                await this.getAssessmentDetail()
            } else {
                this.assessmentDetail = null
            }
        },
        editAssessment() {
            eventBus.$emit('edit_inquir', this.assessment.id)
        },
        deleteAssessment() {
            this.$confirm({
                title: this.$t('inquiries.confirm_delete_title'),
                content: '',
                okText: this.$t('inquiries.delete'),
                okType: 'danger',
                zIndex: 2000,
                closable: true,
                cancelText: this.$t('inquiries.cancel'),
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post('/table_actions/update_is_active/', {
                            id: this.assessment.id,
                            is_active: false
                        })
                            .then(() => {
                                eventBus.$emit('assessment_list_reload')
                                this.$message.success(this.$t('inquiries.delete_success'))
                                resolve()
                            })
                            .catch(e => {
                                console.log(e)
                                reject(e)
                            })
                    })
                }
            })
        },
        async getAssessmentDetail() {
            if (!this.assessmentLoading) {
                try {
                    this.assessmentLoading = true
                    const { data } = await this.$http.get(`risk_assessment/${this.assessment.id}/`)
                    if (data) {
                        this.assessmentDetail = data
                    }
                } catch (e) {
                    console.log(e)
                    this.empty = true
                } finally {
                    this.assessmentLoading = false
                }
            }
        },
    }
}
</script>

<style lang="scss" scoped>
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
    .info_card_section{
        border-bottom: 1px solid #d9d9d9;
        padding-bottom: 20px;
        margin-bottom: 20px;
    }
    .info_card__item{
        color: #000;
        &:not(.full_item){
            max-width: 400px;
        }
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
.personal-reception {
    margin-right: 0;
}
.card_main {
    margin-bottom: 10px;
    border: 1px solid transparent;
    border-radius: 8px;
    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    &.card_active{
        border-color: #d9d9d9;
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
    .header {
        background-color: #fff;
        display: flex;
        justify-content: space-between;
        padding: 5px 0;
        .status {
            justify-self: right;
        }
        .number {
            padding: 5px;
            padding-left: 10px;
            min-width: 270px;
        }
        .organization{
            align-items: center;
        }
        .name {
            font-weight: 600;
        }
        .issue_date {
            min-width: 110px;
        }
        .issue_status {
            min-width: 120px;
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
        .delete_button {
            min-width: 32px;
        }
        .edit_button {
            min-width: 32px;
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

}
.theader {
    font-weight: 600;
}
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.5s;
}
.fade-enter, .fade-leave-to {
  opacity: 0;
}
.custom_border_color {
    border-color: #d9d9d9;
    border-radius: 8px;
}
.contractor {
    display: grid;
    grid-template-columns: max-content 1fr;
}
.item_body {
    padding: 15px;
    background: #fff;
}
.file_name {
    margin-left: 10px;
}
.no-data{
    opacity: 0.3;
}
</style>