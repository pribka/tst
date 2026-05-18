<template>
    <div class="org-card">
        <div class="top">
            <div>
                <div class="mb-2">
                    <a-tag :color="member.status.color">{{ member.status.name}}</a-tag>
                </div>

                <div class="name">
                    {{ member.organization.name || 'Не указано' }}
                </div>
            </div>
            <div v-if="showEditButton" class="edit-button">
                <a-button 
                    type="ui" 
                    flaticon
                    ghost
                    shape="circle"
                    icon="fi-rr-edit"
                    @click="editMemberOrg(member)" />
            </div>
        </div>
        <div class="role" :class="{ 'no-data': !member.role.name}">
            {{ member.role.name || 'Роль организации не указана' }}
        </div>
        <div class="employees">
            <EmployeeCard
                v-for="employee in member.employees"
                :key="employee.id"
                :employee="employee" />
        </div>
    </div>
</template>

<script>
export default {
    name: 'MemberOrgCard',
    components: {
        EmployeeCard: () => import('./EmployeeCard.vue')
    },
    props: {
        member: {
            type: Object,
            required: true
        },
        editMemberOrg: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        showEditButton() {
            return this.member.isEditAvailable || false
        }
    }
}
</script>
<style lang="scss" scoped>
.org-card{
    border: 1px solid rgba(217, 217, 217, 1);
    border-radius: 8px;
    padding: 20px;
    font-weight: 400;
    font-size: 14px;
    display: flex;
    flex-direction: column;
    .top {
        display: flex;
        justify-content: space-between;
        gap: 20px;
        .name {
            color: rgba(0, 0, 0, 1);
            font-size: 16px;
            line-height: 100%;
            margin-bottom: 10px;
        }
        .edit-button {
            align-self: flex-start;
        }
    }
    .role {
        margin-top: 8px;
        font-weight: 400;
        font-size: 14px;
        line-height: 100%;
        color: rgba(0, 0, 0, 0.6)
    }
    .employees {
        margin-top: 20px;
        width: 100%;
        display: flex;
        gap: 20px;
        flex-wrap: wrap;
    }
    .no-data {
        opacity: 0.6;
    }
}
</style>