<template>
    <a-modal
        :title="edit ? $t('calendar.edit_calendar') : $t('calendar.add_calendar')"
        :visible="visible"
        :footer="null"
        :afterClose="afterClose"
        :width="500"
        @cancel="visible = false">
        <a-form-model
            ref="ruleForm"
            :model="form"
            :rules="rules">
            <div class="lg:flex lg:items-start mb-4">
                <a-form-model-item ref="name" :label="$t('calendar.name_label')" prop="name" class="w-full mb-0">
                    <a-input v-model="form.name" size="large" />
                </a-form-model-item>
                <a-form-model-item v-if="!isMobile" ref="color" :label="$t('calendar.color_label')" prop="color" class="ml-2 mb-0">
                    <ColorPicker v-model="form.color" />
                </a-form-model-item>
                <a-form-model-item v-else ref="color" :label="$t('calendar.color_label')" prop="color" class="mt-3 mb-0">
                    <ColorPicker v-model="form.color" typeList />
                </a-form-model-item>
            </div>
            <a-form-model-item>
                <a-button 
                    type="primary" 
                    size="large" 
                    :loading="loading" 
                    block
                    @click="onSubmit()">
                    {{$t('calendar.save_calendar')}}
                </a-button>
            </a-form-model-item>
        </a-form-model>
    </a-modal>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
export default {
    props: {
        elementUpdate: {
            type: Function,
            default: () => {}
        },
        listReload: {
            type: Function,
            default: () => {}
        }
    },
    components: {
        ColorPicker: () => import('./ColorPicker.vue')
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    data() {
        return {
            visible: false,
            loading: false,
            edit: false,
            rules: {
                name: [
                    { required: true, message: this.$t('calendar.required_field'), trigger: 'blur' },
                    { max: 255, message: this.$t('calendar.max_255'), trigger: 'blur' }
                ]
            },
            form: {
                name: '',
                color: '#009be5'
            }
        }
    },
    methods: {
        afterClose() {
            this.edit = false
            this.form = {
                name: '',
                color: '#009be5'
            }
        },
        openModal(isEdit = false, item = null) {
            if(isEdit) {
                this.edit = true
                this.form = JSON.parse(JSON.stringify(item))
            }
            this.visible = true
        },
        onSubmit() {
            this.$refs.ruleForm.validate(async valid => {
                if (valid) {
                    try {
                        this.loading = true
                        if(this.edit) {
                            const { data } = await this.$http.put(`/calendars/${this.form.id}/`, this.form)
                            if(data) {
                                this.elementUpdate(data)
                                this.visible = false
                                this.$message.info(this.$t('calendar.calendar_updated', { name: data.name }))
                            }
                        } else {
                            const { data } = await this.$http.post('/calendars/', this.form)
                            if(data) {
                                this.listReload()
                                this.visible = false
                                this.$message.info(this.$t('calendar.calendar_saved', { name: data.name }))
                            }
                        }
                    } catch(error) {
                        errorHandler({error})
                    } finally {
                        this.loading = false
                    }
                } else {
                    return false
                }
            })
        }
    }
}
</script>