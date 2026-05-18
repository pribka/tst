<template>
    <a-card
        v-if="partisipants.length > 0 || (actions && actions.add_member)"
        :title="!isMobile && $t('project.participants')"
        size="small"
        class="lg:mt-base"
        :class="isMobile ? 'member_card_mobile' : 'mt-6'">
        <h6 v-if="isMobile" class="font-semibold mb-1">
            {{ $t('project.participants') }}
        </h6>
        <a-button
            v-if="isMobile && isStudent"
            @click="visible = true"
            :loading="partisipantsLoading"
            type="ui"
            class="mb-4 mt-2 w-full flex items-center justify-center">
            <i class="fi fi-rr-user-add mr-2"></i>
            {{ $t("project.invite_participants") }}
        </a-button>
        <!-- FRIENDS LIST -->
        <a-spin :spinning="partisipantsLoading">
            <ul class="friend-suggesions-list" ref="project_user_card">
                <li
                    class="friend-suggestion flex items-center mb-4 justify-between"
                    v-for="(friend, index) in partisipants"
                    :key="index">
                    <!--<Profile
                        :avatar="friend.member.avatar && friend.member.avatar.path"
                        :subtitle="friend.membership_role.name"
                        :profile="friend.member"/>-->

                    <Profiler
                        nameClass="text-sm"
                        initStatus
                        :getPopupContainer="getPopupContainer"
                        :popoverText="friend.membership_role.code === 'FOUNDER' ? $t('project.director') : '' || friend.membership_role.code === 'MODERATOR' ? $t('project.moderator') : ''"
                        :subtitle="{ text: friend.membership_role.name, class: 'text-xs' }"
                        :user="friend.member" />

                    <div 
                        v-if="actions && actions.add_member" 
                        class="flex">
                        <a-tooltip
                            :title="$t('project.remove_partisipant')"
                            placement="left"
                            v-if="
                                isFounder &&
                                    friend.membership_role.code !==
                                    'FOUNDER'
                            ">
                            <a-button
                                class="ml-1 cursor-pointer block ant-btn-icon-only text_red"
                                :loading="deleteLoading[friend.id] ? deleteLoading[friend.id] : false"
                                @click="deleteStudent(friend)"
                                shape="circle"
                                ghost
                                type="ui">
                                <i class="fi fi-rr-remove-user"></i>
                            </a-button>
                        </a-tooltip>
                        <a-tooltip
                            :title="$t('project.change_moderator')"
                            placement="bottom"
                            v-if="
                                isFounder &&
                                    friend.membership_role.code !==
                                    'FOUNDER' &&
                                    friend.membership_role.code !==
                                    'MODERATOR'
                            ">
                            <div class="ml-2 cursor-pointer">
                                <a-button
                                    @click="toModerator(friend)"
                                    shape="circle"
                                    :loading="moderatorLoading[friend.id] ? moderatorLoading[friend.id] : false"
                                    type="ui"
                                    ghost
                                    class="ant-btn-icon-only">
                                    <i class="fi fi-rr-following"></i>
                                </a-button>
                            </div>
                        </a-tooltip>
                    </div>
                </li>
            </ul>
        </a-spin>

        <template v-if="actions && actions.add_member">
            <template v-if="actions && actions.add_member">
                <UserDrawer 
                    id="meetingCreate"
                    multiple
                    buttonMode
                    buttonBlock
                    :submitHandler="commitPartisipants"
                    :buttonText="$t('project.invite_participants')"
                    :changeMetadata="changeMetadata"
                    :metadata="{ key: 'partisipants', value: form.metadata }"
                    v-model="form.partisipants" />
            </template>    
        </template>
    </a-card>
</template>

<script>
import { debounce } from "lodash"
import { mapActions } from 'vuex'
import Vue from 'vue'
import eventBus from "@/utils/eventBus"

export default {
    name: "GroupsAndProjectMembers",
    props: {
        isFounder: {
            type: Boolean,
            required: true
        },
        isStudent: {
            type: Boolean,
            required: true
        },
        id: {
            type: [String, Number],
            default: null
        },
        updatePartisipants: {
            type: Function,
            default: () => {}
        },
        actions: {
            type: Object,
            default: () => null
        }
    },
    components:{
        UserDrawer: () => import('@apps/DrawerSelect/index.vue')
    },
    created() {
        if(this.id !== 0){
            this.getParts()
        }
    },
    watch: {
        id(val){
            if(val !== 0){
                this.getParts()
            }
        }
    },
    data() {
        return {
            form: {
                partisipants: [],
                metadata: {
                    partisipants: []
                }
            },
            partisipants: [],
            partisipantsLoading: false,
            inviteItems: [],
            selectedInvite: [],
            loadingInvite: false,
            fetching:false,
            modalInvite: false,
            visible: false,
            deleteLoading: {},
            moderatorLoading: {}
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        detailInfo() {
            return store.projects.getters.info
        }
    },
    mounted() {
        eventBus.$on('update_members_list', () => { this.getParts() })
    },
    beforeDestroy() {
        eventBus.$off('update_members_list')
    },
    methods: {
        ...mapActions({
            getPartisipants: "projects/getPartisipants",
            deleteStudentS: "projects/deleteStudent",
            toModeratorS: "projects/toModerator",
            postInviteS: "projects/postInvite",
            updateGroup: "projects/updateGroup",
            getInfos: "projects/getInfo",
        }),
        changeMetadata({key, value}) {
            Vue.set(this.form.metadata, key, value)
        },
        getPopupContainer() {
            return this.$refs[`project_user_card`]
        },
        drawerClose(update = false) {
            this.visible = false
            if(update)
                this.getParts()
        },
        close(update = false) {
            this.$store.commit('projects/CLEAR_USER_LIST')
            this.form.partisipants.splice(0)
            this.form.metadata.partisipants.splice(0)
            this.drawerClose(update)
        },
        commitPartisipants() {
            if(this.form.partisipants.length === 0)
                return 0

            const prifileIds = this.form.partisipants.map(user => user.id)
            const payload = { profile_id: prifileIds }
            this.$http.post(`/work_groups/workgroups/${this.id}/send_invitations/`, payload)
                .then(() => {
                    this.close(true)
                    this.$message.success(this.$t('project.successful'))
                })
                .catch(error => {
                    this.$message.error(this.$t('project.error'))
                    console.error(error)
                })
        },
        async getParts(){
            try {
                this.partisipantsLoading = true
                const data = await this.getPartisipants(this.id)
                this.partisipants = data.results
                this.updatePartisipants(this.partisipants)
            } catch(e) {
                console.log(e)
            } finally {
                this.partisipantsLoading = false
            }
        },
        // Удалить участника из группы
        async deleteStudent(item) {
            try{
                this.$set(this.deleteLoading, item.id, true)
                await this.deleteStudentS({id: this.id, data: {membership_id: item.id}})
                this.partisipants = this.partisipants.filter((el) => el.id !== item.id);
                this.updatePartisipants(this.partisipants)
                this.$message.success(this.$t('project.member_delete'))
            }
            catch(error){
                this.$message.error(this.$t('project.error') + error)
            } finally {
                this.$delete(this.deleteLoading, item.id)
            }
        },
        // Назначить модератором
        async toModerator(item) {
            try{
                this.$set(this.moderatorLoading, item.id, true)
                await this.toModeratorS({id: this.id, data: {
                    membership_id: item.id,
                    id: item.member.user_id,
                }})
                this.partisipants = await  this.getPartisipants(this.id);
                this.$message.success(this.$t('project.member_set_as_moderator'))
            }
            catch(error){
                this.$message.error(this.$t('project.error') + error)
            } finally {
                this.$delete(this.moderatorLoading, item.id)
            }
        },

        // Поиск друга
        fetchUser: debounce(async function (name) {
            try{
                if (!this.loadingInvite && name !== "" && name.length > 1) {
                    this.fetching = true;
                    const res = await this.$http(`/users/search/`, {
                        params: {
                            fullname: name,
                        },
                    });
                    this.inviteItems = res.data.results;
                }
            }
            catch(error){
                this.$message.error(this.$t('project.error') + error)
            }
            finally{
                this.fetching= false;
            }
        }, 500),

        // Отправь запрос на вступление в групппу другому человеку
        async postInvite() {
            try{
                const data = this.selectedInvite.map((item) => item.key);
                let  res = await this.postInviteS({id: this.id, data})
                //   this.partisipants.push()
                this.$message.success(this.$t('project.successful'))
                this.modalInvite = false;
                this.selectedInvite = [];
            }
            catch(error){
                this.$message.error(this.$t('project.error') + error)
            }

        }
    }
}
</script>

<style lang="scss">
.member_card_mobile {
    border-left: 0px;
    border-right: 0px;
    border-bottom: 0px;
    border-radius: 0px;
    border-top: 1px solid var(--borderColor);
    padding-top: 0.5rem;
    .ant-card-head {
        padding: 0;
        border: none;
    }
    .ant-card-body {
        padding: 0;
    }
}
</style>