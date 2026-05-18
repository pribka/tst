<template>
    <a-modal
        :width="577"
        @afterVisibleChange="afterVisibleChange"
        destroyOnClose
        :visible="visible"
        @cancel="visible = false">
        <template #title>
            <a-form-model
                v-if="!formLoading"
                ref="nameForm"
                :model="form"
                class="name_form"
                :rules="nameRules">
                <a-form-model-item 
                    ref="name" 
                    prop="name" 
                    class="mb-0 name_row">
                    <div class="flex items-center justify-between">
                        <a-input 
                            v-model="form.name"
                            ref="nameInput"
                            inputType="ghost"
                            :placeholder="$t('wgr.title_group')" 
                            size="large"
                            @pressEnter="onSubmit()" />
                        <HelpButton partCode="groups" class="ml-2" />
                    </div>
                </a-form-model-item>
            </a-form-model> 
            <a-skeleton v-else active :paragraph="{rows: 5}" />
        </template>
        <a-form-model
            v-if="!formLoading"
            ref="ruleForm"
            :model="form"
            :label-col="{ span: 6, style: { textAlign: 'left' } }"
            :wrapper-col="{ span: 18 }"
            class="mini_form"
            :rules="rules">
            <a-form-model-item :wrapper-col="{ span: 24 }" ref="description" prop="description">
                <a-textarea
                    v-model="form.description"
                    :placeholder="$t('wgr.description')"
                    inputType="ghost"
                    :auto-size="{ minRows: 1, maxRows: 10 }" />
            </a-form-model-item>
            <a-form-model-item class="flex items-center" :label="$t('Organization')" ref="organization" prop="organization">
                <DSelect
                    v-model="form.organization"
                    apiUrl="/contractor_permissions/organizations/"
                    class="w-full h-6"
                    oneSelect
                    size="default"
                    inputType="ghost"
                    :params="{ permission_type: 'create_workgroup' }"
                    showPlaceholder
                    labelKey="name"
                    :placeholder="$t('Organization')"
                    :listObject="false"
                    :default-active-first-option="false"
                    :filter-option="false"
                    :not-found-content="null" />
            </a-form-model-item>
            <div class="modal_divider"></div>
            <div class="flex items-center gap-2 flex-wrap">
                <Upload
                    objectType
                    croper
                    class="min-w-0"
                    v-model="form.workgroup_logo">
                    <template v-slot:button>
                        <div type="button" class="ant-btn ant-btn-flat flex items-center">
                            <div v-if="form.workgroup_logo && form.workgroup_logo.path" class="flex items-center gap-1">
                                <span>{{ $t("wgr.avatar_group") }}:</span>
                                <div>
                                    <a-avatar
                                        class="shrink-0"
                                        :size="20"
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
                                </div>
                            </div>
                            <div v-else class="flex items-center">
                                <i class="fi fi-rr-clip mr-2" />
                                {{ $t('wgr.avatar_project') }}
                            </div>
                        </div>
                    </template>
                </Upload>
                <UserDrawer
                    :id="defaultUserSelectId"
                    v-model="form.members.profile_id"
                    :metadata="{ key: 'profile_id', value: form.metadata }"
                    :changeMetadata="changeMetadata"
                    multiple
                    buttonNew
                    :buttonText="$t('wgr.participants')"
                    buttonIcon="fi-rr-user-add"
                    :title="$t('wgr.participants')"/>
                <!--<a-checkbox v-model="form.public_or_private" style="margin-left: 10px;">
                    {{$t('wgr.closed')}}
                </a-checkbox>-->
                <!--<a-checkbox v-model="form.with_chat" style="margin-left: 0px;">
                    {{$t('wgr.with_chat')}}
                </a-checkbox>-->
            </div>
        </a-form-model>
        <template #footer>
            <div v-if="!formLoading" class="flex items-center justify-between w-full">
                <div class="flex gap-1 items-center">
                    <a-button type="primary" size="large" :loading="loading" @click="onSubmit()">
                        {{ $t('wgr.create_group') }}
                    </a-button>
                    <a-button type="ui_ghost" ghost size="large" @click="visible = false">
                        {{ $t("wgr.close") }}
                    </a-button>
                </div>
                <!--
                <a-button type="ui_ghost" ghost size="large" @click="openFullForm()">
                    {{ $t('open_full_form') }}
                </a-button>-->
            </div>
            <a-skeleton v-else active :paragraph="{rows: 0}" />
        </template>
    </a-modal>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { formModel } from './utils.js'
import createdMethods from "./mixins/createdMethods"
import { mapState } from 'vuex'
import { errorHandler } from '@/utils/index.js'
export default {
    mixins: [createdMethods],
    components: {
        DSelect: () => import('@apps/DrawerSelect/Select.vue'),
        Upload: () => import("@apps/Upload"),
        UserDrawer: () => import("@apps/DrawerSelect/index.vue"),
        HelpButton: () => import('@apps/Support/components/HelpButton.vue')
    },
    props: {
        pageName: {
            type: String,
            default: 'page_list_workgroup_workgroups.WorkgroupModel',
        },
        model: {
            type: String,
            default: "workgroups.WorkgroupModel",
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        })
    },
    data() {
        return {
            rules: {
                organization: [
                    {
                        required: true,
                        message: this.$t("project.field_require"),
                        trigger: "blur",
                    },
                ],
            },
            defaultUserSelectId: 'workgroups',
            loading: false,
            formLoading: false,
            visible: false,
            form: {...formModel},
            nameRules: {
                name: [
                    { required: true, message: '', trigger: 'blur' }
                ]
            }
        }
    },
    methods: {
        changeMetadata({ key, value }) {
            this.$set(this.form.metadata, key, value);
        },
        getCalendarContainer(trigger) {
            return trigger.parentNode
        },
        async formInit() {
            try {
                await this.init()
                await this.$nextTick()
                requestAnimationFrame(() => {
                    if(this.$refs?.nameInput)
                        this.$refs.nameInput.focus()
                })
            } catch(e) {
                console.log(e)
            } finally {
                this.formLoading = false
            }
        },
        afterVisibleChange(vis) {
            if (vis) {
                this.$nextTick()
                requestAnimationFrame(() => {
                    if(this.$refs?.nameInput)
                        this.$refs.nameInput.focus()
                })
            } else {
                this.formLoading = false
                this.clearForm()
            }
        },
        async openFullForm() {
            const query = JSON.parse(JSON.stringify(this.$route.query))
            if (!query.createGroup) {
                query.createGroup = true
                this.$store.commit('workgroups/SET_FORM_INJECT', { ...this.form })
                await this.$router.replace({ query })
                this.visible = false
            }
        },
        clearForm() {
            this.form = JSON.parse(JSON.stringify(formModel))
            this.form.members.profile_id = []
            this.form.metadata.profile_id = []
        },
        async onSubmit() {
            this.$refs.ruleForm.validate(async (valid) => {
                this.$refs.nameForm.validate(async valid2 => {
                    if (valid && valid2) {
                        try {
                            if(!this.form.name) {
                                this.$message.error(this.$t("wgr.fill_all_fields"))
                                return false
                            }

                            this.loading = true;

                            const form = JSON.parse(JSON.stringify(this.form))
                            if (form.workgroup_logo?.id)
                                form["workgroup_logo"] = form.workgroup_logo.id;
                            else form["workgroup_logo"] = null;

                            if (form.members.profile_id?.length)
                                form.members.profile_id = form.members.profile_id
                                    .map(item => item.id)
                                    .filter(id => id !== this.user.id)


                            const res = await this.createGroupS(form);

                            const openProject = () => {
                                const query = {...this.$route.query}
                                if(!query.viewGroup) {
                                    query.viewGroup = res.id;
                                    this.$router.push({ query });
                                }
                            }

                            this.$message.info(
                                this.$createElement("span", {}, [
                                `${this.$t("wgr.group_created")}. `,
                                this.$createElement(
                                    "span",
                                    {
                                        class: "link cursor-pointer blue_color",
                                        on: {
                                            click: () => {
                                                openProject();
                                            },
                                        },
                                    },
                                    this.$t('wgr.open_group')
                                ),
                                ]),
                                5
                            );
                            eventBus.$emit("update_list_group");
                            eventBus.$emit(`update_filter_${this.model}_${this.pageName}`)
                            this.visible = false
                        } catch (error) {
                            errorHandler({error})
                        } finally {
                            this.loading = false;
                        }
                    } else {
                        this.$message.error(this.$t("wgr.fill_all_fields"));
                    }
                })
            });
        }
    },
    mounted() {
        eventBus.$on('add_workgroup_modal', () => {
            this.visible = true
        })
    },
    beforeDestroy() {
        eventBus.$off('add_workgroup_modal')
    }
}
</script>

<style lang="scss" scoped>
.name_form{
    margin-bottom: -15px;
}
.name_row{
    &::v-deep{
        .has-error{
            .ant-input.ant-input-ghost{
                color: #ff5d5d!important;
                &::placeholder{
                    color: #ff5d5d!important;
                }
            }
            .ant-form-explain{
                display: none;
            }
        }
    }
}
</style>