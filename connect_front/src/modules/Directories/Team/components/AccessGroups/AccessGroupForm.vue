<template>
    <a-form-model 
        ref="form" 
        class="text-black"
        :model="form"
        :rules="rules">
        <div class="form-panel">
            <p class="mb-4 text-base">{{ $t("Description") }}</p>
            <a-form-model-item 
                :label="$t('Group name')"
                prop="name">
                <a-input
                    v-model="form.name"
                    :max-length="255"
                    :disabled="isDisabled"
                    :placeholder="$t('Group name')"
                    size="large"/>
            </a-form-model-item>
            <a-form-model-item :label="$t('Description')">
                <a-input
                    v-model="form.description"
                    :max-length="255"
                    :disabled="isDisabled"
                    :placeholder="$t('Description')"
                    size="large"/>
            </a-form-model-item>
        </div>

        <div class="form-panel">
            <p class="mb-4 text-base">{{ $t("Main modules") }}</p>

            <div class="module-row" v-for="module in mainModules" :key="module.code">
                <p>
                    {{ module.name }}
                </p>
                <DSelect
                    v-model="form.app_section_roles[module.code]"
                    size="large"
                    apiUrl="/contractor_permissions/app_section_roles/"
                    class="w-full"
                    oneSelect
                    :disabled="isDisabled"
                    :params="{
                        app_section: module.code,
                    }"
                    :listObject="false"
                    valueKey="code"
                    infinity
                    :key="module.code"
                    labelKey="name"
                    :default-active-first-option="false"
                    :filter-option="false"
                    :not-found-content="null"/>
            </div>
        </div>

        <div class="form-panel">
            <p class="mb-4 text-base">{{ $t("Additional modules") }}</p>

            <div
                class="module-row"
                v-for="module in addtionalModules"
                :key="module.code">
                <p>
                    {{ module.name }}
                </p>
                <DSelect
                    v-model="form.app_section_roles[module.code]"
                    size="large"
                    apiUrl="/contractor_permissions/app_section_roles/"
                    class="w-full"
                    oneSelect
                    :disabled="isDisabled"
                    :params="{
                        app_section: module.code,
                    }"
                    :listObject="false"
                    valueKey="code"
                    infinity
                    :key="module.code"
                    labelKey="name"
                    :default-active-first-option="false"
                    :filter-option="false"
                    :not-found-content="null"/>
            </div>
        </div>
    </a-form-model>
</template>

<script>
export default {
    components: {
        DSelect: () => import("@apps/DrawerSelect/Select.vue")
    },
    props: {
        organization: {
            type: Object,
            required: true,
        },
        edit: {
            type: Boolean,
            default: false
        },
        accessGroup: {
            type: Object,
            default: () => {}
        }
    },
    data() {
        return {
            form: {
                name: "",
                app_section_roles: {},
                contractor: this.organization.id,
                members: [],
            },
            mainModules: [],
            addtionalModules: [],
            rules: {
                name: [
                    {
                        required: true,
                        message: this.$t('team.team.required_field'),
                        trigger: 'blur'
                    }
                ]
            }
        };
    },
    computed: {
        isDisabled() {
            return this.accessGroup?.is_predefined
        }
    },
    created() {
        this.getModules();
        if (this.accessGroup?.id) {
            this.form = JSON.parse(JSON.stringify(this.accessGroup))
            this.form.app_section_roles = this.accessGroup?.app_section_roles
                ?.reduce((acc, curr) => {
                    acc[curr.app_section.code] = curr.role.code
                    return acc
                }, {})
        }
    },
    methods: {
        getModules() {
            const params = {
                contractor: this.organization.id,
            };
            const url = "contractor_permissions/access_groups/available_sections/";
            this.$http(url, { params }).then(({ data }) => {
                this.mainModules = data.filter((item) => item.is_main);
                this.addtionalModules = data.filter((item) => !item.is_main);
            });
        },
        getPContainer() {
            return this.$refs.form;
        },
        reset() {
            this.form = {
                name: "",
                app_section_roles: {},
                contractor: this.organization.id,
                members: [],
            };
        },
        submit(action=null) {
            return this.$refs.form.validate()
                .then(() => {
                    if (action === 'update') {
                        this.update()
                    } else {
                        this.save()
                    }
                })
                .catch(error => {
                    this.$message.error(this.$t('team.fill_all_fields'))
                    throw Error()
                })
        },
        save() {
            const roles = [];
            for (const key in this.form.app_section_roles) {
                roles.push({
                    app_section: key,
                    role: this.form.app_section_roles[key],
                });
            }
            const payload = {
                ...this.form,
                app_section_roles: roles,
            };
            const url = "/contractor_permissions/access_groups/";
            return this.$http
                .post(url, payload)
                .then(({ data }) => {
                    this.reset();
                    return data.id
                })
                .catch((error) => {
                    this.$message.error(this.$t('team.team.failed_to_create_access_group'));
                    console.error(error);
                })
        },
        update() {
            const roles = [];
            for (const key in this.form.app_section_roles) {
                roles.push({
                    app_section: key,
                    role: this.form.app_section_roles[key],
                });
            }
            const payload = {
                ...this.form,
                app_section_roles: roles,
            };
            const url = `/contractor_permissions/access_groups/${this.accessGroup.id}/`;
            return this.$http
                .put(url, payload)
                .then(({ data }) => {
                    this.reset();
                })
                .catch((error) => {
                    this.$message.error(this.$t('team.team.failed_to_update_access_group'));
                    console.error(error);
                })
        }
    },
};
</script>

<style lang="scss" scoped>
.form-panel {
  padding: 20px;
  border: 1px solid #d9d9d9;
  border-radius: 8px;

  & + & {
    margin-top: 10px;
  }
}

.module-row {
  display: grid;
  align-items: center;
  grid-template-columns: 1fr 3fr;
  column-gap: 20px;

  &:not(:last-child) {
    margin-bottom: 15px;
  }
}

::v-deep {
  .ant-form-item {
    margin: 0;

    &:not(:last-child) {
      margin-bottom: 10px;
    }
  }
  .ant-form-item-label > label {
    color: #00000099;
  }
}
</style>