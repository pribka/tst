<template>
    <a-modal
        :title="modalInfo.title"
        :visible="value"
        :dialogClass="modalInfo.dialogClass"
        :width="modalInfo.width"
        :zIndex="9999999"
        :forceRender="modalInfo.forceRender"
        :afterClose="afterClose"
        @cancel="cancelModal">
        <div :ref="`tab_wrap_${code}`">
            <a-form-model 
                :ref="`tab_form_${code}`" 
                :model="form">
                <FieldSwitch 
                    v-for="field in formField" 
                    :key="field.key"
                    :field="field"
                    :formSubmit="formSubmit"
                    :form="form"
                    :code="code"
                    :edit="edit"
                    :task="task" />
            </a-form-model>
        </div>
        <template slot="footer">
            <template v-if="modalInfo.modalButtons">
                <a-button 
                    v-if="modalInfo.modalButtons.ok" 
                    :type="modalInfo.modalButtons.ok.type"
                    :size="modalInfo.modalButtons.ok.size"
                    :loading="loading"
                    @click="formSubmit()">
                    {{ modalInfo.modalButtons.ok.title }}
                </a-button>
                <a-button 
                    v-if="modalInfo.modalButtons.cancel" 
                    :type="modalInfo.modalButtons.cancel.type"
                    :size="modalInfo.modalButtons.cancel.size"
                    @click="cancelModal()">
                    {{ modalInfo.modalButtons.cancel.title }}
                </a-button>
            </template>
        </template>
    </a-modal>
</template>

<script>
import { mapGetters } from 'vuex'
import FieldSwitch from './FormWidgets/FieldSwitch.vue'
import eventBus from '@/utils/eventBus'
export default {
    components: {
        FieldSwitch
    },
    props: {
        value: {
            type: Boolean
        },
        tab: {
            type: Object,
            default: () => null
        },
        task: {
            type: Object,
            default: () => null
        },
        code: {
            type: [String, Number],
            required: true
        }
    },
    computed: {
        ...mapGetters({
            getTabForm: 'task/getTabForm'
        }),
        form: {
            get() {
                return this.getTabForm(this.task.id, this.code)
            },
            set(value) {
                this.$store.commit('task/SET_UNIVERSAL_TAB_FORM', {
                    value,
                    task: this.task,
                    part: this.code
                })
            }
        },
        modalInfo() {
            return this.tab.modal
        },
        formField() {
            return this.tab.formInfo.formField
        }
    },
    data() {
        return {
            loading: false,
            edit: false
        }
    },
    methods: {
        afterClose() {
            this.$store.commit('task/CLEAR_UNIVERSAL_TAB_FORM', {
                task: this.task,
                part: this.code
            })
            this.edit = false
        },
        cancelModal() {
            this.$emit('input', false)
        },
        formSubmit() {
            this.$refs[`tab_form_${this.code}`].validate(async valid => {
                if (valid) {
                    try {
                        this.loading = true
                        if(this.edit) {
                            await this.$store.dispatch('task/updateTabData', {
                                code: this.code,
                                task: this.task
                            })
                        } else {
                            await this.$store.dispatch('task/cretaeTabData', {
                                code: this.code,
                                task: this.task
                            })
                        }
                        
                        this.$emit('input', false)
                    } catch(error) {
                        if(error?.detail) {
                            if(error.detail.includes('User is not task owner.'))
                                this.$message.error(this.$t(`task.user_not_owner`))
                        }
                        console.log(error)
                    } finally {
                        this.loading = false
                    }
                } else {
                    this.$message.warning(this.$t('task.field_require_all'))
                    return false
                }
            })
        }
    },
    mounted() {
        eventBus.$on(`update_universal_${this.code}`, data => {
            this.$emit('input', true)
            this.edit = true
            this.form = data
            console.log(data, 'data')
        })
    },
    beforeDestroy() {
        eventBus.$off(`update_universal_${this.code}`)
    }
}
</script>