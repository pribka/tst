<template>
    <div class="">
        <a-form-model 
            ref="formRef"
            :model="form"
            :rules="rules">
            <p class="mb-1 opacity-60">
                {{ $t('wgr.the_organization_using_the_template') }}
            </p>
            <DSelect
                v-model="form.organization"
                size="large"
                apiUrl="/contractor_permissions/organizations/"
                class="mb-4 w-full"
                oneSelect
                :listObject="false"
                labelKey="name"
                :params="{ permission_type: 'create_workgroup' }"
                :placeholder="$t('sports.selectFromList')"
                :default-active-first-option="false"
                :filter-option="false"
                :not-found-content="null" />
            <a-form-model-item prop="name" class="mb-4">
                <a-input 
                    v-model="form.name" 
                    size="large" 
                    :placeholder="$t('wgr.enter_the_template_name')" />
            </a-form-model-item>

            <template v-if="user.is_support">
                <div class="mb-4">
                    <span class="mr-5">Публичный шаблон</span>
                    <a-switch 
                        v-model="form.isPublic" />
                </div>
            </template>
        </a-form-model>
        <a-button 
            size="large" 
            block 
            type="primary" 
            @click="submit">
            {{  $t('wgr.create_template') }}
        </a-button>
    </div>
</template>


<script>
import DSelect from '@apps/DrawerSelect/Select.vue'
import eventBus from '@/utils/eventBus'
export default {
    components: {
        DSelect
    },
    props: {
    },
    data() {
        return {
            rules: {
                name: [
                    { required: true, message: this.$t('wgr.field_require'), trigger: 'blur' },
                ],
            },
            form: {
                name: '',
                organization: '',
                isPublic: false,
                isDraft: false,
            }
        }
    },
    computed: {
        user() { return this.$store.state.user.user },
    },
    methods: {
        submit() {
            this.$refs.formRef.validate(valid => {
                if (valid) {
                    this.createTemplate()
                } else {
                    this.$notification.warning({
                        message: this.$t('wgr.please_fill_in_all_required_fields'),
                    })
                    return false;
                }
            });
        },
        createTemplate() {
            const url = 'work_groups/templates/'
            const payload = {
                ...this.form
                // name: this.form.name,
                // organization: "ada02924-7418-11ef-8232-991659feeb66",
                // is_public: false,
                // is_draft: false
            }

            this.$http.post(url, payload)
                .then(({ data }) => {
                    this.clearForm()
                    eventBus.$emit('reload_template_list')
                })
                .catch(error => {
                    console.error(error)
                    this.$notification.error({
                        message: this.$t("wgr.could_not_create_a_template"),
                    })
                })
        },
        clearForm() {
            const formTemplate = {
                isPublic: false,
                organization: null,
                name: ''
            } 
            this.$emit('input', formTemplate)
        }

    }
}
</script>