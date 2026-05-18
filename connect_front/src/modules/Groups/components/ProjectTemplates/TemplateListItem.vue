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
                            :placeholder="$t('wgr.enter_the_template_name')" />
                        <a-tooltip :title="$t('save')" destroyTooltipOnHide>
                            <a-button 
                                @click="save"
                                class="ml-2" 
                                :loading="loading"
                                type="link" 
                                flaticon 
                                icon="fi-rr-disk">
                            </a-button>  
                        </a-tooltip>
                        <a-tooltip :title="$t('cancel')" destroyTooltipOnHide>
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
                @click="selectHandler(item.id)"    
                class="item" :class="active && 'active'">
                <span>{{ item.name }}</span>
                <a-tooltip :title="$t('edit')" destroyTooltipOnHide>
                    <a-button 
                        @click="enableEditing"
                        class="ml-8" 
                        :loading="loading"
                        type="link" 
                        flaticon 
                        icon="fi-rr-pencil">
                    </a-button>                           
                </a-tooltip>
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
                    { required: true, message: this.$t('wgr.field_require'), trigger: 'blur' },
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
                        message: this.$t('wgr.template_saved_successfully'),
                    })
                    eventBus.$emit('reload_template_list')
                })
                .catch(error => {
                    console.error(error)
                    this.$notification.error({
                        message: this.$t('wgr.save_template_error'),
                    })
                })
                .finally(() => {
                    this.loading = false
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
    justify-content: space-between;
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