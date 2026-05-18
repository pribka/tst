<template>
    <a-form-model
        ref="inviteForm"
        :model="form"
        :rules="rules">
        <a-form-model-item
            ref="massive"
            :label="$t('team.enter_emails_separated')"
            prop="massive"
            class="textarea_wrapper">
            <a-textarea
                v-model="form.massive"
                :auto-size="{ minRows: 5, maxRows: 30 }"/>
            <div class="footer_action flex items-center">
                <a-button type="link" size="small" @click="openGroupDrawer()">
                    <div v-if="selectedGroup" class="group_name flex items-center">
                        <span class="mr-1">{{ $t('team.team') }}:</span>
                        <div class="mr-1">
                            <a-avatar 
                                :key="selectedGroup.id"
                                icon="team" 
                                :src="workgroupLogoPath" 
                                :size="18" />
                        </div>
                        <div class="truncate">{{ selectedGroup.name }}</div>
                    </div>
                    <div v-else class="flex items-center">
                        <i class="fi fi-rr-user-add mr-1"></i>
                        {{ $t('team.invite_to_team') }}
                    </div>
                </a-button>
                <a-button v-if="selectedGroup" type="link" size="small" class="text_current ant-btn-icon-only flex items-center justify-center" @click="clearGroup()">
                    <i class="fi fi-rr-cross-small"></i>
                </a-button>
            </div>
            <div 
                v-if="error" 
                class="text_error leading-none">
                {{ $t('team.email_entered_incorrectly') }}
            </div>
        </a-form-model-item>
        <GroupDrawer ref="groupDrawer" :selectProject="selectProject" />
    </a-form-model>
</template>

<script>
export default {
    components: {
        GroupDrawer: () => import('./GroupDrawer.vue')
    },
    props: {
        form: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            error: false,
            selectedGroup: null,
            
        }
    },
    computed: {
        workgroupLogoPath() {
            return this.selectedGroup?.workgroup_logo?.path || ''
        },
        rules() {
            return {
                massive:[
                    {                    
                        required: !(this.form.list?.[0]?.email),
                        message: this.$t('team.required_field'),
                        trigger: 'blur'
                    }
                ]
            }
        }
    },
    methods: {
        resetData() {
            this.selectedGroup = null
            this.error = false
        },
        clearGroup() {
            this.form.workgroup = null
            this.selectedGroup = null
        },
        openGroupDrawer() {
            this.$nextTick(() => {
                this.$refs['groupDrawer'].open()
            })
        },
        selectProject(val) {
            this.form.workgroup = val.id
            this.selectedGroup = val
        },
        setError(value) {
            this.error = value
        }
    }
}
</script>

<style lang="scss" scoped>
.text_error {
    color: var(--errorRed);
    transition:  0.3s cubic-bezier(0.215, 0.61, 0.355, 1);
}
.textarea_wrapper{
    position: relative;
    .group_name{
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        max-width: 400px;
    }
    .footer_action{
        position: absolute;
        bottom: 0;
        left: 5px;
        z-index: 5;
    }
    .ant-input{
        padding-bottom: 30px;
    }
}
</style>