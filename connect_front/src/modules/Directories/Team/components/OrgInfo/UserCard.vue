<template>
    <div 
        class="user_card"
        v-touch:longtap="longtapHandler">
        <UserCardActions 
            ref="userCardActions"
            :item="item"
            :actions="actions"
            :organization="org" />

        <div class="flex items-center mb-3">
            <Profiler
                :user="item"
                initStatus
                :avatarSize="35" />
            <a-tag 
                v-if="isAuthor(item.id)" 
                color="green" 
                class="ml-2 crown" 
                v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }" 
                :content="$t('team.administrator')">
                <i class="fi fi-rr-crown"></i>
            </a-tag>
        </div>
        <div v-if="item.email" class="user_card__row">
            <div class="user_card__row--label">
                <i class="fi fi-rr-envelope"></i>
            </div>
            <div class="user_card__row--value">
                {{ item.email }}
            </div>
        </div>
        <div v-if="item.job_title" class="user_card__row">
            <div class="user_card__row--label">
                {{ item.job_title }}
            </div>
        </div>
        <div v-if="item.last_activity" class="user_card__row">
            <div class="user_card__row--label">
                {{ $t('team.last_activity') }}:
            </div>
            <div class="user_card__row--value">
                {{ $moment(item.last_activity).format('DD.MM.YYYY HH:mm') }}
            </div>
        </div>
        <a-button
            v-if="canManageEmployee"
            type="flat_primary"
            block
            class="mt-3"
            @click="fireEmployee(item)">
            {{ $t('team.fire_employee_fire_action') }}
        </a-button>
    </div>
</template>

<script>
import { mapState } from 'vuex'
import UserCardActions from './UserCardActions.vue'
export default {
    components: {
        UserCardActions
    },
    props: {
        item: {
            type: Object,
            required: true
        },
        deleteUser: {
            type: Function,
            default: () => {}
        },
        leaveOrg: {
            type: Function,
            default: () => {}
        },
        fireEmployee: {
            type: Function,
            default: () => {}
        },
        actions: {
            type: Object,
            default: () => null
        },
        org: {
            type: Object,
            required: true
        }
    },
    computed: {
        ...mapState({
            isMobile: state => state.isMobile,
            user: state => state.user.user
        }),
        canManageEmployee() {
            return Boolean(this.actions?.edit?.availability)
        },
        showLeaveButton(record) {
            return false // !! Заглушка. Кнопка Скрыта Т.к. не проработан функционал
            // когда пользователь не принадлежит ни к какой организации. (Задача 10819)
            return (this.user?.id === record.id) && !this.actions?.edit
        },
        showRemoveEmployeeButton(record) {
            return false // !! Заглушка. Кнопка Скрыта Т.к. не проработан функционал
            // когда пользователь не принадлежит ни к какой организации. (Задача 10819)
            return !this.isAuthor(record.id) && (this.actions?.edit) && (this.user?.id !== record.id)
        },
    },
    methods: {
        isAuthor(id) {
            return this.org?.director?.id === id
        },
        longtapHandler() {
            if(this.isMobile) {
                this.$refs[`userCardActions`].openDrawer()
            }
        },
    },
}
</script>

<style lang="scss" scoped>
.user_card{
    padding: 12px;
    zoom: 1;
    color: #505050;
    font-size: 14px;
    font-variant: tabular-nums;
    line-height: 1.5;
    list-style: none;
    font-feature-settings: "tnum";
    background: #fff;
    border-radius: var(--borderRadius);
    border: 1px solid var(--border1);
    margin-bottom: 10px;
    -webkit-user-select: none;
    -moz-user-select: none;
    user-select: none;
    transition: all 0.5s cubic-bezier(0.645, 0.045, 0.355, 1);

    &.touch{
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
        transform: scale(0.97);
    }
    &__row{
        display: flex;
        align-items: center;
        &:not(:last-child){
            margin-bottom: 5px;
        }
        &--label{
            margin-right: 5px;
            color: var(--gray);
        }
    }
}
</style>
