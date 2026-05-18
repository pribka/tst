<template>
    <div class="">
        <a-form-model 
            ref="formRef"
            :model="form"
            :rules="rules">
            <p class="mb-1 opacity-60">
                {{ $t('Organization using a template') }}
            </p>
            <a-form-model-item prop="organization">
                <DSelect
                    v-model="form.organization"
                    size="large"
                    apiUrl="/contractor_permissions/organizations/"
                    class="w-full"
                    oneSelect
                    :listObject="false"
                    allowClear
                    labelKey="name"
                    :params="{ permission_type: 'create_workgroup' }"
                    :placeholder="$t('sports.selectFromList')"
                    :default-active-first-option="false"
                    :filter-option="false"
                    :not-found-content="null" />
            </a-form-model-item>
            <a-form-model-item prop="name" class="mb-4">
                <a-input 
                    v-model="form.name" 
                    size="large" 
                    :placeholder="$t('Enter a template name')" />
            </a-form-model-item>

            <template v-if="user.is_support">
                <div class="mb-4">
                    <span class="mr-5">{{ $t('Public template') }}</span>
                    <a-switch 
                        v-model="form.is_public" />
                </div>
            </template>
        </a-form-model>
        <a-button 
            size="large" 
            block 
            type="primary" 
            @click="submit">
            {{  $t('Create template') }}
        </a-button>
    </div>
</template>


<script>
import eventBus from '@/utils/eventBus'
export default {
    components: {
        DSelect: () => import('@apps/DrawerSelect/Select.vue')
    },
    data() {
        return {
            form: {
                name: '',
                organization: '',
                is_public: false,
                is_draft: true,
            }
        }
    },
    computed: {
        user() { return this.$store.state.user.user },
        rules() {
            const rules = {
                name: [
                    { required: true, message: this.$t('project.field_require'), trigger: 'blur' },
                ],
                organization: [
                    { required: true, message: this.$t('project.field_require'), trigger: 'blur' },
                ]
            }
            if (this.form.is_public) {
                rules.organization[0].required = false
            }   
            return rules
        },
    },
    methods: {
        submit() {
            this.$refs.formRef.validate(valid => {
                if (valid) {
                    this.createTemplate()
                } else {
                    this.$notification.warning({
                        message: this.$t('Fill in the required fields'),
                    })
                    return false;
                }
            });
        },
        createTemplate() {
            const url = 'work_groups/templates/'
            const payload = {
                ...this.form,
            }

            this.$http.post(url, payload)
                .then(({ data }) => {
                    this.clearForm()
                    eventBus.$emit('reload_template_list')
                })
                .catch(error => {
                    console.error(error)
                    this.$notification.error({
                        message: this.$t("project.could_not_create_a_template"),
                    })
                })
        },
        clearForm() {
            this.form = {
                is_public: false,
                organization: null,
                is_draft: true,
                name: ''
            } 
        }

    }
}
</script>