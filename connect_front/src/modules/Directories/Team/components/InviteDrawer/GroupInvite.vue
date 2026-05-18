<template>
    <a-form-model
        ref="inviteForm"
        :key="form.list.length"
        :model="form">
        <div 
            v-for="(item, index) in form.list" 
            :key="item.key" 
            class="md:grid grid-cols-2 gap-3 mb-4 md:mb-0">
            <a-form-model-item
                :label="$t('team.email')"
                class="mb-2"
                :prop="'list.' + index + '.email'"
                :rules="rules">
                <a-input
                    v-model="item.email"
                    size="large"
                    type="email" />
            </a-form-model-item>
            <a-form-model-item
                :label="$t('team.team')"
                class="mb-2"
                :prop="'list.' + index + '.workgroup'">
                <div class="flex items-center">
                    <div 
                        class="ant-input ant-input-lg flex items-center cursor-pointer truncate" 
                        @click="openGroupDrawer(index)">
                        <template v-if="item.workgroup">
                            <div class="mr-1">
                                <a-avatar 
                                    :key="item.workgroup.id"
                                    icon="team" 
                                    :src="workgroupLogoPath(item)" 
                                    :size="22" />
                            </div>
                            <div class="truncate">
                                {{ item.workgroup.name }}
                            </div>
                        </template>
                    </div>
                    <a-button 
                        v-if="form.list.length > 1" 
                        type="ui"
                        ghost
                        icon="minus" 
                        size="large" 
                        class="ml-1" 
                        @click="deleteEmail(index)" />
                </div>
            </a-form-model-item>
        </div>
        <a-button 
            icon="plus" 
            type="link" 
            class="p-0"
            @click="addEmail">
            {{ $t('team.add_email') }}
        </a-button>

        <GroupDrawer 
            ref="groupDrawer" 
            :selectProject="selectProject" />
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
            index: null,
        }
    },
    computed: {
        rules() {
            return [
                { 
                    message: this.$t('team.email_filled_incorrectly'), 
                    type: 'email', 
                    trigger: 'blur'
                },
                { 
                    required: !(this.form.massive), 
                    message: this.$t('team.required_field'), 
                    type: 'email', 
                    trigger: 'blur'
                }
            ]
        }
    },
    methods: {
        openGroupDrawer(index) {
            this.index = index
            this.$nextTick(() => {
                this.$refs['groupDrawer'].open()
            })
        },
        selectProject(val) {
            this.form.list[this.index].workgroup = val
        },
        resetData() {
            this.index = null
            // this.form = {
            //     list: [
            //         {
            //             key: Date.now(),
            //             email: '',
            //             workgroup: null
            //         }
            //     ]
            // }
        },
        deleteEmail(index) {
            this.form.list.splice(index, 1)
        },
        addEmail() {
            this.form.list.push({
                key: Date.now(),
                email: '',
                workgroup: null
            })
        },
        workgroupLogoPath(workgroup) {
            return workgroup?.workgroup_logo?.path || ''
        }
    }
}
</script>