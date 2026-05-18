<template>
    <div class="col_aside" :class="isMobile && 'col_mobile'">
        <div v-if="isMobile" class="row_info">
            <a-button
                v-if="actions && actions.create_chat && !requestData.with_chat"
                :loading="createChatLoading"
                block
                type="ui"
                @click="createChat">
                {{ $t("project.create_chat") }}
            </a-button>
            <a-button
                v-if="requestData.with_chat && requestData.linked_chat"
                block
                type="ui"
                @click="openChat">
                {{ $t("project.open_chat") }}
            </a-button>
        </div>
        <div v-if="descLength.length" class="user-bio row_info">
            <h6 >{{ $t('project.description')}}:</h6>
            <p class="break-words">
                {{ descLength }}
            </p>
            <div v-if="showDescBtn">
                <span 
                    class="desc_more" 
                    @click="showDesc = !showDesc">
                    {{ showDesc ? $t('project.hide') : $t('project.more') }}
                </span>
            </div>
        </div>

        <!-- Срок сдачи проекта -->
        <div v-if="requestData.dead_line !== null" class="row_info">
            <h6 >{{ $t("project.deadline_project") }}:</h6>
            <a-tag 
                color="purple" 
                class="mt-1">
                <span class="flex items-center">
                    <i class="fi fi-rr-clock-three mr-1"></i>
                    {{  $moment(requestData.dead_line).format("DD.MM.YYYY HH:mm") }}
                </span>
            </a-tag>
            <a-tag 
                v-if="requestData.control_dates"
                color="red" 
                class="mt-1">
                <span class="flex items-center">
                    {{ $t('project.control_on') }}
                </span>
            </a-tag>
        </div>

        <!-- Дата начала -->
        <div v-if="requestData.date_start_plan !== null" class="row_info">
            <h6 >{{ $t("project.date_start_plan") }}:</h6>
            {{  $moment(requestData.date_start_plan).format("DD.MM.YYYY HH:mm") }}
        </div>

        <div
            v-if="requestData.work_directions && requestData.work_directions.length"
            class="row_info">
            <h6>{{ $t("project.work_directions") }}:</h6>
            <div class="direction_tags">
                <a-tag
                    v-for="item in requestData.work_directions"
                    :key="item.id">
                    {{ item.name }}
                </a-tag>
            </div>
        </div>

        <!-- Тип клуба -->
        <div 
            v-if="requestData.workgroup_type !== undefined && requestData.workgroup_type.name !== ''" 
            class="row_info">
            <h6 >{{ $t("project.type") }}:</h6>
            <span>{{
                requestData.workgroup_type !== undefined
                    ? requestData.workgroup_type.name
                    : ""
            }}</span>
        </div>

        <div v-if="founderMember" class="row_info">
            <h6>{{ $t("project.project_founder") }}:</h6>
            <div class="flex flex-col pt-[5px]">
                <div class="member flex items-center">
                    <Profiler
                        :avatarSize="26"
                        nameClass="text-sm"
                        :popoverText="$t('project.project_founder')"
                        :showUserName="true"
                        :user="founderMember" />
                </div>
            </div>
        </div>

        <transition name="slide-fade">
            <div 
                v-if="showParticipantsAside && participantsCount" 
                class="row_info participants_aside_block" :class="actions && actions.add_member && 'mb-1'">
                <h6 v-if="hasParticipantsTab">
                    <span class="participants" @click="changeTab('employees')">{{`${$t("project.participants")} (${participantsCount})`}}:</span>
                </h6>
                <h6 v-else>{{ `${$t("project.participants")} (${participantsCount})` }}:</h6>
                <div class="flex flex-col pt-[5px]">
                    <div 
                        v-for="item in memberVisible" 
                        :key="item.id"
                        class="member flex items-center">
                        <Profiler
                            :avatarSize="26"
                            nameClass="text-sm"
                            :popoverText="item.membership_role.name"
                            :showUserName="true"
                            :user="item.member" />
                    </div>
                    <div v-if="hasParticipantsTab && participantsCount > 1" class="all_participants white-background" @click="changeTab('employees')">
                        <div class="participants">{{ participantsText }}</div>
                        <i class="fi fi-rr-arrow-up-right"></i>
                    </div>
                </div>
            </div>
        </transition>
        <transition name="slide-fade">
            <InviteButton
                v-if="actions && actions.add_member"
                :requestData="requestData"
                :addToMembersList="addToMembersList"
                :updatePartisipants="updatePartisipants" />
        </transition>
        
        <!-- Кол-во задач -->
        <div v-if="requestData.tasks" class="row_info">
            <div class="row_info" :class="isMobile && 'flex'">
                <h6 >{{ $t("project.count_task") }}:</h6>
                <span :class="isMobile && 'ml-2'">{{ requestData.tasks }}</span>
            </div>
    
            <!-- Кол-во выполненных задач -->
            <div v-if="requestData.complete_tasks" :class="isMobile && 'flex'">
                <h6 >{{ $t("project.tasks_complete") }}:</h6>
                <span :class="isMobile && 'ml-2'">{{ requestData.complete_tasks }}</span>
            </div>
    
            <div v-if="requestData.is_project">
                <a-progress
                    class="row_progress"
                    :stroke-color="{
                        '0%': '#4179fb',
                        '100%': '#4179fb',
                    }"
                    :percent="percent"/>
            </div>
        </div>

        <!-- Смета -->
        <div v-if="budgetStat" class="row_info">
            <h6 >{{ $t('project.all_budget') }}:</h6>
            <span>{{ priceFormat(budgetStat.total_sum) }} <template v-if="budgetStat.currency">{{ budgetStat.currency.icon }}</template></span>
        </div>

        <div v-if="requestData?.location_point?.address" class="row_info">
            <h6 >{{ $t('Address') }}:</h6>
            
            <!-- Marker -->
            <div class="flex">
                <svg class="mt-1 mr-1.5 shrink-0" height="12" viewBox="0 0 10 12" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M5 0C3.67445 0.00145554 2.4036 0.527637 1.46625 1.46311C0.528902 2.39859 0.00159113 3.66697 0 4.98999C0 6.27499 0.996894 8.28599 2.96313 10.967C3.1972 11.287 3.50368 11.5474 3.85763 11.7269C4.21158 11.9064 4.60298 12 5 12C5.39702 12 5.78842 11.9064 6.14237 11.7269C6.49631 11.5474 6.80279 11.287 7.03687 10.967C9.00311 8.28599 10 6.27499 10 4.98999C9.99841 3.66697 9.4711 2.39859 8.53375 1.46311C7.59639 0.527637 6.32555 0.00145554 5 0ZM5 6.97899C4.60368 6.97899 4.21627 6.86169 3.88674 6.64193C3.55722 6.42217 3.30039 6.10981 3.14872 5.74436C2.99706 5.37891 2.95738 4.97677 3.03469 4.58881C3.11201 4.20085 3.30286 3.84449 3.58309 3.56478C3.86333 3.28508 4.22038 3.09459 4.60908 3.01742C4.99778 2.94025 5.40068 2.97986 5.76682 3.13124C6.13297 3.28261 6.44592 3.53896 6.6661 3.86785C6.88629 4.19675 7.00381 4.58343 7.00381 4.97899C7.00381 5.50942 6.79269 6.01813 6.41691 6.3932C6.04112 6.76828 5.53144 6.97899 5 6.97899Z" fill="#1D65C0"/>
                </svg>
                <span>{{ requestData.location_point.address }}</span>
            </div>
        </div>

        <div v-if="requestData?.funds" class="row_info">
            <h6 >{{ $t('Budget') }}:</h6>
            <span>
                {{ priceFormat(requestData.funds) }} 
                <template v-if="requestData.funds_currency">{{ requestData.funds_currency.icon }}</template>
            </span>
        </div>



        <!-- Оценка -->
        <div v-if="difficultyStat" class="row_info">
            <h6 >{{ $t('project.all_difficulty') }}:</h6>
            <span>{{ priceFormat(difficultyStat.total_avg) }}</span>
        </div>

        <!-- Программа -->
        <div v-if="requestData.program" class="row_info">
            <h6 >{{ $t("project.program") }}:</h6>
            <span>{{ requestData.program.name }}</span>
        </div>

        <!-- Контрагент -->
        <div v-if="requestData.counterparty" class="row_info">
            <h6 >{{ $t("project.counterparty") }}:</h6>
            <span>{{ requestData.counterparty.name }}</span>
        </div>

        <!-- Объект калькуляции -->
        <div v-if="requestData.costing_object" class="row_info">
            <h6 >{{ $t("project.costing_object") }}:</h6>
            <span>{{ requestData.costing_object.name }}</span>
        </div>

        <div 
            v-if="requestData.organization && requestData.organization.name" 
            class="row_info">
            <h6>
                {{$t('project.organization')}}
            </h6>
            <div 
                class="flex items-center" >
                <!-- @click="openWorkgroup('viewGroup', task.organization)" -->
                <div>
                    <a-avatar 
                        :src="requestData.organization.logo" 
                        icon="team" 
                        :size="32" />
                </div>
                <span class="ml-2">{{ requestData.organization.name }}</span>
            </div>
        </div>


        <!-- Дата основания -->
        <div class="row_info">
            <h6 >{{ $t("project.date_create") }}:</h6>
            <span>{{
                $moment(requestData.created_at).format("DD.MM.YYYY")
            }}</span>
        </div>
        <!-- Соц сети -->
        <div
            v-if="requestData.social_links.length > 0"
            class="social-links flex-column mt-4">
            <h6 >{{ $t("project.social_links") }}:</h6>
            <div
                v-for="link in requestData.social_links"
                :key="link.id"
                class="flex">
                <a
                    class="mt-1"
                    target="_blank"
                    :href="link.social_link">{{ link.social_web_type.name }}</a>
            </div>
        </div>
    </div>
</template>

<script>
import { mapState } from "vuex"
import { priceFormatter } from '@/utils'
export default {
    name: "GroupsAndProjectAbout",
    components: {
        InviteButton: () => import('../../components/InviteButton.vue')
    },
    props: {
        requestData: {
            type: Object,
            required: true
        },
        updatePartisipants: {
            type: Function,
            default: () => {}
        },
        addToMembersList: {
            type: Function,
            default: () => {}
        },
        changeTab: {
            type: Function,
            default: () => {}
        },
        actions: {
            type: Object,
            default: () => null
        },
        active: {
            type: String,
            default: ''
        },
        membersVisibleCount: {
            type: Number,
            default: 5
        },
        createChatLoading: {
            type: Boolean,
            default: false
        },
        createChat: {
            type: Function,
            default: () => {}
        },
        openChat: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        participantsText() {
            return this.memberHidden ? `${this.$t('project.more_participants')} ${this.memberHidden.length}` : this.$t('project.all_participants')
        },
        descLength() {
            if(!this.showDesc && this.requestData?.description?.length > 175)
                return this.requestData.description.substr(0, 175) + '...'
            else
                return this.requestData.description
        },
        isAuthor() {
            if(this.user && this.user.id === this.requestData?.founder?.member?.id)
                return true
            else
                return null
        },
        privateGroup() {
            if(this.requestData?.public_or_private)
                return true
            else
                return false
        },
        percent(){
            return parseInt(((this.requestData.complete_tasks / this.requestData.tasks) * 100).toFixed(2))
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        showParticipantsAside() {
            return this.active !== 'employees'
        },
        founderMember() {
            return this.requestData?.founder?.member || null
        },
        participantsCount() {
            const count = Number(this.requestData?.members_count || 0)
            if (this.founderMember) {
                return Math.max(count - 1, 0)
            }
            return count
        },
        members() {
            const founderId = this.founderMember?.id

            return (this.requestData.workgroup_members || []).filter(item => item?.member?.id !== founderId)
        },
        memberVisible() {
            if(this.members?.length > this.membersVisibleCount)
                return this.members.slice(0, this.membersVisibleCount)
            else
                return this.members
        },
        memberHidden() {
            if(this.members?.length > this.membersVisibleCount)
                return this.members.slice(this.membersVisibleCount, this.members.length)
            else
                return false
        },
        hasParticipantsTab() {
            return this.requestData?.tabs.some(tab => tab.name === 'participants')
        }
    },
    data() {
        return {
            showDesc: false,
            showDescBtn: false,
            budgetStat: null,
            difficultyStat: null
        }
    },
    created() {
        if(this.requestData?.description?.length > 175)
            this.showDescBtn = true

        this.getBudget()
        this.getDifficulty()
    },
    methods: {
        priceFormat(price) {
            return priceFormatter(String(price))
        },
        async getBudget() {
            if(!this.budgetStat) {
                try {
                    const { data } = await this.$http.get('/tasks/budget/aggregate/', {
                        params: {
                            obj: this.requestData.id
                        }
                    })
                    if(data) {
                        this.budgetStat = data
                    }
                } catch(e) {
                    console.log(e)
                }
            }
        },
        async getDifficulty() {
            if(!this.difficultyStat) {
                try {
                    this.loading = true
                    const { data } = await this.$http.get('/tasks/difficulty/aggregate/', {
                        params: {
                            obj: this.requestData.id
                        }
                    })
                    if(data) {
                        this.difficultyStat = data
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.loading = false
                }
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.participants {
    cursor: pointer;
    &:hover{
        color: #4777FF;
    }
}
.count_avatar{
    background: transparent!important;
    color: var(--text)!important;
    font-size: 14px!important;
}
.member{
    &:not(:last-child){
        margin-bottom: 10px;
    }
}
.slide-fade-enter-active {
  transition: all .3s ease;
}
.slide-fade-leave-active {
  transition: all .3s cubic-bezier(1.0, 0.5, 0.8, 1.0);
}
.slide-fade-enter, .slide-fade-leave-to{
  transform: translateY(-10px);
  opacity: 0;
}
.row_progress{
    &::v-deep{
        .ant-progress-inner{
            @media (min-width: 768px) {
                background: #fff;
            }
        }
        .ant-progress-text{
            color: #888888;
        }
    }
}
.col_aside{
    &__title{
        font-size: 16px;
        margin-bottom: 10px;
        color: #000;
    }
    &::v-deep{
        .ant-progress{
            .ant-progress-inner{
                @media (min-width: 768px) {
                    background: #fff;
                }
            }
        }
    }
    .col_mobile{
        padding: 0px;
        background: #fff;
        border-radius: 0px;
        &::v-deep{
            .ant-progress{
                .ant-progress-inner{
                    background-color: #f5f5f5;
                }
            }
        }
    }
}
.row_info{
    h6{
        opacity: 0.6;
    }
    .all_participants {
        width: 100%;
        align-items: center;
        display: flex;
        justify-content: space-between;
        color: #4777FF;
        cursor: pointer;
    }
    .white-background {
        border-radius: 8px;
        padding: 0 8px;
        height: 36px;
        &:hover{
            background-color: #fff;
        }
    }
}
.desc_more{
    color: var(--primaryColor);
    border-bottom: 1px dashed;
    cursor: pointer;
    font-size: 13px;
}
.row_info {
    padding: 0.5rem 0;
    color: #000;
}
.direction_tags{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    &::v-deep{
        .ant-tag{
            margin-right: 0;
        }
    }
}
.participants_aside_block {
    overflow: hidden;
}
</style>
