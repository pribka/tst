<template>
    <div 
        @click="moreBtn()" 
        style="cursor: pointer">
        <a-card class="group_card" :class="isMobile && 'is_mobile'">
            <div class="flex items-center card_header justify-between mb-3 pb-3">
                <div class="info flex items-center truncate">
                    <div>
                        <a-avatar 
                            :size="isMobile ? 30 : 40" 
                            icon="team" 
                            :src="image" />
                    </div>
                    <h2 
                        class="ml-3 truncate"
                        :class="isMobile ? 'text-base' : 'text-lg'">
                        {{ title }}
                    </h2>
                </div>
                <div 
                    v-if="isAuthor || dead_line" 
                    class="pl-2 flex items-center">
                    <a-tag
                        v-if="isAuthor && !isMobile"
                        class="mr-0"
                        color="green">
                        {{ $t('project.is_author') }}
                    </a-tag>
                </div>
            </div>

            <div 
                v-if="desc" 
                class="flex justify-between text-gray card_desc"
                :class="isMobile ? 'mb-2' : 'mb-3'">
                <span 
                    class="text-sm" 
                    style="word-wrap: break-word; overflow-x: hidden;">
                    {{desc}}
                </span>
            </div>

            <a-row 
                class="mt-2 text-gray" 
                :gutters="16" 
                type="flex">
                <a-col 
                    :sm="1" 
                    :lg="19" 
                    :span="16"  
                    class="flex-col flex"
                    :class="isMobile && 'w-full'">
                    <div class="flex items-center">
                        <a-tooltip 
                            class="flex items-center" 
                            :title="$t('project.task')">
                            <i class="fi fi-rr-list"></i>
                            <span class="ml-2">
                                {{ alltask }}
                            </span>
                        </a-tooltip>

                        <a-tooltip 
                            class="flex items-center ml-4" 
                            :title="$t('project.tasks_complete')">
                            <i class="fi fi-rr-list-check"></i>
                            <span class="ml-2">
                                {{ completetask }}
                            </span>
                        </a-tooltip>

                        <a-tooltip 
                            v-if="comments" 
                            class="flex items-center ml-4" 
                            :title="$t('project.comments')">
                            <i class="fi fi-rr-comment-alt"></i>
                            <span class="ml-2">
                                {{ comments }}
                            </span>
                        </a-tooltip>
                    </div>
                    <div 
                        v-if="dead_line || date_start_plan" 
                        class="flex items-center mt-2">
                        <a-tag 
                            v-if="date_start_plan"
                            v-tippy="{ inertia : true}"
                            :content="$t('project.date_start_plan')">
                            {{ $moment(date_start_plan).format("DD.MM.YYYY HH:mm") }}
                        </a-tag>
                        <a-tag 
                            v-if="dead_line"
                            v-tippy="{ inertia : true}"
                            :content="$t('project.deadline_project')"
                            color="purple">
                            {{ $moment(dead_line).format("DD.MM.YYYY HH:mm") }}
                        </a-tag>
                    </div>

                    <a-progress
                        class="mt-3"
                        :stroke-color="{
                            '0%': '#108ee9',
                            '100%': '#87d068',
                        }"
                        :percent="percent"/>

                    <div 
                        class="lg:flex items-center mt-4"
                        :class="isMobile && 'flex'">
                        <!-- Участники -->
                        <ul 
                            class="flex">
                            <li 
                                v-for="el in participants.slice(0, 4)" 
                                :key="el.id">
                                <a-tooltip :title="userAuthor(el)" >
                                    <a-avatar 
                                        :src="el.member.avatar && el.member.avatar.path" 
                                        icon="user" 
                                        :size="25" 
                                        class="border-2 border-white border-solid -m-1" />
                                </a-tooltip>
                            </li>
                        </ul>
                        <small 
                            class="text-sm ml-2">
                            {{ participantsText }}
                        </small>
                    </div>
                    
                </a-col>
            </a-row>
        </a-card>
    </div>
</template>

<script>
import { mapState } from 'vuex'
import {declOfNum} from './utils'
export default {
    name: "GroupsAndProjectCard",
    props: {
        image: [String],
        title: [String],
        description: [String],
        director: [String, Object],
        participants: [Array, Object],
        type: [String],
        status: [String, Boolean],
        alltask: [String, Number],
        completetask: [String, Number],
        comments: [String, Number],
        members_count: [String, Number],
        dead_line: {
            type: String,
            default: ''
        },
        date_start_plan: {
            type: String,
            default: ''
        }
    },
    computed:{
        ...mapState({ 
            user: state => state.user.user,
            isMobile: state => state.isMobile
        }),
        desc() {
            if(this.description) {
                if(this.description && this.description.length > 110)
                    return this.description.substr(0, 110)
                else
                    return this.description
            } else
                return null
        },
        isAuthor() {
            if(this.user && this.user.id === this.director.id) {
                return true
            } else
                return null
        },
        percent(){
            return parseInt(((this.completetask / this.alltask) * 100).toFixed(2))
        },
        participantsText() {
            return this.members_count + ' ' +
             declOfNum(this.participants.length, [this.$t('project.participant'), this.$t('project.participant2'), this.$t('project.participant3')])
        }
    },
    methods: {
        moreBtn() {
            this.$emit("eventMore");
        },
        userAuthor(user) {
            if(user.member.id === this.director.id)
                return `${this.$t('project.author')}: ${user.member.last_name} ${user.member.first_name}`
            else
                return `${this.$t('project.participant')}: ${user.member.last_name} ${user.member.first_name}`
        }
    }
}
</script>

<style lang="scss">
.group_card{
    height: 100%;
    &.is_mobile{
        background: #fff;
    }
    .ant-card-body{
        display: flex;
        flex-direction: column;
        height: 100%;
    }
    .card_desc{
        flex-grow: 1;
        font-weight: 300;
    }
}
.card_header{
    border-bottom: 1px dashed var(--borderColor);
    .ant-avatar{
        border: 1px solid var(--border2);
    }
}
</style>

<style lang="scss" scoped>
.title {
    font-size: 16px;
    font-weight: 500;
}
.text {
    font-size: 14px;
    font-weight: 300;
}
.text-medium {
    font-size: 12px;
    font-weight: 500;
}
.column {
    display: flex;
    flex-direction: column;
}
</style>
