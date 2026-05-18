<template>
    <div>
        <!-- <template v-if="actions && actions.add_member">
            <div class="flex mb-2">
                <InviteButton
                    :useSubmitHandler="commitPartisipants"
                    :useChangeMetadata="changeMetadata"
                    useInject
                    :injectMetadata="form.metadata"
                    :requestData="{id}"
                    v-model="form.partisipants" />
            </div>
        </template>    -->
        <div ref="tableWrapperRef" class="flex-grow min-h-0">
            <a-table
                :columns="visibleColumns" 
                :data-source="tableData" 
                :row-key="record => record.id || record.key"
                bordered 
                size="small"
                :scroll="scroll"
                :loading="loading"
                :pagination="false"
                :locale="{
                    emptyText: $t('no_data')
                }">
                <template slot="member" slot-scope="text, record">
                    <Profiler
                        nameClass="text-sm"
                        initStatus
                        showCurrentContractor
                        :popoverText="record.membership_role.code === 'FOUNDER' ? $t('project.director') : '' || record.membership_role.code === 'MODERATOR' ? $t('project.moderator') : ''"
                        :subtitle="{ text: record.membership_role.name, class: 'text-xs' }"
                        :user="record.member" />
                </template>
                <template slot="last_activity" slot-scope="text, record">
                    {{ record.member.last_activity ? $moment(record.member.last_activity).format('DD.MM.YYYY HH:mm') : '-' }}
                </template>
                <template slot="actions" slot-scope="text, record">
                    <div class="flex items-center">
                        <a-tooltip
                            v-if="actions?.set_default_visors" 
                            destroyTooltipOnHide
                            :title="getSetDefaultVisorTitle(record)"
                            placement="bottom">
                            <div class="cursor-pointer">
                                <a-button
                                    @click="setDefaultVisor(record, !record.default_visor)"
                                    shape="circle"
                                    :loading="setDefaultVisorLoading[record.id]"
                                    type="ui"
                                    ghost
                                    flaticon
                                    :icon="getSetDefaultVisorIcon(record)">
                                </a-button>
                            </div>
                        </a-tooltip>
                        <template v-if="actions && actions.add_member" >
                            <a-tooltip
                                :title="$t('project.remove_partisipant')"
                                destroyTooltipOnHide
                                placement="left"
                                v-if="isFounder && record.membership_role.code !== 'FOUNDER'">
                                <a-button
                                    class="cursor-pointer text_red"
                                    :loading="deleteLoading[record.id] ? deleteLoading[record.id] : false"
                                    @click="deleteStudent(record)"
                                    shape="circle"
                                    ghost
                                    type="ui"
                                    flaticon
                                    icon="fi-rr-remove-user">
                                </a-button>
                            </a-tooltip>
                            <a-tooltip
                                :title="getChangeModeratorTitle(record)"
                                destroyTooltipOnHide
                                placement="bottom"
                                v-if="canSetModerator(record)">
                                <a-button
                                    @click="toModerator(record)"
                                    shape="circle"
                                    :loading="moderatorLoading[record.id]"
                                    type="ui"
                                    ghost
                                    flaticon
                                    :icon="isModerator(record) ? 'fi-rr-arrow-circle-down' : 'fi-rr-arrow-circle-up'">
                                </a-button>
                            </a-tooltip>
                        </template>
                    </div>
                </template>
            </a-table>
        </div>
        <div class="flex">
            <a-pagination
                class="mt-4 ml-auto pager_wrapper"
                :current="page"
                :page-size.sync="pageSize"
                :defaultPageSize="Number(pageSize)"
                :total="count"
                show-less-items
                showSizeChanger
                @showSizeChange="showSizeChange"
                :pageSizeOptions="pageSizeOptions"
                @change="changePage">
                <template slot="buildOptionText" slot-scope="props">
                    {{ props.value }}
                </template>
            </a-pagination>
        </div>

    </div>
</template>

<script>
//import UserDrawer from '@apps/DrawerSelect/index.vue'
import eventBus from "@/utils/eventBus"
import Vue from 'vue'
import { mapActions } from 'vuex'
import { errorHandler } from '@/utils/index.js'
// import InviteButton from './InviteButton.vue'
export default {
    components: {
        // InviteButton
    },
    props: {
        getRoles: {
            type: Function,
            required: true
        },
        id: {
            type: String,
            default: ''
        },
        actions: {
            type: Object,
            default: () => null
        },
        isFounder: {
            type: Boolean,
            required: true
        },
        updatePartisipants: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
            pageSize: 15,
            page: 1,
            pageSizeOptions: ['15', '30', '50'],
            form: {
                partisipants: [],
                metadata: {
                    partisipants: []
                }
            },
            deleteLoading: {},
            moderatorLoading: {},
            setDefaultVisorLoading: {},
            tableHeight: 300,

            loading: false,
            tableKey: `project_members_${this.id}`,
            defaultColumns: [
                {
                    title: "Сотрудник",
                    dataIndex: 'member.full_name',
                    key: "full_name",
                    width: 260,
                    scopedSlots: { customRender: 'member' }
                    
                },
                {
                    title: "Email",
                    dataIndex: 'member.email',
                    key: "email",
                    width: 260,                    
                },
                {
                    title: "Активность",
                    dataIndex: 'member.last_activity',
                    key: "last_activity",
                    width: 160,
                    scopedSlots: { customRender: 'last_activity' }     
                },
                {
                    title: "",
                    dataIndex: 'member.id',
                    key: "actions",
                    width: 140,
                    scopedSlots: { customRender: 'actions' }     
                },
            ],
        }
    },
    computed: {
        scroll() {
            const totalWidth = this.visibleColumns.reduce((acc, curr) => acc + curr.width, 0)
            return {
                x: totalWidth,
                y: this.tableHeight
            }
        },
        visibleColumns() {
            return this.columns.filter(column => !column.hiddable || column.visible)
        },
        tableData() {
            return this.$store.state.projects.tables?.[this.tableKey]?.results
        },
        count() {
            return this.$store.state.projects.tables?.[this.tableKey]?.count || 0
        },

    },

    created() {
        this.initColumns()
        this.getData()
    },

    mounted() {
        this.setTableHeight();
        window.addEventListener('resize', this.setTableHeight);

        // eventBus.$on(`update_filter_${this.pageModel}`, () => {
        //     this.page = 1
        //     this.getData()
        // })
    },
    beforeDestroy() {
        window.removeEventListener('resize', this.setTableHeight);
    },
    methods: {        
        ...mapActions({
            deleteStudentS: "projects/deleteStudent",
            toModeratorS: "projects/toModerator",
        }),
        getChangeModeratorTitle(record) {
            return this.isModerator(record) ? this.$t('project.unset_moderator') : this.$t('project.change_moderator')
        },
        canSetModerator(record) {
            return this.isFounder && record.membership_role.code !== 'FOUNDER'
        },
        isModerator(record) {
            return record.membership_role.code === 'MODERATOR'
        },
        canUnsetModerator() {
            return this.isFounder
        },
        getSetDefaultVisorTitle(record) {
            return record.default_visor ? 
                this.$t('project.unset_as_default_visor') : 
                this.$t('project.set_as_default_visor')
        },
        getSetDefaultVisorIcon(record) {
            return record.default_visor ? 'fi-rr-eye-crossed' : 'fi-rr-eye'
        },
        setDefaultVisor(record, setDefaultVisor) {
            const url = `work_groups/workgroups/${this.id}/set_default_visor/`
            const payload = { 
                member: record.id,
            	default_visor: setDefaultVisor
            }
            this.$set(this.setDefaultVisorLoading, record.id, true)
            this.$http.put(url, payload)
                .then((data) => {
                    this.getData()

                })
                .catch(error => {
                    errorHandler({error})
                })
                .finally(() => {
                    this.$delete(this.setDefaultVisorLoading, record.id)
                })
        },
        async toModerator(record) {
            try{
                this.$set(this.moderatorLoading, record.id, true)
                await this.toModeratorS({id: this.id, data: 
                {
                    membership_id: record.id,
                    id: record.member.user_id,
                    unset: this.isModerator(record)
                }})

                if (this.isModerator(record)) {
                    this.$message.info(this.$t('project.member_unset_as_moderator'))
                } else {
                    this.$message.info(this.$t('project.member_set_as_moderator'))
                }
                
                await this.changePage(1)
            }
            catch(error){
                errorHandler({error})
            } finally {
                this.$delete(this.moderatorLoading, record.id)
            }
        },
        deleteStudent(item) {
            this.$confirm({
                title: this.$t('wgr.user_remove_message', { user: item.member.full_name }),
                okText: this.$t('remove'),
                cancelText: this.$t('cancel'),
                onOk: async () => {
                    try{
                        this.$set(this.deleteLoading, item.id, true)
                        await this.deleteStudentS({id: this.id, data: {membership_id: item.id}})
                        this.$message.success(this.$t('wgr.member_delete'))
                        this.changePage(1)
                    }
                    catch(error){
                        errorHandler({error})
                    } finally {
                        this.$delete(this.deleteLoading, item.id)
                    }
                }
            })
        },
        setTableHeight() {
            this.$nextTick(() => {
                const wrapper = this.$refs.tableWrapperRef;
                if (wrapper) {
                    this.tableHeight = wrapper.clientHeight - 50; // минус примерный размер заголовков
                }
            });
        },
        commitPartisipants() {
            if(this.form.partisipants.length === 0)
                return 0

            const prifileIds = this.form.partisipants.map(user => user.id)
            const payload = { profile_id: prifileIds }
            this.$http.post(`/work_groups/workgroups/${this.id}/send_invitations/`, payload)
                .then(() => {
                    this.$message.success(this.$t('project.successful'))
                    this.saveMetadata()
                    this.changePage(1)
                })
                .catch(error => {
                    errorHandler({error})
                })
        },
        changeMetadata({key, value}) {
            Vue.set(this.form.metadata, key, value)
        },
        async saveMetadata() {
            try {
                await this.$http.patch(`/work_groups/workgroups/${this.id}/`, {
                    metadata: this.form.metadata
                })
            } catch(error) {
                errorHandler({error})
            }
        },
        getData() {
            const params = {
                page: this.page,
                page_size: this.pageSize,
                page_name: this.pageName
            }
            const actionPayload = { 
                endpoint: `work_groups/workgroups/${this.id}/get_workgroups_members/`, 
                params, 
                tableKey: this.tableKey, 
            }
            this.loading = true

            this.$store.dispatch('projects/setTable', actionPayload)
                .then(() => {
                    this.updatePartisipants(this.count)
                    this.getRoles()
                })
                .catch(error => {
                    this.$message.error(this.$t('Error receiving table data'))
                    console.error(error)
                })
                .finally(() => {
                    this.loading = false
                })
        },
        showSizeChange(current, size) {
            this.pageSize = size
            this.changePage(1)
        },
        changePage(newPage) {
            this.page = newPage
            this.getData()

        },

        initColumns() {
            const localTableConfigs = JSON.parse(localStorage.getItem('table_configs')) 
            const columns = localTableConfigs?.projectMembers || JSON.parse(JSON.stringify(this.defaultColumns))
            this.changeColumns(columns)
        },
        changeColumns(selectedColumns) {
            this.columns = JSON.parse(JSON.stringify(selectedColumns))
            this.columns.forEach(column => column.customRender = this.renderContent)
        },


    }
    
}
</script>