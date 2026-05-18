<template>
    <a-drawer
        ref="addInvestProjectDrawer"
        placement="right"
        :width="drawerWidth"
        :title="$t('sports.repairInfo')"
        :visible="visible"
        destroyOnClose
        :afterVisibleChange="afterVisibleChange"
        @close="visible = false">
        <a-form-model
            ref="formRef"
            :model="form"
            :rules="rules">
            <a-spin :spinning="editLoader">
                <div class="grid gap-4 md:grid-cols-2">
                    <a-form-model-item ref="amount" :label="$t('sports.amount')" prop="amount">
                        <a-input-number 
                            v-model="form.amount" 
                            size="large"
                            :step="0.1" 
                            :min="0"
                            :precision="2"
                            class="w-full" />
                    </a-form-model-item>
                    <a-form-model-item ref="renovation_date" :label="$t('sports.repairDate')" prop="renovation_date">
                        <a-date-picker 
                            v-model="form.renovation_date" 
                            :showToday="false" 
                            class="w-full" 
                            :placeholder="$t('sports.selectDate')" 
                            size="large" />
                    </a-form-model-item>
                    <a-form-model-item ref="renovation_type" :label="$t('sports.repairType')" prop="renovation_type">
                        <DSelect
                            v-model="form.renovation_type"
                            size="large"
                            apiUrl="/sports_facilities/renovation/types/"
                            class="w-full"
                            oneSelect
                            valueKey="code"
                            infinity
                            initList
                            :listObject="false"
                            labelKey="name"
                            :default-active-first-option="false"
                            :filter-option="false"
                            :not-found-content="null" />
                    </a-form-model-item>
                </div>
                <div class="work_types">
                    <div
                        v-for="(work_type, index) in form.works"
                        :key="work_type.id"
                        class="work_types__item"
                        :class="checkLastItem(index)">
                        <div class="col_1">
                            <a-form-model-item 
                                label="Основные работы, можете выбрать несколько видов работы" 
                                :rules="{
                                    required: true,
                                    message: $t('sports.formError'),
                                    trigger: 'blur',
                                }"
                                :prop="'works.' + index + '.type1'">
                                <DSelect
                                    v-model="work_type.type1"
                                    size="large"
                                    apiUrl="/sports_facilities/renovation/work_types/"
                                    class="w-full"
                                    oneSelect
                                    valueKey="code"
                                    :params="{
                                        renovation_type: 'current'
                                    }"
                                    infinity
                                    initList
                                    :listObject="false"
                                    labelKey="full_name"
                                    :default-active-first-option="false"
                                    :filter-option="false"
                                    :not-found-content="null"
                                    @change="changeWorkType(index)"
                                    @changeGetObject="getObject($event, index, 'type1')" />
                            </a-form-model-item>
                        </div>
                        <div class="col_1">
                            <a-form-model-item 
                                label="Виды выполненных работ, можете выбрать несколько видов работы:" 
                                :rules="{
                                    required: true,
                                    message: $t('sports.formError'),
                                    trigger: 'blur',
                                }"
                                class="w-full"
                                :prop="'works.' + index + '.work_type'">
                                <div 
                                    class="filed_row" 
                                    :class="form.works.length === (index + 1) && 'last_row'">
                                    <div class="filed_col_1">
                                        <DSelect
                                            v-model="work_type.work_type"
                                            size="large"
                                            apiUrl="/sports_facilities/renovation/work_types/"
                                            class="w-full"
                                            oneSelect
                                            :params="{
                                                renovation_type: 'current',
                                                parent: work_type.type1
                                            }"
                                            valueKey="code"
                                            :key="work_type.type1"
                                            :disabled="checkDisabled(work_type)"
                                            infinity
                                            :initList="edit"
                                            :listObject="false"
                                            labelKey="full_name"
                                            :default-active-first-option="false"
                                            :filter-option="false"
                                            :not-found-content="null"
                                            @changeGetObject="getObject($event, index, 'work_type')" />
                                    </div>
                                    <div class="filed_col_2">
                                        <div 
                                            class="md:flex items-center actions_col justify-end"
                                            :class="[form.works.length === (index + 1) && 'last_act', form.works.length === 1 && 'first_act']">
                                            <a-button 
                                                v-if="form.works.length === (index + 1)"
                                                type="primary"
                                                size="large"
                                                icon="plus"
                                                :block="isMobile"
                                                class="md:ml-1"
                                                @click="addWorkTypes()">
                                                <template v-if="isMobile">
                                                    {{ $t('sports.addOnly') }}
                                                </template>
                                            </a-button>
                                            <a-button 
                                                v-if="form.works.length > 1"
                                                type="danger"
                                                class="md:ml-1"
                                                size="large"
                                                flaticon
                                                :block="isMobile"
                                                icon="fi-rr-trash"
                                                @click="deleteWorkTypes(index)">
                                                <template v-if="isMobile">
                                                    {{ $t('sports.delete') }}
                                                </template>
                                            </a-button>
                                        </div>
                                    </div>
                                </div>
                            </a-form-model-item>
                        </div>
                    </div>
                    <ul v-if="infoList.length">
                        <li v-for="(item, index) in infoList" :key="index">
                            {{ item.type1.full_name }}: <span>{{ item.work_type.full_name }}</span>
                        </li>
                    </ul>
                </div>
                <a-form-model-item ref="comment" :label="$t('sports.comment')" prop="comment">
                    <a-textarea
                        v-model="form.comment"
                        size="large"
                        :placeholder="$t('sports.enterComment')"
                        :auto-size="{ minRows: 5, maxRows: 6 }" />
                </a-form-model-item>
                <a-form-model-item ref="attachments" prop="attachments">
                    <a-button 
                        type="primary" 
                        size="large" 
                        class="px-7" 
                        :loading="fileLoading" 
                        style="color:#000;" 
                        :block="isMobile"
                        ghost 
                        @click="triggerFileDialog">
                        {{ $t('sports.attachFiles') }}
                    </a-button>
                    <input
                        type="file"
                        ref="repairFiles"
                        multiple
                        style="display: none"
                        @change="handleFileChange" />
                    <div v-if="form.attachments.length" class="files_wrap mt-3">
                        <div class="w_label">Прикреплённые файлы</div>
                        <div class="files_list">
                            <div v-for="(file, index) in form.attachments" :key="file.id" class="file_card truncate">
                                <div class="flex items-center mr-4 truncate">
                                    <i class="fi fi-rr-document file_ico mr-2"></i>
                                    <span class="truncate">{{ file.name }}</span>
                                </div>
                                <div>
                                    <a-button 
                                        type="ui"
                                        ghost
                                        flaticon
                                        icon="fi-rr-trash"
                                        @click="deleteFile(index)" />
                                </div>
                            </div>
                        </div>
                    </div>
                </a-form-model-item>
            </a-spin>
            <a-button type="primary" size="large" block :loading="loading" @click="formSubmit()">
                {{ edit ? $t('sports.save') : $t('sports.addRepairInfo') }}
            </a-button>
        </a-form-model>
    </a-drawer>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { mapState } from 'vuex'
import DSelect from '@apps/DrawerSelect/Select.vue'

export default {
    components: {
        DSelect
    },
    data() {
        return {
            visible: false,
            edit: false,
            fileLoading: false,
            editLoader: false,
            workTypesList: [
                {
                    type1: null,
                    work_type: null
                }
            ],
            form: {
                sport_facility: this.$route.params.id,
                renovation_date: null,
                renovation_type: null,
                comment: "",
                amount: "",
                attachments: [],
                works: [
                    {
                        id: Date.now(),
                        type1: null,
                        work_type: null
                    }
                ]
            },
            loading: false,
            rules: {
                renovation_date: [
                    { required: true, message: this.$t('sports.formError'), trigger: 'blur' }
                ],
                renovation_type: [
                    { required: true, message: this.$t('sports.formError'), trigger: 'blur' }
                ],
                amount: [
                    { required: true, message: this.$t('sports.formError'), trigger: 'blur' }
                ]
            }
        }
    },
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth
        }),
        isMobile() {
            return this.$store.state.isMobile
        },
        drawerWidth() {
            if(this.windowWidth > 1100)
                return 1100
            else {
                return '100%'
            }
        },
        infoList() {
            return this.workTypesList.filter(f => f.type1 && f.work_type)
        }
    },
    methods: {
        checkDisabled(work_type) {
            /*if(this.edit && work_type.disabled) {
                return true
            } else {
                
            }*/
            return work_type.type1 ? false : true
        },
        afterVisibleChange(vis) {
            if(!vis) {
                this.edit = false
                this.workTypesList = [
                    {
                        type1: null,
                        work_type: null
                    }
                ]
                this.form = {
                    sport_facility: this.$route.params.id,
                    renovation_date: null,
                    renovation_type: null,
                    comment: "",
                    attachments: [],
                    amount: "",
                    works: [
                        {
                            id: Date.now(),
                            type1: null,
                            work_type: null
                        }
                    ]
                }
            }
        },
        getObject(e, index, type) {
            this.workTypesList[index][type] = e
        },
        changeWorkType(index) {
            this.form.works[index].work_type = null
        },
        deleteFile(index) {
            this.form.attachments.splice(index, 1)
        },
        triggerFileDialog() {
            this.$refs.repairFiles.click()
        },
        resetFileInput() {
            this.$refs.repairFiles.value = null
        },
        async handleFileChange(event) {
            const files = Array.from(event.target.files)
                .filter((file) => file.type.startsWith("image/"))
            try {
                this.fileLoading = true
                for(const i in files) {
                    const data = await this.$uploadFile({
                        file: files[i],
                        url: '/common/upload/',
                        fieldName: 'upload',
                        fileName: files[i].name
                    })
                    if(data)
                        this.form.attachments.push(data[0])
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.fileLoading = false
            }
            this.resetFileInput()
        },
        checkLastItem(index) {
            if(this.form.works.length > 1 && this.form.works.length === (index + 1))
                return 'last'
            return ''
        },
        deleteWorkTypes(index) {
            this.form.works.splice(index, 1)
            this.workTypesList.push.splice(index, 1)
        },
        addWorkTypes() {
            this.form.works.push({
                id: Date.now(),
                type1: null,
                work_type: null
            })
            this.workTypesList.push({
                type1: null,
                work_type: null
            })
        },
        formSubmit() {
            this.$refs.formRef.validate(async valid => {
                if (valid) {
                    const queryData = {...this.form}
                    if(queryData.renovation_date)
                        queryData.renovation_date = this.$moment(queryData.renovation_date).format('YYYY-MM-DD')
                    if(queryData.amount)
                        queryData.amount = queryData.amount.toFixed(2)
                    if(queryData.works?.length) {
                        //if(this.edit)
                        //queryData.works = queryData.works.filter(f => !f.disabled)
                        queryData.works = queryData.works.map(item => {
                            if(item.work_type)
                                return {
                                    work_type: item.work_type
                                }
                            return {
                                work_type: item.type1
                            }
                        })
                    }
                    if(queryData.attachments?.length)
                        queryData.attachments = queryData.attachments.map(item => item.id)
                    if(this.edit) {
                        try {
                            this.loading = true
                            const { data } = await this.$http.put(`/sports_facilities/renovation/${queryData.id}/`, queryData)
                            if(data) {
                                eventBus.$emit('repair_list_reload')
                                this.$message.success('Информация о ремонте успешно обновлена')
                                this.visible = false
                            }
                        } catch(e) {
                            console.log(e)
                        } finally {
                            this.loading = false
                        }
                    } else {
                        try {
                            this.loading = true
                            const { data } = await this.$http.post('/sports_facilities/renovation/', queryData)
                            if(data) {
                                eventBus.$emit('repair_list_reload')
                                this.$message.success('Информация о ремонте успешно добавлена')
                                this.visible = false
                            }
                        } catch(e) {
                            console.log(e)
                        } finally {
                            this.loading = false
                        }
                    }
                } else {
                    console.log('error submit!!');
                    return false;
                }
            })
        },
        async getEditData(item) {
            try {
                this.editLoader = true
                const { data } = await this.$http.get(`/sports_facilities/renovation/${item.id}/`)
                if(data) {
                    const editData = data
                    editData.renovation_date = this.$moment(editData.renovation_date)
                    if(editData.renovation_type)
                        editData.renovation_type = editData.renovation_type.code
                    if(editData.amount)
                        editData.amount = Number(editData.amount)
                    if(editData.works?.length) {
                        this.workTypesList = editData.works.map(work => {
                            return {
                                work_type: work.work_type,
                                type1: work.work_type.parent
                            }
                        })
                        editData.works = editData.works.map(work => {
                            return {
                                id: work.id,
                                work_type: work.work_type.code,
                                type1: work.work_type.parent.code,
                                disabled: true
                            }
                        })
                    }
                    if(!editData.attachments?.length)
                        editData.attachments = []
                    this.form = editData
                }
            } catch(e) {
                console.log(e, 'getEditData')
            } finally {
                this.editLoader = false
            }
        }
    },
    mounted(){
        eventBus.$on('add_repair_info', () => {
            this.visible = true
        })
        eventBus.$on('edit_repair_info', data => {
            this.edit = true
            this.visible = true
            this.getEditData(data)
        })
    },
    beforeDestroy() {
        eventBus.$off('add_repair_info')
        eventBus.$off('edit_repair_info')
    }
}
</script>

<style lang="scss" scoped>
.actions_col{
    &.last_act{
        &:not(.first_act){
            @media (max-width: 767px) {
                display: grid;
                gap: 10px;
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }   
        
    }
}
.form_block{
    &::v-deep{
        .ant-form-item{
            @media (max-width: 767px) {
                margin-bottom: 10px;
            }
        }
    }
}
.files_wrap{
    .w_label{
        color: #000;
        opacity: 0.6;
        margin-bottom: 5px;
        line-height: 20px;
    }
}
.filed_row{
    @media (min-width: 992px) {
        display: flex;
        flex-wrap: wrap;
        margin-left: -5px;
        margin-right: -5px;
    }
    .filed_col_1,
    .filed_col_2{
        @media (min-width: 992px) {
            flex: 0 0 auto;
            padding-left: 5px;
            padding-right: 5px;
        }
    }
    .filed_col_1{
        @media (min-width: 992px) {
            width: 85%;
        }
        @media (min-width: 1350px) {
            width: 90%;
        }
        @media (min-width: 1600px) {
            width: 92%;
        }
    }
    .filed_col_2{
        margin-top: 10px;
        @media (min-width: 992px) {
            width: 15%;
            margin-top: 0px;
        }
        @media (min-width: 1350px) {
            width: 10%;
        }
        @media (min-width: 1600px) {
            width: 8%;
        }
    }
    &.last_row{
        .filed_col_1{
            @media (min-width: 992px) {
                width: 77%;
            }
            @media (min-width: 1350px) {
                width: 82%;
            }
            @media (min-width: 1600px) {
                width: 85%;
            }
        }
        .filed_col_2{
            @media (min-width: 992px) {
                width: 23%;
            }
            @media (min-width: 1350px) {
                width: 18%;
            }
            @media (min-width: 1600px) {
                width: 15%;
            }
        }
    }
}
.files_list{
    @media (min-width: 768px) {
        display: flex;
        flex-wrap: wrap;
    }
    .file_card{
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 10px;
        border: 1px solid #D9D9D9;
        border-radius: 4px;
        padding: 10px 15px;
        .file_ico{
            font-size: 28px;
            opacity: 0.6;
        }
        @media (min-width: 768px) {
            margin-right: 10px;
            max-width: 300px;
        }
    }
}
.work_types{
    width: 100%;
    &__item{
        @media (min-width: 992px) {
            display: flex;
            flex-wrap: wrap;
            margin-left: -8px;
            margin-right: -8px;
            align-items: flex-end;
        }
        .col_1{
            @media (min-width: 992px) {
                padding-left: 8px;
                padding-right: 8px;
                width: 50%;
            }
            
        }
    }
    &::v-deep{
        .ant-form-item-label{
            white-space: normal;
            line-height: 24px;
            text-align: left;
        }
    }
    .dym_label{
        @media (min-width: 768px) {
            min-height: 24px;
        }
    }
    ul{
        color: #000;
        padding-left: 15px;
        margin-bottom: 20px;
        li{
            list-style: disc;
            &:not(:last-child){
                margin-bottom: 10px;
            }
        }
        span{
            opacity: 0.6;
        }
    }
}
</style>
