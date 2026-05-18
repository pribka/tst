<template>
    <div>
        <div    
            class="user-list__item"
            v-for="record in memberList" :key="record.id">
            <Profiler
                nameClass="text-sm"
                initStatus
                :popoverText="record.membership_role.code === 'FOUNDER' ? $t('project.director') : '' || record.membership_role.code === 'MODERATOR' ? $t('project.moderator') : ''"
                :subtitle="{ text: record.membership_role.name, class: 'text-xs' }"
                :user="record.member" />

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


        </div>
        <infinite-loading
            @infinite="getData"
            :identifier="infinityId"
            v-bind:distance="10">
            <div slot="spinner"><a-spin /></div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>

    </div>
</template>

<script>
// import UserDrawer from '@apps/DrawerSelect/index.vue'
import InfiniteLoading from 'vue-infinite-loading'
import eventBus from "@/utils/eventBus"
import { mapActions } from 'vuex'
import { errorHandler } from '@/utils/index.js'
export default {
    components: {
        // UserDrawer,
        InfiniteLoading
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
            memberList: [],
            pageSize: 5,
            page: 1,
            infinityId: new Date(),
            form: {
                partisipants: [],
                metadata: {
                    partisipants: []
                }
            },
            deleteLoading: {},
            moderatorLoading: {},
            setDefaultVisorLoading: {},

            loading: false,
        }
    },
    computed: {
        pageName() {
            return `members_${this.id}`
        },
    },
    methods: {        
        ...mapActions({
            deleteStudentS: "projects/deleteStudent",
            toModeratorS: "projects/toModerator",
        }),
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
                    this.reload()

                })
                .catch(error => {
                    errorHandler({error})
                })
                .finally(() => {
                    this.$delete(this.setDefaultVisorLoading, record.id)
                })
        },
        getSetDefaultVisorTitle(record) {
            return record.default_visor ? 
                this.$t('project.unset_as_default_visor') : 
                this.$t('project.set_as_default_visor')
        },

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
                this.reload()
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
                        this.reload()
                        this.$message.success(this.$t('wgr.member_delete'))
                    }
                    catch(error){
                        errorHandler({error})
                    } finally {
                        this.$delete(this.deleteLoading, item.id)
                    }
                }
            })
        },
        reload() {
            this.page = 1
            this.memberList.splice(0)
            this.infinityId = new Date()
        },
        getData($state) {
            const params = {
                page: this.page,
                page_size: this.pageSize,
                page_name: this.pageName
            }
            const url = `work_groups/workgroups/${this.id}/get_workgroups_members/`

            this.getRoles()
            this.$http(url, { params })
                .then(({ data }) => {
                    this.memberList.push(...data.results)
                    if (data?.next) {
                        this.page++
                        $state.loaded();
                    } else {
                        $state.complete();
                    }
                })
        },
    },
    mounted() {
        eventBus.$on(`update_member_list_${this.id}`, () => {
            this.reload()
        })
    },
    beforeDestroy() {
        eventBus.$off(`update_member_list_${this.id}`)
    },
}
</script>

<style lang="scss" scoped>
.user-list__item {
    display: flex;
    padding: 10px 0;
    justify-content: space-between;
    align-items: center;
}
.user-list__item + .user-list__item {
    border-top: 1px solid #e5e5e5;
}
</style>