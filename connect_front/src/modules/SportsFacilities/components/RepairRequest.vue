<template>
    <div class="form_block">
        <div class="form_block__label">{{ $t('sports.repairRequest') }}</div>
        <a-form-model
            ref="formRef"
            :model="form"
            :rules="rules">
            <div class="grid gap-4 grid-cols-2">
                <a-form-model-item ref="potreb" :label="$t('sports.needRepair')" prop="potreb">
                    <a-radio-group 
                        v-model="form.potreb" 
                        size="large" 
                        class="w-full flex items-center text-center">
                        <a-radio-button :value="true" class="w-full">
                            {{ $t('sports.yes') }}
                        </a-radio-button>
                        <a-radio-button :value="false" class="w-full">
                            {{ $t('sports.no') }}
                        </a-radio-button>
                    </a-radio-group>
                </a-form-model-item>
                <a-form-model-item ref="price" :label="$t('sports.repairCost')" prop="price">
                    <a-input 
                        v-model="form.price" 
                        size="large" 
                        :placeholder="$t('sports.enterCost')" /> 
                </a-form-model-item>
            </div>
            <a-form-model-item ref="comment" :label="$t('sports.comment')" prop="comment">
                <a-textarea
                    v-model="form.comment"
                    size="large"
                    :placeholder="$t('sports.enterComment')"
                    :auto-size="{ minRows: 5, maxRows: 6 }" />
            </a-form-model-item>
            <a-form-model-item ref="files" prop="files">
                <a-button 
                    type="primary" 
                    size="large" 
                    class="px-7" 
                    :loading="fileLoading" 
                    style="color:#000;" 
                    ghost 
                    @click="triggerFileDialog">
                    {{ $t('sports.attachFiles') }}
                </a-button>
                <input
                    type="file"
                    ref="repairFiles2"
                    multiple
                    style="display: none"
                    @change="handleFileChange" />
                <div v-if="form.files.length" class="files_wrap mt-3">
                    <div class="w_label">Прикреплённые файлы</div>
                    <div class="files_list">
                        <div v-for="(file, index) in form.files" :key="file.id" class="file_card truncate">
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
            <div class="form_actions">
                <a-dropdown>
                    <a-button 
                        block 
                        class="act_btn"
                        size="large" 
                        type="primary">
                        {{ $t('sports.toReview') }}
                        <i class="fi fi-rr-menu-dots-vertical" />
                    </a-button>
                    <a-menu slot="overlay">
                        <a-menu-item>
                            <a href="javascript:;">1st menu item</a>
                        </a-menu-item>
                        <a-menu-item>
                            <a href="javascript:;">2nd menu item</a>
                        </a-menu-item>
                    </a-menu>
                </a-dropdown>
                <a-button type="primary" size="large" ghost block :loading="loading" @click="formSubmit()">
                    {{ $t('sports.saveChanges') }}
                </a-button>
            </div>
        </a-form-model>
    </div>
</template>

<script>
export default {
    data() {
        return {
            loading: false,
            fileLoading: false,
            rules: {
                potreb: [
                    { required: true, message: this.$t('sports.formError'), trigger: 'blur' }
                ],
                price: [
                    { required: true, message: this.$t('sports.formError'), trigger: 'blur' }
                ],
                comment: [
                    { required: true, message: this.$t('sports.formError'), trigger: 'blur' }
                ]
            },
            form: {
                potreb: true,
                price: "",
                comment: "",
                files: []
            }
        }
    },
    methods: {
        deleteFile(index) {
            this.form.files.splice(index, 1)
        },
        triggerFileDialog() {
            this.$refs.repairFiles2.click()
        },
        resetFileInput() {
            this.$refs.repairFiles2.value = null
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
                        this.form.files.push(data[0])
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.fileLoading = false
            }
            this.resetFileInput()
        },
        formSubmit() {
            this.$refs.formRef.validate(valid => {
                if (valid) {
                    alert('submit!');
                } else {
                    console.log('error submit!!');
                    return false;
                }
            })
        }
    }
}
</script>

<style lang="scss" scoped>
@import "../assets/style.scss";
.form_block{
    margin-top: 20px;
}
.files_wrap{
    .w_label{
        color: #000;
        opacity: 0.6;
        margin-bottom: 5px;
        line-height: 20px;
    }
}
.files_list{
    display: flex;
    flex-wrap: wrap;
    .file_card{
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-right: 10px;
        margin-bottom: 10px;
        border: 1px solid #D9D9D9;
        border-radius: 4px;
        padding: 10px 15px;
        max-width: 300px;
        .file_ico{
            font-size: 28px;
            opacity: 0.6;
        }
    }
}
.form_actions{
    display: grid;
    grid-template-columns: 204px 1fr;
    gap: 1rem;
    &::v-deep{
        .act_btn{
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
    }
}
</style>
