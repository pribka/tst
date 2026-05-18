<template>
    <a-drawer
        class="add-org-drawer"
        :visible="visible"
        :zIndex="zIndex"
        :width="drawerWidth"
        title="Добавить организацию"
        :afterVisibleChange="afterVisibleChange"
        @close="onAddOrgDrawerClose()" >
        <a-spin :spinning="loading" class="spinner">
            <a-form-model ref="addOrgForm" :model="form">
                <div class="content" ref="contentWrapper">
                    <div v-if="form.organization" class="selected-org appearance-anim" ref="selectedOrg">
                        <OrgCard
                            :organization="form.organization"
                            :showSelectButton="false" />
                        <div class="org-role" v-if="!isEdit">
                            <div class="label">Роль организации в проекте</div>
                            <div class="form">
                                <div class="field">
                                    <a-form-model-item
                                        prop="role" 
                                        ref="role" 
                                        :rules="{
                                            required: true,
                                            message: $t('field_required'),
                                            trigger: ['change', 'blur']
                                        }">
                                        <a-select
                                            size="large"
                                            placeholder="Укажите роль организации в проекте"
                                            v-model="form.role"
                                            class="w-full"
                                            auto-focus
                                            :getPopupContainer="getPopupContainer">
                                            <a-select-option v-for="role in orgRoles" :key="role.id" :value="role.code">
                                                {{ role.name }}
                                            </a-select-option>
                                        </a-select>
                                    </a-form-model-item>
                                </div>
                            </div>
                        </div>
                        <div class="employees">
                            <div class="label">Добавить сотрудников</div>
                            <div class="list">
                                <div v-for="(item, index) in form.employees" :key="index" class="item" :class="{'item--with-delete-button': isEdit}">
                                    <div class="employee">
                                        <a-form-model-item
                                            :prop="'employees.' + index + '.employee'" 
                                            :ref="'employees.' + index + '.employee'" 
                                            :rules="{
                                                required: true,
                                                trigger: ['change', 'blur']
                                            }">
                                            <a-select
                                                v-model="item.employee"
                                                class="w-full"
                                                size="large"
                                                placeholder="Сотрудник"
                                                :disabled="isEmployeeEditDisabled(item)"
                                                :getPopupContainer="getPopupContainer">
                                                <a-select-option v-for="employee in orgEmployees" :key="employee.id" :value="employee.id" :disabled="isEmployeeOptionDisabled(employee)">
                                                    {{ employee.full_name }}
                                                </a-select-option>
                                            </a-select>
                                        </a-form-model-item>
                                    </div>
                                    <div class="role">
                                        <a-form-model-item
                                            :prop="'employees.' + index + '.role'" 
                                            :ref="'employees.' + index + '.role'" 
                                            :rules="{
                                                required: true,
                                                trigger: ['change', 'blur']
                                            }">
                                            <a-select
                                                v-model="item.role"
                                                class="w-full"
                                                size="large"
                                                placeholder="Роль в проекте"
                                                :disabled="isEmployeeRoleEditDisabled(item)"
                                                :getPopupContainer="getPopupContainer">
                                                <a-select-option v-for="role in membershipRoles" :key="role.id" :value="role.code" :disabled="isRoleOptionDisabled(role.code)">
                                                    {{ role.name }}
                                                </a-select-option>
                                            </a-select>
                                        </a-form-model-item>
                                    </div>
                                    <div v-if="isEdit" class="delete-button">
                                        <a-button 
                                            type="ui" 
                                            class="text_red"
                                            flaticon
                                            ghost
                                            shape="circle"
                                            icon="fi-rr-trash"
                                            :disabled="isDeleteDisabled(item)"
                                            @click="deleteEmployee(item, index)" />
                                    </div>
                                </div>
                            </div>
                            <div v-if="isEdit" class="add-employee" @click="addEmployee">
                                + Добавить сотрудника
                            </div>
                        </div>
                        <div class="buttons">
                            <div class="save-cancel">
                                <a-button
                                    size="large"
                                    type="primary"
                                    @click="addOrgInProject">
                                    {{ isEdit ? 'Сохранить' : 'Добавить организацию в проект' }}
                                </a-button>
                                <a-button
                                    size="large"
                                    @click="cancel">
                                    Отмена
                                </a-button>
                            </div>
                            <div v-if="showDelete" class="delete">
                                <a-button
                                    size="large"
                                    class="member-org-delete-button"
                                    @click="showDeleteConfirm">
                                    Исключить организацию
                                </a-button>
                            </div>
                        </div>
                    </div>
                    <div v-else class="org-select appearance-anim" ref="orgSelect">
                        <div class="info">
                            Вы можете добавить другую организацию зарегистрированную в системе<br>
                            для совместной работы над общими проектами
                        </div>
                        <div class="search">
                            <div class="label">Наименование организации или БИН</div>
                            <div class="form">
                                <div class="field">
                                    <a-input
                                        ref="searchInput"
                                        size="large"
                                        placeholder="Введите наименование организации или БИН"
                                        v-model="searchText"
                                        auto-focus
                                        @pressEnter="search"/>
                                </div>
                                <div class="button">
                                    <!-- :loading="loading" -->
                                    <a-button
                                        size="large"
                                        class="w-full"
                                        type="primary"
                                        :block="isMobile"
                                        :disabled="searchText.length < 3 || loading"
                                        @click="search">
                                        Найти организацию
                                    </a-button>
                                </div>
                            </div>
                        </div>
                        <div class="org-list">
                            <OrgCard
                                v-for="organization in organizations"
                                :key="organization.id"
                                :organization="organization"
                                @select="selectOrganization" />
                        </div>
                    </div>
                </div>
            </a-form-model>
        </a-spin>
    </a-drawer>
</template>

<script>
import { mapState } from 'vuex'
import eventBus from "@/utils/eventBus"
import { errorHandler } from '@/utils/index.js'
export default {
    name: 'AddOrganizationDrawer',
    components: {
        OrgCard: () => import('./OrgCard.vue')
    },
    props: {
        onAddOrgDrawerClose: {
            type: Function,
            default: () => {}
        },
        zIndex: {
            type: Number,
            default: 1100
        },
        visible: {
            type: Boolean,
            default: false
        },
        isEdit: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            form: {
                organization: null,
                role: undefined,
                employees: [
                    {
                        employee: undefined,
                        role: undefined,
                    },
                ]
            },
            windowWidth: window.innerWidth,
            searchText: '',
            loading: false,
            organizations: [],
            orgRoles: [],
            orgEmployees: [],
            membershipRoles: [],
            disabledRoles: new Set(['FOUNDER', 'MODERATOR'])
        }
    },
    computed: {
        drawerWidth() {
            if(this.windowWidth > 800)
                return 800
            else if(this.windowWidth < 800 && this.windowWidth > 500)
                return this.windowWidth - 30
            else
                return this.windowWidth
        },
        ...mapState({
            isMobile: state => state.isMobile,
            project: state => state.projects.workgroupData,
            user: state => state.user.user
        }),
        showDelete() {
            return this.form.organization && this.isEdit
        }
    },
    methods: {
        getPopupContainer() {
            return this.$refs.contentWrapper
        },
        isEmployeeEditDisabled(item) {
            return this.disabledRoles.has(item.role) || (item.role === 'ORG-COORDINATOR' && item.employee === this.user.id)
        },
        isEmployeeOptionDisabled(employee) {
            return employee.id === this.user.id
        },
        isEmployeeRoleEditDisabled(item) {
            return !this.isEdit || item.employee === this.user.id
        },
        isRoleOptionDisabled(role) {
            return this.disabledRoles.has(role)
        },
        isDeleteDisabled(item) {
            return this.disabledRoles.has(item.role) || this.form.employees.length <= 1 || (item.role === 'ORG-COORDINATOR' && item.employee === this.user.id)
        },
        async search() {
            this.loading = true
            try {
                const { data } = await this.$http.get('/catalogs/contractors/to_add/', {params: {
                    search: this.searchText
                }})
                this.organizations = data || []
            } catch(e) {
                console.log(e)
                this.$message.error('Не удалось получить список организаций')
                this.handleError(e)
            } finally {
                this.loading = false
            }
        },
        async getOrgRoles() {
            this.loading = true
            const params = {
                projectAdd: true
            }
            try {
                const { data } = await this.$http.get('/catalogs/contractor_relation_types/', {
                    params: params
                })
                this.orgRoles = data.results || []
            } catch(e) {
                console.log(e)
                this.$message.error('Не удалось получить типы отношений')
                this.handleError(e)
            } finally {
                this.loading = false
            }
        },
        async getEmployees(organizationID=undefined, heads) {
            if (!organizationID) return
            this.loading = true
            const params = heads ? {heads: true} : {}
            try {
                const { data } = await this.$http.get(`/catalogs/contractors/${organizationID}/employees/`, {
                    params: params
                })
                this.orgEmployees = data || []
            } catch(e) {
                console.log(e)
                this.$message.error('Не удалось получить список сотрудников')
                this.handleError(e)
            } finally {
                this.loading = false
            }
        },
        async getMembershipRoles(all=false) {
            this.loading = true
            const params = all ? {all: true} : {}
            try {
                const { data } = await this.$http.get('/work_groups/workgroups_membership_role/', {
                    params: params
                })
                this.membershipRoles = data || []
            } catch(e) {
                console.log(e)
                this.$message.error('Не удалось получить роли участников')
            } finally {
                this.loading = false
            }
        },
        selectOrganization(memberOrg, heads, all) {
            Promise.all([this.getEmployees(memberOrg.organization.id, heads), this.getMembershipRoles(all), this.getOrgRoles()])
                .then(() => {
                    if (!this.orgEmployees.length) throw new Error('Список сотрудников пуст')
                    const el = this.$refs.orgSelect
                    if (el) {
                        el.classList.remove('appearance-anim')
                        el.classList.add('disappearance-anim')
                        setTimeout(() => {
                            if (this.isEdit) {
                                const { employees, organization, role } = memberOrg
                                this.form.role = role
                                this.form.employees = employees.map(item => ({
                                    employee: item.member.id,
                                    role: item.membership_role.code
                                }))
                                this.form.organization = organization
                            } else {
                                this.form.employees = [{
                                    employee: this.orgEmployees[0].id,
                                    role: 'ORG-COORDINATOR'
                                }]
                                this.form.organization = memberOrg.organization
                            }
                        }, 100)
                    }
                })
                .catch((e) => {
                    console.log(e)
                    this.$message.error('Ошибка при выборе организации')
                })
        },
        cancel() {
            const el = this.$refs.selectedOrg
            if (el) {
                el.classList.remove('appearance-anim')
                el.classList.add('disappearance-anim')
                setTimeout(() => {
                    this.orgEmployees = []
                    this.resetForm()
                    if (this.isEdit) this.onAddOrgDrawerClose()
                }, 100)

            }
        },
        resetForm() {
            this.form = {
                organization: null,
                role: undefined,
                employees: [{
                    employee: undefined,
                    role: undefined
                },]
            }
        },
        afterVisibleChange(vis) {
            if(!vis) {
                this.searchText = ''
                this.organizations = []
                this.orgRoles = []
                this.orgEmployees = []
                this.membershipRoles = []
                this.resetForm()
            }
        },
        addEmployee() {
            this.form.employees.push({
                employee: undefined,
                role: undefined
            })
        },
        deleteEmployee(item, index) {
            if (this.form.employees.length <= 1) return
            this.$delete(this.form.employees, index)
        },
        getPayload() {
            let payload = JSON.parse(JSON.stringify(this.form))

            if (payload.organization?.id)
                payload.organization = payload.organization.id

            return payload
        },
        addOrgInProject() {
            this.$refs.addOrgForm.validate(async (valid, errors) => {
                if (valid) {
                    const payload = this.getPayload()
                    this.loading = true
                    try {
                        if (this.isEdit) {
                            const { data } = await this.$http.put(`/work_groups/workgroups/${this.project.id}/add/organization/`, payload)
                            this.$emit('updateOrganization', data)
                            this.$message.success('Данные обновлены')
                        } else {
                            const { data } = await this.$http.post(`/work_groups/workgroups/${this.project.id}/add/organization/`, payload)
                            this.$emit('addToOrganizations', data)
                            this.$message.success('Организация добавлена в проект')
                        }
                        eventBus.$emit('update_members_list')
                        this.onAddOrgDrawerClose()
                    } catch(error) {
                        errorHandler({error})
                    } finally {
                        this.loading = false
                    }
                } else {
                    this.$message.error('Заполните обязательные поля')
                    console.log('ERRORS', errors)
                }
            })
        },
        showDeleteConfirm() {
            this.$confirm({
                title: 'Исключить организацию из проекта?',
                okText: 'Исключить',
                okType: 'danger',
                zIndex: 1200,
                cancelText: 'Отмена',
                onOk: () => {
                    this.removeOrgFromProject()
                },
                onCancel() {},
            })
        },
        async removeOrgFromProject() {
            const payload = {
                organization: this.form.organization.id
            }
            this.loading = true
            try {
                await this.$http.post(`/work_groups/workgroups/${this.project.id}/remove/organization/`, payload)
                this.$message.success('Организация исключена из проекта')
                this.$emit('removeFromOrganizations', this.form.organization)
                eventBus.$emit('update_members_list')
                this.onAddOrgDrawerClose()
            } catch(e) {
                errorHandler({error})
            } finally {
                this.loading = false
            }
        },
        handleError(e) {
            if (e instanceof Object && e !== null) {
                Object.keys(e).forEach((key) => {
                    if (Array.isArray(e[key])) {
                        e[key].forEach(message => this.$message.error(`${message} (${key})`))
                    } else if(typeof e[key] === 'string') {
                        this.$message.error(`${key} - ${e[key]}`)
                    }
                })
            }
        }
    }
}
</script>
<style lang="scss" scoped>
.spinner.ant-spin-nested-loading {
    height: 100%;
    &::v-deep {
        .ant-spin-container {
            height: 100%;
        }
    }
}
.content {
    padding: 0px 15px;
    font-weight: 400;
    font-size: 14px;
    color: rgba(0, 0, 0, 1);
    height: 100%;
    .label {
        line-height: 100%;
        opacity: 0.6;
    }
    .form {
        gap: 10px;
        margin-top: 10px;
        @media (min-width: 768px) {
            display: flex;
        }
        .field {
            flex: 1;
        }
        .button {
            @media (max-width: 767.98px) {
                margin-top: 10px;
            }
            @media (min-width: 768px) {
                width: 192px;
            }
        }
    }
    .org-select {
        display: flex;
        flex-direction: column;
        overflow: hidden;
        height: 100%;
        .info {
            line-height: 140%;
        }
        .search {
            margin-top: 20px;
        }
        .org-list {
            margin-top: 20px;
            display: flex;
            flex-direction: column;
            gap: 15px;
            overflow-y: auto;
        }
    }
    .selected-org {
        height: 100%;
        display: flex;
        flex-direction: column;
        gap: 20px;
        .employees {
            flex: 1;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            .list {
                display: flex;
                flex-direction: column;
                gap: 10px;
                margin-top: 10px;
                overflow: auto;
                .item {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    grid-template-rows: auto;
                    column-gap: 10px;
                }
                .item--with-delete-button {
                    grid-template-columns: repeat(2, 1fr) auto;
                }
                .delete-button {
                    align-self: center;
                    &::v-deep{
                        .ant-btn{
                            border: 0px;
                            box-shadow: initial;
                        }
                    }
                }
            }
            .add-employee {
                cursor: pointer;
                padding: 10px 0;
                font-family: Roboto;
                font-weight: 400;
                font-size: 14px;
                line-height: 100%;
                color: rgba(29, 101, 192, 1);
            }
        }
        .buttons {
            margin-top: auto;
            display: flex;
            justify-content: space-between;
            .save-cancel {
                display: flex;
                gap: 16px;
            }
            .delete {
                .ant-btn {
                    border-color: rgba(245, 34, 45, 1);
                }
                .member-org-delete-button {
                    color: var(--red);
                }

            }
        }
    }
    &::v-deep{
        .ant-form-item {
            margin-bottom: 0;
        }
        .ant-form-explain{
            display: none;
        }
    }

}
.ant-form {
    height: 100%;
}
@keyframes disappearance {
  from {
    opacity: 1;
  }
  to {
    opacity: 0;
  }
}
.disappearance-anim {
  animation-name: disappearance;
  animation-duration: 0.1s;
}
@keyframes appearance {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
.appearance-anim {
  animation-name: appearance;
  animation-duration: 0.1s;
}
</style>
<style lang="scss">
.add-org-drawer {
    .ant-drawer-body {
        height: calc(100% - 40px);
    }
}
</style>