<template>
    <a-drawer
        title="Добавить заявку"
        :visible="visible"
        class="b_process_drawer"
        @close="visible = false"
        destroyOnClose
        :zIndex="1000"
        :width="600"
        placement="right">
        <div class="drawer_body">
            <a-form-model
                ref="processForm"
                :model="form"
                :rules="rules">
                <a-form-model-item
                    ref="name"
                    prop="name">
                    <a-input
                        v-model="form.name"
                        @pressEnter="formSubmit()"
                        size="large"
                        placeholder="Название" />
                </a-form-model-item>
                <a-form-model-item
                    ref="description"
                    prop="description">
                    <CkeditorTextarea
                        :key="edit || visible"
                        v-model="form.description" />
                </a-form-model-item>
                <a-form-model-item
                    ref="dead_line"
                    label="Крайний срок"
                    prop="dead_line">
                    <DatePicker
                        v-model="form.dead_line"
                        size="large"
                        :show-time="{ format: 'HH:mm' }" />
                </a-form-model-item>
                <a-form-model-item
                    v-if="!defaultItinerary"
                    ref="itinerary"
                    prop="itinerary">
                    <a-select 
                        v-model="form.itinerary"
                        size="large"
                        :loading="itineraryLoading">
                        <a-select-option 
                            v-for="item in itineraryList" 
                            :key="item.id" 
                            :value="item.id">
                            {{ item.name }}
                        </a-select-option>
                    </a-select>
                </a-form-model-item>
                <a-form-model-item
                    ref="amount_of_money"
                    label="Сумма заявки"
                    prop="amount_of_money">
                    <a-input-number
                        v-model="form.amount_of_money"
                        class="amount_of_money"
                        @pressEnter="formSubmit()"
                        size="large" 
                        :min="0" 
                        :max="10000000000" />
                </a-form-model-item>
                <a-form-model-item
                    label="Файлы"
                    prop="attachments">
                    <Upload
                        :key="edit || visible"
                        v-model="form.attachments"
                        :defaultList="fileList"
                        multiple />
                </a-form-model-item>
            </a-form-model>
        </div>
        <div class="drawer_footer">
            <a-button 
                :loading="loading" 
                @click="formSubmit()"
                type="primary">
                {{ edit ? 'Редактировать' : 'Добавить' }}
            </a-button>
        </div>
    </a-drawer>
</template>

<script>
import DatePicker from '@apps/Datepicker'
import CkeditorTextarea from '@apps/CKEditor'
import Upload from '@apps/Upload'
import eventBus from '../../utils/eventBus'
const formModel = {
    name: '',
    description: '',
    amount_of_money: null,
    itinerary: null,
    attachments: [],
    dead_line: null
}
export default {
    components: {
        CkeditorTextarea,
        Upload,
        DatePicker
    },
    computed: {
        updateModel() {
            return this.$store.state.bprocess.updateModel
        },
        visible: {
            get() {
                return this.$store.state.bprocess.editDrawer
            },
            set(val) {
                this.$store.commit('bprocess/SET_EDIT_DRAWER', val)
            }
        },
        itineraryList() {
            return this.$store.state.bprocess.processList
        }
    },
    watch: {
        visible(val) {
            if(val) {
                this.getCurrentItinerary()
                this.getList()
            } else
                this.clear()
        }
    },
    data() {
        return {
            loading: false,
            itineraryLoading: false,
            edit: false,
            defaultItinerary: false,
            fileList: [],
            form: Object.assign({}, formModel),
            rules: {
                name: [
                    { required: true, message: 'Обязательно для заполнения', trigger: 'blur' },
                    { max: 255, message: 'Максимум 255 символов', trigger: 'blur' }
                ],
                amount_of_money: [
                    { required: true, message: 'Обязательно для заполнения', trigger: 'blur' }
                ]
            }
        }
    },
    methods: {
        getCurrentItinerary() {
            if(this.$route.params?.processId) {
                this.defaultItinerary = true
                this.form.itinerary = this.$route.params.processId
            }
        },
        clear() {
            this.edit = false
            this.fileList = []
            this.defaultItinerary = false
            this.form = Object.assign({}, formModel)
        },
        async getList() {
            try {
                this.itineraryLoading = true
                await this.$store.dispatch('bprocess/getMainList')
            } catch(e) {
                console.log(e)
            } finally {
                this.itineraryLoading = false
            }
        },
        formSubmit() {
            this.$refs.processForm.validate(async valid => {
                if (valid) {
                    if(!this.edit) {
                        try {
                            this.loading = true
                            const { data } = await this.$http.post('/processes/financial_application/create/', this.form)
                            if(data) {
                                this.$message.success('Заявка успешно добавлена')
                                this.visible = false
                                eventBus.$emit(`UNSHIFT_PROCESS_LIST_${this.updateModel}`, data)
                                let query = Object.assign({}, this.$route.query)
                                if(query.bprocess && query.bprocess !== data.id || !query.bprocess) {
                                    query.bprocess = data.id
                                    this.$router.push({query})
                                }
                            }
                        } catch(e) {
                            console.log(e)
                        } finally {
                            this.loading = false
                        }
                    }
                } else
                    return false
            })
        }
    }
}
</script>

<style lang="scss">
.b_process_drawer{
    .amount_of_money{
        width: 100%;
        max-width: 250px;
    }
    .ant-drawer-content,
    .ant-drawer-wrapper-body{
        overflow: hidden;
    }
    .ant-drawer-body{
        height: calc(100% - 40px);
        padding: 0px;
        .drawer_body{
            height: calc(100% - 40px);
            padding: 20px;
            overflow-y: auto;
            overflow-x: hidden;
        }
        .drawer_footer{
            display: flex;
            align-items: center;
            height: 40px;
            border-top: 1px solid #e8e8e8;
            padding-left: 20px;
            padding-right: 20px;
        }
    }
    .ck-editor__editable {
        max-height: 300px;
    }
}
</style>