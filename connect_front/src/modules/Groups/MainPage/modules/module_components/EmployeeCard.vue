<template>
    <div class="employee" ref="employee_card">
        <Profiler
            nameClass="text-sm"
            initStatus
            :getPopupContainer="getPopupContainer"
            :popoverText="employee.membership_role.code === 'FOUNDER' ? $t('project.director') : '' || employee.membership_role.code === 'MODERATOR' ? $t('project.moderator') : ''"
            :subtitle="{ text: employee.membership_role.name, class: 'text-xs' }"
            :user="employee.member" />
    </div>
</template>
<script>
export default {
    name: 'EmployeeCard',
    props: {
        employee: {
            type: Object,
            required: true
        }
    },
    methods: {
        getPopupContainer() {
            return this.$refs[`employee_card`]
        },
    }
    
}
</script>
<style lang="scss" scoped>
.employee {
    border: 1px solid rgba(240, 242, 255, 1);
    border-radius: 6px;
    background-color: rgba(251, 251, 251, 1);
    padding: 12px 12px;
}
</style>