<template>
    <FormsWidget
        v-if="formStruct"
        :key="`${action}_task`"
        :form="formStruct"
        :showActionButtons="false"
        :showSidebar="false"
        injectedPart
        injectForm
        ref="pvh_form"
        :meta="formStruct"
        :params="params"
        :action="action"
        :id="params.id" />
</template>

<script>
import { mapGetters } from 'vuex'
import { v4 as uuidv4 } from 'uuid'
export default {
    components: {
        FormsWidget: () => import('@/components/FormsWidget/TableForm')
    },
    props: {
        form: {
            type: Object,
            required: true
        },
        formInfo: {
            type: Object,
            required: true
        },
        edit: {
            type: Boolean,
            default: false
        },
        setButtonLoading: {
            type: Function,
            required: true
        }
    },
    computed: {
        ...mapGetters({
            getFormByKey: 'form/getFormByKey'
        }),
        formStruct() {
            if(this.name.length) {
                return this.getFormByKey(this.name)
            } else
                return null
        }
    },
    data() {
        return {
            action: this.edit ? 'update' : 'create',
            name: '',
            params: {
                action: this.edit ? 'update' : 'create',
                id: this.edit ? this.form.id : uuidv4()
            }
        }
    },
    created() {
        this.getFormInfo()
    },
    methods: {
        async getFormInfo() {
            try {
                this.setButtonLoading(true)
                const data = await this.$store.dispatch('form/getTaskFormInfo', {
                    form: this.form,
                    formInfo: this.formInfo
                })
                if(data) {
                    this.name = `${data.name}_${this.form.task_type}`
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.setButtonLoading(false)
            }
        }
    }
}
</script>