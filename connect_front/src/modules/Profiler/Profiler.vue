<template>
    <a-popover
        v-if="user"
        :value="isPopupVisible"
        overlayClassName="profile_popover"
        :title="popoverTitle ? popoverTitle : ''"
        :mouseEnterDelay="mouseEnterDelay"
        :getPopupContainer="getPopupContainer"
        :mouseLeaveDelay="mouseLeaveDelay"
        :trigger="trigger"
        :destroyTooltipOnHide="destroyOnHide"
        @visibleChange="visibleChange">
        <template v-if="showPopup" slot="content">
            <div class="flex items-start">
                <div class="mr-2 mt-1 profile_badge">
                    <a-badge :color="statusColor">
                        <a-avatar
                            :key="user.id"
                            avResize
                            :size="32"
                            :src="user.avatar && user.avatar.path ? user.avatar.path : ''"
                            icon="user" />
                    </a-badge>
                </div>
                <div>
                    <div class="user-name flex items-center">
                        <span :class="user.is_support && 'mr-1'">
                            {{userName}}
                        </span>
                        <template v-if="user.is_support">
                            <i 
                                class="fi fi-rr-headset support_badge" 
                                :content="$t('profiler.techSupport')"
                                v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }" />
                        </template>
                    </div>

                    
                    <div v-if="popoverText"
                         class="text-gray text_mail extra_info">
                        {{popoverText}}
                    </div>
                    <div 
                        v-if="birthdayDay" 
                        class="extra_info mb-1 text_green">
                        {{ birthdayDay }}
                    </div>
                    <div 
                        v-if="user.company" 
                        class="extra_info">
                        {{user.company}}
                    </div>
                    <div 
                        v-if="user.job_title" 
                        class="extra_info">
                        {{user.job_title}}
                    </div>
                    <div 
                        v-if="user.contact_phone" 
                        class="extra_info">
                        <a :href="`tel:${user.contact_phone}`">{{user.contact_phone}}</a>
                    </div>
                    <div 
                        v-if="user.email" 
                        class="text_mail extra_info">
                        {{user.email}}
                    </div>
                    <div 
                        v-if="user.last_activity && !isOnline" 
                        class="extra_info">
                        {{ $t('profiler.visited') }} {{ $moment(user.last_activity).format('DD.MM.YYYY HH:mm') }}
                    </div>
                    <slot name="actions" />
                    <div 
                        v-if="showTaskButton || showChat" 
                        class="mt-2 profile_menu">
                        <a-button
                            v-if="showTaskButton && !appType"
                            size="small"
                            type="ui"
                            block
                            icon="fi-rr-add"
                            flaticon
                            @click="createTask()">
                            {{$t('profiler.add_task')}}
                        </a-button>
                        <a-button
                            v-if="showChat && !appType"
                            size="small"
                            block
                            type="ui"
                            flaticon
                            icon="fi-rr-comment"
                            @click="writeMessage()">
                            {{$t('profiler.write_a_message')}}
                        </a-button>
                    </div>
                </div>
            </div>
        </template>
        <slot>
            <div 
                :class="wrapperClass"
                class="user_profile profile_badge"
                @click="$emit('click')">
                <div 
                    v-if="showUserName" 
                    class="flex items-center">
                    <div v-if="showAvatar" class="mr-2">
                        <template v-if="initStatus">
                            <a-badge 
                                :color="statusColor" 
                                :class="avatarSize < 20 && 'badge_xs' || avatarSize < 25 && 'badge_sm'">
                                <a-avatar
                                    :size="avatarSize" 
                                    :key="user.id"
                                    avResize
                                    :src="user.avatar && user.avatar.path ? user.avatar.path : ''"
                                    icon="user" />
                            </a-badge>
                        </template>
                        <template v-else>
                            <a-avatar
                                :size="avatarSize" 
                                :key="user.id"
                                avResize
                                :src="user.avatar && user.avatar.path ? user.avatar.path : ''"
                                icon="user" />
                        </template>
                    </div>
                    <div class="flex-grow" :class="nameWrapperClass">
                        <div :class="[nameClass, showSupportTag && 'flex items-center']">
                            <span :class="showSupportTag && 'mr-1'">
                                {{userName}}
                            </span>
                            <template v-if="showSupportTag">
                                <i 
                                    class="fi fi-rr-headset support_badge"
                                    v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }"
                                    :content="$t('profiler.techSupport')"  />
                            </template>
                        </div>
                        <div v-if="showCurrentContractor">
                            <span v-if="currentContractor" class="default-organization">
                                {{currentContractor}}
                            </span>
                            <span v-else class="default-organization text-gray-400">
                                {{ $t('org_no_select') }}
                            </span>
                        </div>
                        <div
                            v-if="subtitle"
                            class="text-gray" :class="subtitle.wrapClass && subtitle.wrapClass">
                            <span :class="subtitle.class && subtitle.class">
                                {{subtitle.text}}
                            </span>
                        </div>
                    </div>
                </div>
                <template v-else>
                    <template v-if="initStatus">
                        <a-badge 
                            :color="statusColor" 
                            :class="avatarSize < 20 && 'badge_xs' || avatarSize < 25 && 'badge_sm'">
                            <a-avatar
                                :key="user.id"
                                :size="avatarSize"
                                icon="user"
                                avResize
                                :src="user.avatar && user.avatar.path ? user.avatar.path : ''" />
                        </a-badge>
                    </template>
                    <template v-else>
                        <a-avatar
                            :size="avatarSize"
                            :key="user.id"
                            icon="user"
                            avResize
                            :src="user.avatar && user.avatar.path ? user.avatar.path : ''" />
                    </template>
                </template>
            </div>
        </slot>
    </a-popover>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { mapState } from 'vuex'
export default {
    name:'Profiler',
    inheritAttrs:false,
    props: {
        user: {
            type: Object,
            required: true
        },
        subtitle: {
            type: Object,
            default: null
        },
        showAvatar: {
            type: Boolean,
            default: true
        },
        showCurrentContractor: {
            type: Boolean,
            default: false
        },
        showUserName: {
            type: Boolean,
            default: true
        },
        wrapperClass: {
            type: String,
            default: 'inline-block'
        },
        avatarSize: {
            type: Number,
            default: 32
        },
        nameClass: {
            type: String,
            default: ''
        },
        nameWrapperClass: {
            type: String,
            default: ''
        },
        mouseLeaveDelay: {
            type: Number,
            default: 0.9
        },
        mouseEnterDelay: {
            type: Number,
            default: 1.1
        },
        isPopupVisible: Boolean,
        destroyOnHide: {
            type: Boolean,
            default: true
        },
        showTaskButton: {
            type: Boolean,
            default: false
        },
        showChatButton: {
            type: Boolean,
            default: true
        },
        popoverTitle: {
            type: String,
            default: ''
        },
        getPopupContainer: {
            type: Function,
            default: () => document.body
        },
        popoverText: {
            type: String,
            default: ''
        },
        initStatus: {
            type: Boolean,
            default: false
        },
        hideSupportTag: {
            type: Boolean,
            default: false
        },
        showPopup: {
            type: Boolean,
            default: true
        },
        trigger: {
            type: String,
            default: 'hover'
        }
    },
    computed: {
        ...mapState({
            appType: state => state.appType
        }),
        currentContractor() {
            return this.user?.current_contractor?.name?.length > 0
                ? this.user.current_contractor.name
                : this.user?.current_contractor?.full_name?.length > 0
                    ? this.user.current_contractor.full_name
                    : ''
        },
        userId() {
            return this.user.id
        },
        showSupportTag() {
            return !this.hideSupportTag && this.user?.is_support
        },
        isOnline() {
            return this.$store.getters['user/getUserStatus'](this.userId)
        },
        firstCheck() {
            return this.$store.getters['user/getUserFirstCheck'](this.userId)
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        currentUser() {
            if(this.$store.state.user.user)
                return this.$store.state.user.user
            else
                return null
        },
        userName() {
            if(this.user)
                if(this.user.last_name || this.user.first_name)
                    return `${this.user.last_name} ${this.user.first_name}`
                else
                    return this.user.full_name
            else
                return ''
        },
        showChat() {
            if(this.showChatButton) {
                if(this.currentUser?.id !== this.userId)
                    return true
                else
                    return false
            } else
                return false
        },
        statusColor() {
            if(this.user.last_activity) {
                if(this.isOnline)
                    return '#52c41a'
                else
                    return '#f5222d'
            } else
                return '#808080'
        },
        birthdayDay() {
            if(this.user.birthday) {
                if(this.user.birthday === this.$moment().format('YYYY-MM-DD'))
                    return this.$t('profiler.birthdayToday')
            }
            return null
        }
    },
    created() {
        if(this.initStatus && !this.firstCheck && this.user.last_activity)
            this.$store.commit('user/SET_ONLINE_USER_EVENT', this.user)
    },
    methods: {
        visibleChange(vis) {
            if(vis && !this.firstCheck && this.user.last_activity)
                this.$store.commit('user/SET_ONLINE_USER_EVENT', this.user)
        },
        writeMessage() {
            if(this.isMobile) {
                if(this.$route.name === 'chat-body') {
                    this.$router.replace({name: 'chat-body', params: { id: this.userId }, query: { user: this.userId }})
                        .then(() => {
                            this.$nextTick(() => {
                                eventBus.$emit('RELOAD_ACTIVE_CHAT')
                            })
                        })
                } else
                    this.$router.push({name: 'chat-body', params: { id: this.userId }, query: { user: this.userId }})
            } else {
                if(this.$route.query?.chat_id) {
                    this.$router.replace({query: {user: this.userId}})
                        .then(() => {
                            this.$nextTick(() => {
                                eventBus.$emit('RELOAD_ACTIVE_CHAT')
                            })
                        })
                } else
                    this.$router.push({name: 'chat', query: {user: this.userId}})
            }
        },
        createTask() {
            let form = {
                operator: this.user
            }
            eventBus.$emit('ADD_WATCH', {type: 'add_task', data: form})
        }
    }
}
</script>

<style lang="scss">
.profile_popover {
    z-index: 1500;
    .ant-popover-arrow{
        display: none;
    }
    &.ant-popover-placement-bottom, 
    &.ant-popover-placement-bottomLeft, 
    &.ant-popover-placement-bottomRight{
        padding-top: 0px;
    }
    &.ant-popover-placement-top, 
    &.ant-popover-placement-topLeft, 
    &.ant-popover-placement-topRight{
        padding-bottom: 0px;
    }
}
</style>

<style lang="scss" scoped>
.default-organization {
    font-size: 12px;
}
.profile_badge{
    &::v-deep{
        .ant-badge{
            display: block;
            &.badge_sm{
                .ant-badge-dot{
                    width: 6px !important;
                    height: 6px !important;
                }
            }
            &.badge_xs{
                .ant-badge-dot{
                    top: 3px;
                    width: 4px !important;
                    height: 4px !important;
                }
            }
            &:not(.badge_sm),
            &:not(.badge_xs){
                .ant-badge-dot{
                    width: 8px !important;
                    height: 8px !important;
                    top: 5px!important;
                    right: 3px!important;
                }
            }
        }
    }
}
.extra_info {
    font-size: 12px;
}
.user-name {
    margin-bottom: 10px;
    max-width: 250px;
}
.text_mail {
    margin-top: 5px;
}
.support_badge{
    font-size: 11px;
    margin-left: 2px;
}
</style>