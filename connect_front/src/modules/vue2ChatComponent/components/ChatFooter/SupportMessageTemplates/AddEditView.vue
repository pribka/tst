<template>
    <div>
        <div class="head">
            <div class="title">
                {{ $t('chat.popup_title') }}
            </div>
            <div class="close-icon" @click="closeAddEdit">
                <a-icon type="close" />
            </div>
        </div>
        <a-spin :spinning="loading">
            <div class="form">
                <div class="title" :class="titleError && 'error'">
                    <div class="label ant-form-item-required">{{ $t('chat.form.title') }}</div>
                    <div class="input-field">
                        <a-input
                            v-model="title"
                            :maxLength="255" />
                    </div>
                </div>
                <div class="text" :class="textError && 'error'">
                    <div class="label ant-form-item-required">{{ $t('chat.form.message') }}</div>
                    <div class="text-input-field">
                        <a-textarea
                            v-model="text"
                            :maxLength="1023" />
                    </div>
                </div>
            </div>
            <div class="is-private-switch">
                <span class="label">{{ $t('chat.form.public') }}</span>
                <a-switch v-model="isPublic" class="switch"/>
            </div>
            <div class="button">
                <a-button
                    @click="submit"
                    :disabled="loading"
                    type="primary">{{ $t('chat.button.submit') }}</a-button>
            </div>
            <a-popconfirm
                :title="$t('chat.form.delete_template')"
                :ok-text="$t('chat.form.confirm_delete')"
                :cancel-text="$t('chat.form.cancel_delete')"
                @confirm="deleteConfirm">
                <div v-if="edit" class="delete">
                    {{ $t('chat.form.delete_template') }}
                </div>
            </a-popconfirm>
        </a-spin>
    </div>
</template>

<script>
import { mapState } from 'vuex'
import FormValidation from './FormValidation'

export default {
    name: 'AddEditView',
    props: {
        edit: {
            type: Boolean,
            default: false
        },
        editableTemplateID: {
            type: String,
            default: ''
        },
        deleteTemplate: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return{
            title: '',
            text: '',
            isPublic: false,
            loading: false,
            validateErrors: {}
        }
    },
    mounted() {
        if(this.edit) {
            const template = this.getTemplate()
            if(!template)
                return
            this.title = template.title
            this.text = template.text
            this.isPublic = template.is_public
        }
    },
    computed: {
        ...mapState({
            templateList: state => state.chat.supportMessageTemplates
        }),
        popup_title() {
            return this.edit ? this.$t('chat.edit_template') : this.$t('chat.new_template');
        },
        buttonText() {
            return this.edit ? this.$t('chat.save') : this.$t('chat.create');
        },
        titleError() {
            return 'title' in this.validateErrors;
        },
        textError() {
            return 'text' in this.validateErrors;
        }
    },
    methods: {
        closeAddEdit() {
            this.$emit('closeAddEdit')
        },
        deleteConfirm() {
            this.deleteTemplate(this.editableTemplateID)
            this.closeAddEdit()
        },
        getTemplate() {
            if(!this.editableTemplateID)
                return null
            const index = this.templateList.findIndex(item => item.id === this.editableTemplateID)
            if(index === -1)
                return null
            return this.templateList[index]
        },
        submit() {
            const payload = {
                title: this.title,
                text: this.text,
                is_public: this.isPublic
            }
            if(this.loading)
                return;
        
            let validations = new FormValidation(this.title, this.text);
            this.validateErrors = validations.validate();
            if(Object.keys(this.validateErrors).length) {
                for(let error in this.validateErrors) {
                    this.$message.error(this.validateErrors[error]);
                }
                return;
            }
    
            this.loading = true;
            if(this.edit) {
                const url = `chat/message_templates/${this.editableTemplateID}/`;
                this.$http.put(url, payload)
                    .then(response => {
                        this.$store.dispatch('chat/updateSMT', response.data);
                        this.$emit('closeAddEdit');
                    })
                    .catch(e => {
                        this.$message.error(this.$t('chat.template_save_error'));
                        console.log(e);
                    })
                    .finally(() => {
                        this.loading = false;
                    });
            } else {
                const url = 'chat/message_templates/';
                this.$http.post(url, payload)
                    .then(response => {
                        this.$store.commit('chat/ADD_SUPPORT_MESSAGE_TEMPLATE', response.data);
                        this.$emit('closeAddEdit');
                    })
                    .catch(e => {
                        this.$message.error(this.$t('chat.template_create_error'));
                        console.log(e);
                    })
                    .finally(() => {
                        this.loading = false;
                    });
            }
        }
    }
}
</script>
<style lang="scss" scoped>
.head{
    display: grid;
    grid-template-columns: 1fr auto;
    border-bottom: 2px solid rgb(0, 0, 0, 1);
    padding-bottom: 25px;
    align-items: center;
    .title{
        font-size: 16px;
        font-weight: 400;
        line-height: 16px;
        text-align: left;
    }
    .close-icon{
        height: 14px;
        width: 14px;
        cursor: pointer;
    }
}
.form{
    display: grid;
    grid-template-rows: repeat(2, auto);
    row-gap: 20px;
    margin-top: 25px;
    .label{
        font-size: 14px;
        font-weight: 400;
        line-height: 14px;
        text-align: left;
        margin-bottom: 10px;
    }
    .title{
        .input-field{
            .ant-input{
                height: 40px;
            }
        }
    }
    .text{
        .text-input-field{
            .ant-input{
                height: 122px;
                min-height: 122px;
                max-height: 122px;
                overflow-y: auto;
            }
        }
    }
    .error {
        .ant-input{
            border-color: red;
        }
        .label{
            color: red;
        }
    }
}
.is-private-switch{
    margin-top: 20px;
    .switch{
        margin-left: 20px;
    }
}
.button{
    margin-top: 20px;
    .ant-btn{
        height: 40px;
        width: 100%;
    }
}
.delete{
    margin-top: 20px;
    text-align: center;
    color: rgba(214, 46, 46, 1);
    font-size: 14px;
    font-weight: 400;
    line-height: 14px;
    text-align: center;
    cursor: pointer;
}
</style>