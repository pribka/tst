<template>
    <div class="col_aside" :class="isMobile && 'col_mobile'">
        <!--<div v-if="isMobile" class="row_info">
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
        </div>-->
        <div 
            v-if="isAuthor || privateGroup" 
            class="row_info flex-items-center">
            <a-tag 
                v-if="isAuthor"
                class="mr-2"
                color="green">
                {{ $t('wgr.is_author') }}
            </a-tag>
            <a-tag
                v-if="privateGroup"
                color="red">
                {{ $t('wgr.closed') }}
            </a-tag>
        </div>
        <div v-if="descLength.length" class="user-bio row_info">
            <h6 >{{ $t('wgr.description')}}:</h6>
            <p class="break-words">
                {{ descLength }}
            </p>
            <div v-if="showDescBtn">
                <span 
                    class="desc_more" 
                    @click="showDesc = !showDesc">
                    {{ showDesc ? $t('wgr.hide') : $t('wgr.more') }}
                </span>
            </div>
        </div>

        <!-- Срок сдачи проекта -->
        <!--<div v-if="requestData.dead_line !== null" class="row_info">
            <h6 >{{ $t("wgr.deadline_project") }}:</h6>
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
                    {{ $t('wgr.control_on') }}
                </span>
            </a-tag>
        </div>-->

        <!-- Дата начала -->
        <div v-if="requestData.date_start_plan !== null" class="row_info">
            <h6 >{{ $t("wgr.date_start_plan") }}:</h6>
            {{  $moment(requestData.date_start_plan).format("DD.MM.YYYY HH:mm") }}
        </div>

        <!-- Тип клуба -->
        <div 
            v-if="requestData.workgroup_type !== undefined && requestData.workgroup_type.name !== ''" 
            class="row_info">
            <h6 >{{ $t("wgr.type") }}:</h6>
            <span>{{
                requestData.workgroup_type !== undefined
                    ? requestData.workgroup_type.name
                    : ""
            }}</span>
        </div>

        <!-- Кол-во участников -->
        <!--<div 
            v-if="requestData.members_count" 
            class="row_info">
            <h6 v-if="hasParticipantsTab">
                <span class="participants" @click="changeTab('participants')">{{`${$t("wgr.participants")} (${requestData.members_count})`}}:</span>
            </h6>
            <h6 v-else>{{ `${$t("wgr.participants")} (${requestData.members_count})` }}:</h6>
            <div class="flex flex-col pt-[5px]">
                <div 
                    v-for="item, index in memberVisible" 
                    :key="`${item.id}_${index}`"
                    class="member flex items-center">
                    <Profiler
                        :avatarSize="26"
                        nameClass="text-sm"
                        :popoverText="item.membership_role.name"
                        :showUserName="true"
                        :user="item.member" />
                </div>
                <div v-if="hasParticipantsTab" class="all_participants white-background" @click="changeTab('participants')">
                    <div class="participants">{{ participantsText }}</div>
                    <i class="fi fi-rr-arrow-up-right"></i>
                </div>
            </div>
        </div>-->
        <transition name="slide-fade">
            <InviteButton
                v-if="actions && actions.add_member"
                :requestData="requestData"
                :updatePartisipants="updatePartisipants" />
        </transition>
        
        <!--<div v-if="requestData.tasks" class="row_info">
            <div class="row_info" :class="isMobile && 'flex'">
                <h6 >{{ $t("wgr.count_task") }}:</h6>
                <span :class="isMobile && 'ml-2'">{{ requestData.tasks }}</span>
            </div>
    
            <div v-if="requestData.complete_tasks" :class="isMobile && 'flex'">
                <h6 >{{ $t("wgr.tasks_complete") }}:</h6>
                <span :class="isMobile && 'ml-2'">{{ requestData.complete_tasks }}</span>
            </div>
    
            <div v-if="requestData.is_project">
                <a-progress
                    :stroke-color="{
                        '0%': '#108ee9',
                        '100%': '#87d068',
                    }"
                    :percent="percent"/>
            </div>
        </div>-->

        <!--<div v-if="budgetStat" class="row_info">
            <h6 >{{ $t('wgr.all_budget') }}:</h6>
            <span>{{ priceFormat(budgetStat.total_sum) }} <template v-if="budgetStat.currency">{{ budgetStat.currency.icon }}</template></span>
        </div>

        <div v-if="difficultyStat" class="row_info">
            <h6 >{{ $t('wgr.all_difficulty') }}:</h6>
            <span>{{ priceFormat(difficultyStat.total_avg) }}</span>
        </div>

        <div v-if="requestData.program" class="row_info">
            <h6 >{{ $t("wgr.program") }}:</h6>
            <span>{{ requestData.program.name }}</span>
        </div>

        <div v-if="requestData.counterparty" class="row_info">
            <h6 >{{ $t("wgr.counterparty") }}:</h6>
            <span>{{ requestData.counterparty.name }}</span>
        </div>

        <div v-if="requestData.costing_object" class="row_info">
            <h6 >{{ $t("wgr.costing_object") }}:</h6>
            <span>{{ requestData.costing_object.name }}</span>
        </div>-->

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
            <h6 >{{ $t("wgr.date_create") }}:</h6>
            <span>{{
                $moment(requestData.created_at).format("DD.MM.YYYY")
            }}</span>
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
        changeTab: {
            type: Function,
            default: () => {}
        },
        actions: {
            type: Object,
            default: () => null
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
            return this.memberHidden ? `${this.$t('wgr.more_participants')} ${this.memberHidden.length}` : this.$t('wgr.all_participants')
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
        members() {
            const members = [...this.requestData.workgroup_members]
            for (let i = members.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [members[i], members[j]] = [members[j], members[i]]
            }
            return members
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
.col_aside{
    &__title{
        font-size: 16px;
        margin-bottom: 10px;
        color: #000;
    }
    &::v-deep{
        .ant-progress{
            .ant-progress-inner{
                background: #fff;
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
}
</style>