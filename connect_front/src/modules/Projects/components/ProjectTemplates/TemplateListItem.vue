<template>
    <div>
        <template v-if="edit">
            <a-form-model 
                ref="formRef"
                :model="form"
                :rules="rules">
                <a-form-model-item prop="name">
                    <div class="flex items-center">
                        <a-input 
                            v-model="form.name" 
                            size="large" 
                            :placeholder="$t('project.enter_the_template_name')" />
                        <a-tooltip :title="$t('save')">
                            <a-button 
                                @click="save"
                                class="ml-2" 
                                :loading="loading"
                                type="link" 
                                flaticon 
                                icon="fi-rr-disk">
                            </a-button>  
                        </a-tooltip>
                        <a-tooltip :title="$t('cancel')">
                            <a-button 
                                @click="cancel"
                                class="ml-2" 
                                :loading="loading"
                                type="link" 
                                flaticon 
                                icon="fi-rr-cross-circle">
                            </a-button>  
                        </a-tooltip>
                    </div>
                </a-form-model-item>
            </a-form-model>
        </template>
        <template v-else>
            <div
                @click="selectHandler({ id: item.id, template: item })"    
                class="item" :class="active && 'active'">
                <div>
                    <template v-if="item.is_draft">
                        <a-tag class="mb-2" color="purple">
                            {{ $t('Draft') }}
                        </a-tag>
                    </template>
                    <p class="mr-4">{{ item.name }}</p>
                </div>
                <template v-if="canChange">
                    <a-tooltip :title="$t('edit')">
                        <a-button 
                            @click="enableEditing"
                            class="ml-auto" 
                            :loading="loading"
                            type="link" 
                            flaticon 
                            icon="fi-rr-pencil">
                        </a-button>                           
                    </a-tooltip>
                    <a-popconfirm 
                        class="ml-2" 
                        :title="$t('Are you sure?')" 
                        ok-text="Да" 
                        cancel-text="Нет"
                        @confirm="deleteTemplate">
                        <a-button class="border-0 shadow-none" type="danger" ghost flaticon icon="fi-rr-trash"></a-button>
                    </a-popconfirm>
                </template>
            </div>
        </template>
    </div>
</template>

<script>
import eventBus from "@/utils/eventBus"
export default {
    props: {
        item: {
            type: Object,
            required: true,
        },
        activeItem: {
            type: String,
            default: ''
        },
        selectHandler: {
            type: Function,
            default: () => {}
        },
    },
    data() { 
        return {
            edit: false,
            loading: false,
            form: {
                name: ''
            },
            rules: {
                name: [
                    { required: true, message: this.$t('project.field_require'), trigger: 'blur' },
                ],
            },
        }
    },
    computed: {
        buttonIcon() {
            return this.edit? 'fi-rr-disk' : 'fi-rr-pencil'
        },
        active() {
            return this.item.id === this.activeItem
        },
        user() {
            return this.$store.state.user.user
        },
        isPublic() {
            return this.item.is_public
        },
        canChange() {
            return this.user.id === this.item.author?.id
        }
        
    }, 
    methods: {
        enableEditing() {
            this.edit = true
            this.form.name = this.item.name
        },
        save() {
            const url = `/work_groups/templates/${this.item.id}/`
            const payload = {
                name: this.form.name
            }
            this.loading = true
            this.$http.put(url, payload)
                .then(({ data }) => {
                    this.$notification.success({
                        message: this.$t('project.template_saved_successfully'),
                    })
                    eventBus.$emit('reload_template_list')
                })
                .catch(error => {
                    console.error(error)
                    this.$notification.error({
                        message: this.$t('project.save_template_error'),
                    })
                })
                .finally(() => {
                    this.loading = false
                })
        },
        deleteTemplate() {
            const url = `/work_groups/templates/${this.item.id}/`
            this.$http.delete(url)
                .then(() => {
                    eventBus.$emit('reload_template_list')
                })
                .catch(error => {
                    this.$message.error(this.$t('error'))
                    console.error(error)
                })
        },
        cancel() {
            this.edit = false
            this.form.name = this.item.name
        }
    }
}
</script>

<style lang="scss" scoped>
.item {
    display: flex;
    align-items: center;
    padding: 20px 16px;
    margin-bottom: 10px;
    border-radius: 6px;
    background-color: #fafafa;
    border: 1px solid transparent;
    transition: color 0.2s ease, border-color 0.2s ease;
    cursor: pointer;
    &:hover {
        color: var(--primaryColor);
    }
    &.active {
        color: var(--primaryColor);
        background-color: var(--primaryHover);
        border-color: var(--primaryColor);
    }
}

</style>