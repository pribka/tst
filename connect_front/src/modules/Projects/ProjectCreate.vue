<template>
    <DrawerTemplate
        v-model="drawerVisible"
        :width="drawerWidth"
        destroyOnClose
        @afterVisibleChange="afterVisibleChange"
        @close="closeDrawer">
        <template #title>
            <div class="drawer_title">
                {{ drawerTitle }}
            </div>
        </template>
        <template #rightHeader>
            <HelpButton partCode="projects" />
        </template>
        <a-form-model ref="form" :model="form" :rules="rules">
            <div class="form_block">
                <div class="form_block__header">
                    <h3>{{ $t("project.avatar_project") }}</h3>
                </div>
                <div class="flex items-center">
                    <Upload
                        objectType
                        croper
                        class="min-w-0"
                        v-model="form.workgroup_logo">
                        <template v-slot:button>
                            <div class="flex items-center">
                                <a-avatar
                                    class="shrink-0"
                                    :size="60"
                                    :src="
                                        form.workgroup_logo && form.workgroup_logo.path
                                            ? form.workgroup_logo.path
                                            : null
                                    "
                                    :key="
                                        form.workgroup_logo && form.workgroup_logo.path
                                            ? form.workgroup_logo.path
                                            : null
                                    "
                                    flaticon
                                    icon="fi-rr-users-alt"/>
                                <div
                                    type="button"
                                    class="ml-6 min-w-0 ant-btn ant-btn-primary ant-btn-lg ant-btn-background-ghost flex items-center">
                                    <i class="flaticon fi fi-rr-cloud-upload-alt"></i>
                                    <span class="truncate">{{ $t("project.logo_upload") }}</span>
                                </div>
                            </div>
                        </template>
                    </Upload>
                </div>
            </div>
            <div class="form_block">
                <div class="form_block__header">
                    <h3>{{ $t("Basic information about a project") }}</h3>
                </div>
                <div class="grid md:gap-4 grid-cols-1 md:grid-cols-2">
                    <a-form-model-item :label="$t('project.title_project')" prop="name">
                        <a-input
                            v-model="form.name"
                            size="large"
                            :placeholder="$t('project.title_project')"/>
                    </a-form-model-item>
                    <a-form-model-item :label="$t('Organization')" prop="organization">
                        <DSelect
                            v-model="form.organization"
                            size="large"
                            apiUrl="/contractor_permissions/organizations/"
                            class="w-full"
                            oneSelect
                            :listObject="false"
                            labelKey="name"
                            :params="{ permission_type: 'create_workgroup' }"
                            :placeholder="$t('sports.selectFromList')"
                            :default-active-first-option="false"
                            :filter-option="false"
                            :not-found-content="null"/>
                    </a-form-model-item>
                    <a-form-model-item
                        v-if="!edit"
                        :label="$t('project.project_founder')"
                        ref="founder"
                        prop="founder">
                        <UserDrawer
                            :id="`${defaultUserSelectId}_founder`"
                            v-model="form.founder"
                            class="w-full"
                            :title="$t('project.project_founder')" />
                    </a-form-model-item>

                    <!--<a-form-model-item
                        ref="locationRegion"
                        :label="$t('sports.region')"
                        prop="locationRegion">
                        <DSelect
                            v-model="form.locationRegion"
                            size="large"
                            apiUrl="/accounting_catalogs/locations/"
                            class="w-full"
                            :listObject="false"
                            :params="{ parent: 'root' }"
                            :placeholder="$t('sports.selectFromList')"
                            :default-active-first-option="false"
                            :filter-option="false"
                            :not-found-content="null"
                            @change="changeSelect('region')"
                            @changeGetObject="changeGetObject">
                            <template v-slot:option_item="{ data }">
                                {{ data.code }} - {{ data.name }}
                            </template>
                        </DSelect>
                    </a-form-model-item>
                    <a-form-model-item
                        ref="locationDistrict"
                        :label="$t('sports.district')"
                        prop="locationDistrict">
                        <DSelect
                            v-model="form.locationDistrict"
                            size="large"
                            apiUrl="/accounting_catalogs/locations/"
                            class="w-full"
                            :key="form.locationRegion"
                            :disabled="form.locationRegion ? false : true"
                            :initList="form.locationRegion || isEdit ? true : false"
                            :listObject="false"
                            :params="{
                                parent: form.locationRegion,
                            }"
                            :placeholder="$t('sports.selectFromList')"
                            :default-active-first-option="false"
                            :filter-option="false"
                            :not-found-content="null"
                            @change="changeSelect('district')"
                            @changeGetObject="changeGetObject">
                            <template v-slot:option_item="{ data }">
                                {{ data.code }} - {{ data.name }}
                            </template>
                        </DSelect>
                    </a-form-model-item>
                    <a-form-model-item
                        ref="location_akimat"
                        :label="$t('sports.akimat')"
                        prop="location_akimat">
                        <DSelect
                            v-model="form.location_akimat"
                            size="large"
                            apiUrl="/accounting_catalogs/locations/"
                            class="w-full"
                            :key="form.locationDistrict"
                            :disabled="form.locationDistrict ? false : true"
                            :initList="form.locationDistrict || isEdit ? true : false"
                            :listObject="false"
                            :params="{ parent: form.locationDistrict }"
                            :placeholder="$t('sports.selectFromList')"
                            :default-active-first-option="false"
                            :filter-option="false"
                            :not-found-content="null"
                            @change="changeSelect('akimat')"
                            @changeGetObject="changeGetObject">
                            <template v-slot:option_item="{ data }">
                                {{ data.code }} - {{ data.name }}
                            </template>
                        </DSelect>
                    </a-form-model-item>
                    <a-form-model-item
                        ref="location_settlement"
                        :label="$t('sports.settlement')"
                        prop="location_settlement">
                        <DSelect
                            v-model="form.location_settlement"
                            size="large"
                            apiUrl="/accounting_catalogs/locations/"
                            class="w-full"
                            :key="form.location_akimat"
                            :disabled="form.location_akimat ? false : true"
                            :initList="form.location_акimat || isEdit ? true : false"
                            :listObject="false"
                            :params="{
                                parent: form.location_akimat,
                            }"
                            :placeholder="$t('sports.selectFromList')"
                            :default-active-first-option="false"
                            :filter-option="false"
                            :not-found-content="null"
                            @change="changeSelect('settlement')"
                            @changeGetObject="changeGetObject">
                            <template v-slot:option_item="{ data }">
                                {{ data.code }} - {{ data.name }}
                            </template>
                        </DSelect>
                    </a-form-model-item>
                    <a-form-model-item
                        ref="location"
                        :label="$t('sports.village')"
                        prop="location">
                        <DSelect
                            v-model="form.location"
                            size="large"
                            apiUrl="/accounting_catalogs/locations/"
                            class="w-full"
                            :key="form.location_settlement"
                            :disabled="form.location_settlement ? false : true"
                            :initList="form.location_settlement || isEdit ? true : false"
                            :listObject="false"
                            :params="{
                                parent: form.location_settlement,
                            }"
                            :placeholder="$t('sports.selectFromList')"
                            :default-active-first-option="false"
                            :filter-option="false"
                            :not-found-content="null"
                            @changeGetObject="changeGetObject">
                            <template v-slot:option_item="{ data }">
                                {{ data.code }} - {{ data.name }}
                            </template>
                        </DSelect>
                    </a-form-model-item>-->
                    <a-form-model-item
                        ref="location_point"
                        :label="$t('sports.provide_address')"
                        prop="location_point">
                        <component
                            v-if="AddressSelectAsync"
                            :is="AddressSelectAsync"
                            v-model="form.location_point"
                            ref="addressSelect" />
                    </a-form-model-item>
                    <div v-if="form.location_point" class="address_item md:col-span-2">
                        <span>
                            {{ form.location_point.address }}
                        </span>
                        <div class="flex items-center pl-2">
                            <a-button icon="fi-rr-edit" flaticon @click="editAddress()" />
                            <a-button
                                type="danger"
                                class="ml-1"
                                icon="fi-rr-trash"
                                flaticon
                                @click="form.location_point = null"/>
                        </div>
                    </div>

                    <a-form-model-item
                        class="md:col-span-2"
                        name="description"
                        prop="description"
                        :label="$t('project.description')">
                        <a-textarea
                            v-model="form.description"
                            size="large"
                            :auto-size="{ minRows: 4, maxRows: 7 }"/>
                    </a-form-model-item>
                </div>
            </div>
            <div class="form_block">
                <div class="form_block__header">
                    <h3>{{ $t("project.work_directions") }}</h3>
                </div>
                <a-form-model-item
                    prop="work_directions">
                    <WorkDirectionsSelect
                        v-model="form.work_directions"
                        inputType="default"
                        size="large"
                        :organization="form.organization" />
                </a-form-model-item>
            </div>
            <div v-if="!edit" class="form_block">
                <div class="form_block__header">
                    <h3>{{ $t('project.participants_select') }}</h3>
                </div>
                <a-form-model-item :label="$t('project.participants')" prop="members">
                    <UserDrawer
                        :id="defaultUserSelectId"
                        v-model="form.members.profile_id"
                        :metadata="{ key: 'profile_id', value: form.metadata }"
                        :changeMetadata="changeMetadata"
                        multiple
                        :buttonText="$t('project.participants')"
                        :title="$t('project.participants')"/>
                </a-form-model-item>
            </div>
            <template v-if="!edit">
                <div class="form_block">
                    <div class="form_block__header">
                        <h3>{{ $t("Project template") }}</h3>
                    </div>
                    <div class="grid gap-0 md:gap-6 grid-cols-1 md:grid-cols-2">
                        <a-checkbox v-model="form.use_template">{{
                            $t("Create a project based on a template")
                        }}</a-checkbox>
                        <a-form-model-item
                            class="md:col-span-2"
                            ref="template"
                            prop="template"
                            :label="$t('Select project template')">
                            <DSelect
                                v-model="form.template"
                                size="large"
                                apiUrl="/work_groups/templates/available_temlates/"
                                class="w-full"
                                :key="form.template"
                                :listObject="false"
                                :placeholder="$t('Select project template')"
                                :default-active-first-option="false"
                                :filter-option="false"
                                :not-found-content="null">
                                <template v-slot:option_item="{ data }">
                                    {{ data.name }}
                                </template>
                            </DSelect>
                        </a-form-model-item>
                    </div>
                </div>
            </template>

            <div class="form_block">
                <div class="form_block__header">
                    <h3>{{ $t("Project dates") }}</h3>
                </div>
                <div class="grid md:gap-4 grid-cols-1 md:grid-cols-2">
                    <a-form-model-item
                        prop="date_start_plan"
                        ref="date_start_plan"
                        :label="$t('project.date_start_plan')">
                        <a-date-picker
                            size="large"
                            class="w-full"
                            :show-time="true"
                            :showTime="{
                                defaultValue: $moment('09:00:00', 'HH:mm'),
                                format: 'HH:mm'
                            }"
                            :inputReadOnly="false" 
                            @change="changeStartDate"
                            dropdownClassName="project_start"
                            :disabled-time="disabledDateTime"
                            :disabled-date="disabledDate"
                            :getCalendarContainer="getPopupContainer"
                            format="DD.MM.YYYY HH:mm"
                            v-model="form.date_start_plan"/>
                    </a-form-model-item>
                    <a-form-model-item
                        prop="dead_line"
                        ref="dead_line"
                        :label="$t('project.deadline_project')">
                        <a-date-picker
                            size="large"
                            :disabled="fromTemplate"
                            class="w-full"
                            :getCalendarContainer="getPopupContainer"
                            :show-time="true"
                            :inputReadOnly="false" 
                            dropdownClassName="project_end"
                            :disabled-date="disabledDateFrom"
                            :showTime="{
                                defaultValue: $moment('18:00:00', 'HH:mm'),
                                format: 'HH:mm'
                            }"
                            format="DD.MM.YYYY HH:mm"
                            v-model="form.dead_line"/>
                    </a-form-model-item>
                    <a-form-model-item class="md:col-span-2" prop="control_dates">
                        <a-checkbox v-model="form.control_dates">
                            {{ $t("project.control_dates") }}
                        </a-checkbox>
                        <a-alert :message="$t('project.project_control')" type="info" />
                    </a-form-model-item>
                </div>
            </div>

            <template v-if="false">
                <div class="form_block">
                    <div class="form_block__header">
                        <h3>Рабочее время</h3>
                    </div>
                    <div class="grid gap-0 md:gap-6 grid-cols-1 md:grid-cols-2">
                        <a-form-model-item ref="funds" label="Рабочие дни" prop="funds">
                            <a-button size="large" class="mr-2" type="primary">Пн</a-button>
                            <a-button size="large" class="mr-2" type="primary">Вт</a-button>
                            <a-button size="large" class="mr-2" type="primary">Ср</a-button>
                            <a-button size="large" class="mr-2" type="primary">Чт</a-button>
                            <a-button size="large" class="mr-2">Сб</a-button>
                            <a-button size="large">Вс</a-button>
                        </a-form-model-item>

                        <a-form-model-item ref="funds" label="Рабочие часы" prop="funds">
                            <a-button size="large" class="mr-2" type="primary">9:00 - 13:00</a-button>
                            <a-button size="large" type="primary">14:00 - 18:00</a-button>
                        </a-form-model-item>
                    </div>
                </div>
            </template>

            <div class="form_block">
                <div class="form_block__header">
                    <h3>{{ $t("Planned project budget") }}</h3>
                </div>
                <a-form-model-item
                    ref="funds"
                    :label="$t('project.project_budget')"
                    prop="funds">
                    <div class="md:flex items-center">
                        <a-input-number
                            v-model="form.funds"
                            class="w-full"
                            :placeholder="$t('project.project_budget')"
                            size="large"/>
                        <DSelect
                            v-model="form.funds_currency"
                            size="large"
                            apiUrl="/app_info/filtered_select_list/"
                            class="w-full mt-2 md:mt-0 md:ml-4 currency_select"
                            oneSelect
                            firstSelected
                            defaultSelectCode="643"
                            showSearch
                            searchKey="text"
                            valueKey="code"
                            listObject="filteredSelectList"
                            :params="{ model: 'catalogs.CurrencyModel' }"
                            :default-active-first-option="false"
                            :filter-option="false"
                            :not-found-content="null"/>
                    </div>
                </a-form-model-item>
            </div>
        </a-form-model>
        <template #footer>
            <div class="flex items-center">
                <a-button
                    :loading="loadingBtn"
                    class="px-9"
                    type="primary"
                    size="large"
                    @click="createProject()">
                    {{ submitButtonText }}
                </a-button>
                <a-checkbox v-model="form.with_chat" class="ml-4">
                    {{ $t("project.with_chat") }}
                </a-checkbox>
            </div>
        </template>
    </DrawerTemplate>
</template>

<script>
import eventBus from "@/utils/eventBus"
import createdMethods from "./mixins/createdMethods"
import locale from "ant-design-vue/es/date-picker/locale/ru_RU"
import { formModel } from './utils.js'
import { mapState } from 'vuex'
import { errorHandler } from '@/utils/index.js'
export default {
    name: "NewProjectCreate",
    mixins: [createdMethods],
    components: {
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue'),
        DSelect: () => import("@apps/DrawerSelect/Select.vue"),
        Upload: () => import("@apps/Upload"),
        UserDrawer: () => import("@apps/DrawerSelect/index.vue"),
        HelpButton: () => import('@apps/Support/components/HelpButton.vue'),
        WorkDirectionsSelect: () => import('./components/WorkDirectionsSelect.vue')
    },
    props: {
        pageName: {
            type: String,
            default: "page_list_projects.WorkgroupModel",
        },
        model: {
            type: String,
            default: "workgroups.WorkgroupModel",
        }
    },
    data() {
        return {
            isEdit: false,
            dateFormat: "YYYY-MM-DD HH:mm",
            AddressSelectAsync: null,
            locale,
            drawerVisible: false,
            form: {...formModel},
            defaultUserSelectId: 'project',
            visible: false,
            loading: false,
            previewFile: null,
            edit: false,
            editProjectId: null,
            currencyList: [],
            groupTypes: [],
            sLinks: [],
            listLinks: [],
            loadingBtn: false
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user,
            formInject: state => state.projects.formInject
        }),
        fromTemplate() {
            return this.form.use_template
        },
        rules() {
            return {
                founder: [
                    {
                        required: !this.edit,
                        message: this.$t("project.field_require"),
                        trigger: "change",
                    },
                ],
                name: [
                    {
                        required: true,
                        message: this.$t("project.field_require"),
                        trigger: "blur",
                    },
                ],
                organization: [
                    {
                        required: true,
                        message: this.$t("project.field_require"),
                        trigger: "blur",
                    },
                ],
                dead_line: [
                    {
                        required: !this.fromTemplate,
                        message: this.$t("project.field_require"),
                        trigger: "change",
                    },
                ],
                date_start_plan: [
                    {
                        required: this.fromTemplate,
                        message: this.$t("project.field_require"),
                        trigger: "change",
                    },
                ],
                template: [
                    {
                        required: this.fromTemplate,
                        message: this.$t("project.field_require"),
                        trigger: "blur",
                    },
                ],
            }
        },
        submitButtonText() {
            return this.id ? this.$t("project.update") : this.$t("project.create")
        },
        id() {
            return this.editProjectId
        },
        drawerTitle() {
            return this.edit
                ? this.$t("project.update_project")
                : this.$t("project.add_project")
        },
        drawerWidth() {
            const baseWidth = 1100
            const offset = 40
            return this.windowWidth > baseWidth + offset
                ? baseWidth
                : this.windowWidth
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
    },

    mounted() {
        eventBus.$on('add_proejct_modal', this.openCreateDrawer)
        eventBus.$on('edit_project_modal', this.openEditDrawer)
    },
    beforeDestroy(){
        eventBus.$off('add_proejct_modal', this.openCreateDrawer)
        eventBus.$off('edit_project_modal', this.openEditDrawer)
    },

    methods: {
        async openCreateDrawer({ organization = null } = {}) {
            this.closeDrawer()
            this.edit = false
            this.editProjectId = null
            if (organization?.id) {
                this.form.organization = organization.id
            }
            this.initFormDefaults()
            this.openDrawer()
        },
        async openEditDrawer({ id } = {}) {
            if (!id) return

            try {
                this.closeDrawer()
                this.editProjectId = id
                await this.initUpdate()
                this.openDrawer()
            } catch (error) {
                errorHandler({ error })
            }
        },
        changeMetadata({ key, value }) {
            this.$set(this.form.metadata, key, value)
        },
        getPopupContainer(trigger) {
            return trigger.parentNode
        },
        async loadAddressSelect() {
            if (this.AddressSelectAsync) return
            const m = await import(/* webpackChunkName: "address-select", webpackPrefetch: false, webpackPreload: false */ '@apps/DrawerSelect/AddressSelect')
            this.AddressSelectAsync = m.default || m
            await this.$nextTick()
        },
        async getCurrency() {
            try {
                const { data } = await this.$http.get('/app_info/filtered_select_list/?model=catalogs.CurrencyModel', {
                    params: {
                        model: 'catalogs.CurrencyModel'
                    }
                })
                if(data?.filteredSelectList?.length) {
                    this.currencyList = data.filteredSelectList
                    if (!this.form.funds_currency) {
                        this.form.funds_currency = data.filteredSelectList[0].code
                    }
                }
            } catch(error) {
                errorHandler({error, show: false})
            }
        },
        editAddress() {
            this.$nextTick(() => {
                if(this.$refs?.addressSelect)
                    this.$refs.addressSelect.editAddress(this.form.location_point)
            })
        },
        async createProject() {
            this.$refs.form.validate(async (v) => {
                if (v) {
                    try {
                        this.loadingBtn = true
                        //await this.uploadSocLink()
                        let res

                        const form = JSON.parse(JSON.stringify(this.form))
                        form.is_project = true

                        if (form?.program?.id) form["program"] = form.program.id
                        if (form?.counterparty?.id)
                            form["counterparty"] = form.counterparty.id
                        if (form?.costing_object?.id)
                            form["costing_object"] = form.costing_object.id
                        if (form.workgroup_logo?.id)
                            form["workgroup_logo"] = form.workgroup_logo.id
                        else form["workgroup_logo"] = null
                        if (Array.isArray(form.work_directions)) {
                            form.work_directions = form.work_directions.map(item => item?.id || item)
                        }
                        if (this.edit) {
                            delete form.founder
                        } else if (form?.founder?.id) {
                            form.founder = form.founder.id
                        } else {
                            form.founder = null
                        }

                        if (this.edit && this.id) {
                            form.name_ru = form.name
                            delete form.members
                            res = await this.updateGroupS({ data: form, id: this.id })
                            this.$message.success(this.$t("project.information_edited"))
                        } else {
                            if (form.members.profile_id?.length)
                                form.members.profile_id = form.members.profile_id
                                    .map(item => item.id)
                                    .filter(id => id !== this.user.id)

                            res = await this.createGroupS(form)

                            const openProject = () => {
                                const query = {...this.$route.query}
                                if(!query.viewProject) {
                                    query.viewProject = res.id
                                    this.$router.push({ query })
                                }
                            }
                            this.$message.info(
                                this.$createElement("span", {}, [
                                `${this.$t("project.project_created")}. `,
                                this.$createElement(
                                    "span",
                                    {
                                        class: "link cursor-pointer blue_color",
                                        on: {
                                            click: () => {
                                                openProject()
                                            },
                                        },
                                    },
                                    this.$t('project.open_project')
                                ),
                                ]),
                                5
                            )
                        }

                        if(res) {
                            if(this.$refs?.form)
                                this.$refs.form.resetFields()
                            this.sLinks = []
                            eventBus.$emit("update_list_project")
                            eventBus.$emit(`update_filter_${this.model}_${this.pageName}`)
                            if (this.edit && this.id) {
                                eventBus.$emit('project_updated', res.id)
                            }
                            this.closeDrawer()
                        }
                    } catch (error) {
                        errorHandler({error})
                    } finally {
                        this.loadingBtn = false
                    }
                } else {
                    this.$message.error(this.$t("project.fill_all_fields"))
                }
            })
        },
        disabledDateFrom(current) {
            if (this.form.date_start_plan) {
                if (
                    this.$moment(this.form.date_start_plan).isSame(
                        current.format(),
                        "day"
                    )
                ) {
                    return false
                } else
                    return (
                        current &&
            current < this.$moment(this.form.date_start_plan).endOf("day")
                    )
            } else return null
        },
        disabledDateTime() {
            if (this.form.dead_line) {
                return {
                    disabledHours: () =>
                        this.range(
                            this.$moment(this.form.dead_line)
                                .subtract({ hours: 1 })
                                .format("HH"),
                            24
                        ),
                }
            } else return null
        },

        range(start, end) {
            const result = []
            for (let i = start; i < end; i++) {
                result.push(i)
            }
            return result
        },
        disabledDate(current) {
            if (this.form.dead_line)
                return (
                    current && current > this.$moment(this.form.dead_line).endOf("day")
                )
            else return null
        },

        changeStartDate(date) {
            if (
                this.form.dead_line &&
        this.$moment(this.form.dead_line).isSameOrBefore(date)
            ) {
                this.form.date_start_plan = this.$moment(date).subtract({ hours: 1 })
            }
        },
        changeGetObject(obj) {
            this.form.selectedLocation = obj
        },
        initFormDefaults() {
            if (!this.user || this.edit) return

            if (!this.form.founder?.id) {
                this.form.founder = this.user
            }
        },
        changeSelect(type) {
            switch (type) {
            case "region":
                this.form.locationDistrict = null
                this.form.location_akimat = null
                this.form.location_settlement = null
                this.form.location = null
                break
            case "district":
                this.form.location_акimat = null
                this.form.location_settlement = null
                this.form.location = null
                break
            case "akimat":
                this.form.location_settlement = null
                this.form.location = null
                break
            case "settlement":
                this.form.location = null
                break
            }
        },

        openDrawer() {
            this.drawerVisible = true
        },
        afterVisibleChange(vis) {
            if(!vis) {
                this.isEdit = false
                this.edit = false
                this.editProjectId = null
                this.$store.commit('projects/SET_FORM_INJECT', null)
            } else {
                if(this.formInject) {
                    this.form = {...this.formInject}
                    this.$store.commit('projects/SET_FORM_INJECT', null)
                }
                if (!this.edit) {
                    this.initFormDefaults()
                }
                this.getCurrency()
                if (!this.AddressSelectAsync) this.loadAddressSelect()
            }
        },
        closeDrawer() {
            this.drawerVisible = false
            this.previewFile = null
            this.groupTypes = []
            this.sLinks = []
            this.listLinks = []
            this.file = null
            this.dataUrl = null
            this.editProjectId = null
            this.form = JSON.parse(JSON.stringify(formModel))
            this.form.members.profile_id = []
            this.form.metadata.profile_id = []
        },
    },

}
</script>

<style lang="scss" scoped>
.currency_select{
    @media (min-width: 768px) {
        max-width: 100px;
    }
}
.form_block {
  padding: 15px;
  border: 1px solid var(--border2);
  border-radius: var(--borderRadius);
  margin-bottom: 20px;

  @media (min-width: 768px) {
    padding: 30px;
  }

  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20px;

    h3 {
      font-size: 18px;
      color: #000000;
      font-weight: 400;
      margin: 0px;
      @media (min-width: 768px) {
        font-size: 20px;
      }
    }

    .st {
      color: #000000;
      font-size: 18px;
      opacity: 0.3;
      padding-left: 15px;
      text-wrap: nowrap;
    }
  }

  &__attachments {
    margin-bottom: 20px;
  }
}

.address_item {
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border: 1px solid #e1e7ec;
  padding: 15px;
  border-radius: 8px;
}

::v-deep {
  .ant-form-item {
    margin-bottom: 10px;

    @media (min-width: 900px) {
      margin-bottom: 24px;
    }
  }
}
</style>
