<template>
    <div class="projects-wrap">
        <div class="projects-list">
            <ProjectsList
                :selectedProjectID="selectedProjectID"
                @select="onSelect" />
        </div>
        <div class="user-list">
            <template v-if="selectedProjectID">
                <ProjectsUsers
                    ref="projectUsersRef"
                    :multiple="multiple"
                    :selectedProjectID="selectedProjectID"
                    :checkSelected="checkSelected"
                    :itemSelect="itemSelect"
                    :deselectUser="deselectUser"
                    :selectedList="selectedList"
                    :singleSelected="singleSelected" />
            </template>
            <template v-else>
                <div class="empty">
                    {{ $t('select_project') }}
                </div>
            </template>
        </div>
    </div>
</template>

<script>
export default {
    name: 'Projects',
    components: {
        ProjectsList: () => import('./ProjectsList.vue'),
        ProjectsUsers: () => import('./ProjectsUsers.vue')
    },
    props: {
        multiple: {
            type: Boolean,
            default: false
        },
        model: {
            type: String,
            default: "users.ProfileModel",
        },
        pageName: {
            type: String,
            default: 'user_select',
        },
        checkSelected: {
            type: Function,
            default: () => {}
        },
        itemSelect: {
            type: Function,
            default: () => {}
        },
        deselectUser: {
            type: Function,
            default: () => {}
        },
        selectedList: {
            type: Array,
            default: () => []
        },
        singleSelected: {
            type: [String, null],
            default: null
        }
    },
    data() {
        return {
            loading: false,
            selectedProjectID: null
        }
    },
    computed: {
        isMobile() {
            return !this.$store.state.isMobile
        },
        wrapClass() {
            return this.isMobile ? 'projects-wrap-mobile' : 'projects-wrap' 
        },
        selectedUserID: {
            get() {
                return this.singleSelected
            },
            set(val) {
                const selectedUser = this.list.find(user => user.id === val)
                if (selectedUser) {
                    this.itemSelect(selectedUser)
                }
            }
        }
    },
    methods: {
        onSelect(projectID) {
            this.selectedProjectID = this.selectedProjectID === projectID ? null : projectID
            if (this.selectedProjectID)
                this.$nextTick(() => {
                    this.$refs.projectUsersRef.reload()
                })
        }
    }
}
</script>
<style lang="scss" scoped>
.projects-wrap {
    width: 100%;
    height: 100%;
    overflow: hidden;
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    grid-template-rows: 1fr;
    gap: 12px;
    .projects-list {
        width: 100%;
        height: 100%;
        min-width: 0;
        overflow: auto;
    }
    .user-list {
        width: 100%;
        height: 100%;
        min-width: 0;
        min-height: 0;
        overflow: hidden;
        .empty {
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            background-color: rgba(240, 241, 247, 1);
            border-radius: 16px;
        }
    }
}
</style>