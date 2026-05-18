<template>
    <div>
        <div v-if="!croper">

            <!-- Main upload -->
            <a-upload
                v-if="!drag"
                name="upload"
                :multiple="multiple"

                :withCredentials="true"
                :headers="{
                    'X-CSRFToken': $cookies.get('csrftoken')
                }"

                :file-list="fileList"
                :listType="listType"
                :showUploadList="showUploadList"
                @change="handleChange"
                @preview="handlePreview"
                :disabled="disabled"
                :beforeUpload="handleUploadButton"
                :customRequest="customUploadRequest">
                <a-button :disabled="disabled"> <a-icon type="upload" /> {{ buttonText ==="" ? 'Загрузить файл' : buttonText }} </a-button>
            </a-upload>
            <!-- Drag and drop -->
            <a-upload-dragger
                v-if="drag"
                name="upload"
                :multiple="multiple"
                :file-list="fileList"
                :listType="listType"
                :showUploadList="showUploadList"
                @change="handleChange"
                @preview="handlePreview"
                :disabled="disabled"
                :beforeUpload="handleUploadButton"
                :customRequest="customUploadRequest">

                <p class="ant-upload-drag-icon">
                    <a-icon type="inbox" />
                </p>
                <p class="ant-upload-text">
                    {{ $t('upload.drag_file') }}
                </p>

            </a-upload-dragger>
            <!-- Модалка preview -->
            <a-modal :visible="previewVisible" :footer="null" @cancel="handleCancel">
                <img   style="width: 100%" :src="previewImage" />
            </a-modal>

        </div>

        <div v-else class="flex items-center">
            <label for="avatar_upload">
                <slot name="button">
                    <a-avatar :src="imageAvatar" :key="imageAvatar" :size="80" flaticon icon="fi-rr-users-alt"></a-avatar>
                    <div class="flex items-center">
                        <div class="ant-btn flex items-center ml-4">
                            <span>{{ buttonText ==="" ? 'Загрузить файл' : buttonText }}</span>
                        </div>
                    </div>
                </slot>
            </label>
            <input

                type="file"
                id="avatar_upload"
                style="display:none;"
                ref="avatarUpload"
                v-on:change="handleFileChange"
                accept=".jpg, .jpeg, .png, .gif" />

        </div>

        <a-drawer
            title=""
            :placement="isMobile ? 'bottom' : 'right'"
            :width="cropDrawerWidth"
            :zIndex="99999"
            destroyOnClose
            class="cropper_modal"
            :visible="cropModal"
            @close="closeCropModal()">
            <div class="cr_d_body">
                <div v-if="dataUrl" class="relative h-full">
                    <img
                        ref="avatarImg"
                        @load.stop="createCropper"
                        :src="dataUrl" />

                    <div class="action_btn flex items-center">
                        <a-button 
                            type="ui"
                            icon="fi-rr-rotate-left" 
                            flaticon
                            shape="circle"
                            @click="cropper.rotate(-45)" />
                        <a-button 
                            type="ui"
                            class="ml-1" 
                            flaticon
                            shape="circle"
                            icon="fi-rr-rotate-right"
                            @click="cropper.rotate(45)"  />
                    </div>
                </div>
            </div>
            <div class="cr_d_footer">
                <a-button type="primary" size="large" block @click="uploadImage()" class="mb-2" :loading="uploadLoading">
                    Загрузить
                </a-button>
                <a-button type="ui" ghost block size="large" @click="closeCropModal()">
                    {{$t('close')}}
                </a-button>
            </div>
        </a-drawer>
    </div>
</template>

<script>
import 'cropperjs/dist/cropper.css'
import Cropper from 'cropperjs'
import { checkImageWidthHeight, hashString, getFileExtension } from './utils'
import { mapState } from 'vuex'
export default {
    name: 'Upload',
    props: {
        value: [String, Array, Number, Object],

        // Дефолтный лист для вставки файлов в upload
        // Пример добавление файла в fileList

        //  this.fileList.push({
        //         uid: res.club_logo.id,
        //         name: res.club_logo.name,
        //         status: 'done',
        //         url: res.club_logo.path
        //     })

        defaultList: [String, Object, Array],

        // Режим Drag & Drop
        drag: {
            type: Boolean,
            default: false
        },
        // Текст кнопки загрузки файлов
        buttonText: {
            type: String,
            default: ""
        },
        // Эндпоинт
        action: {
            type: String,
            default: "/common/upload/"
        },
        // Скрыть лист с файлами
        showUploadList: {
            type: Boolean,
            default: true
        },
        // Макс кол-во файлов (если multiple true)
        limit: {
            type: Number,
            default: 5
        },
        // Загрузка нескольких файлов
        multiple: {
            type: Boolean,
            default: false
        },
        croper: {
            type: Boolean,
            default: false
        },
        // Вид списка
        listType:{
            type: String,
            default: 'text'
        },

        disabled: {
            type: Boolean,
            default: false
        },
        // Минимальная ширина для кропера
        minWidth: {
            type: [Number, String],
            default: "150"
        },
        returnArray:{
            type: Boolean,
            default: true
        },
        // Минимальная высота для кропера
        minHeight: {
            type: [Number, String],
            default: "150"
        },
        objectType: {
            type: Boolean,
            default: false
        }
    },
    data(){
        return{
            fileList: [],
            minSize: 100,
            previewVisible: false,
            previewImage: null,
            avatarLoader: false,
            cropModal: false,
            uploadLoading: false,
            deleteLoader: false,
            imageAvatar: "",
            dataUrl: "",
            file: null,
            cropperOptions: {
                aspectRatio: 1 / 1,
                minCropBoxWidth: 100,
                minCropBoxHeight: 100
            }
        }
    },
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth
        }),
        cropDrawerWidth() {
            if(this.windowWidth > 500)
                return 400
            else
                return this.windowWidth
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    watch: {
        defaultList(){
            if(this.defaultList){
                if(this.croper){
                    this.imageAvatar = this.defaultList
                }

            }
        }
    },
    created() {
        if(!this.croper){
            this.fileList = this.defaultList;
        }

    },

    methods:{
        async customUploadRequest({ file, onProgress, onSuccess, onError }) {
            try {
                const data = await this.$uploadFile({
                    file,
                    url: this.action,
                    fieldName: 'upload',
                    fileName: file.name,
                    onProgress
                })
                onSuccess(data)
            } catch (error) {
                onError(error)
            }
        },
        uploadImage() {
            this.cropper.getCroppedCanvas().toBlob(async (avatar) => {
                try {
                    const exc = getFileExtension(this.file.name),
                        filename = `${hashString(this.file.name)}.${exc}`

                    this.uploadLoading = true
                    const data = await this.$uploadFile({
                        file: avatar,
                        url: this.action,
                        fieldName: 'upload',
                        fileName: filename
                    })
                    if(data) {
                        // const res = await this.$store.dispatch('user/userUpdateAvatar', {
                        //     avatar: data[0].id
                        // })
                        // if(res) {
                        //     this.$message.success(this.$t('success_avatar'))
                        //
                        // }
                        // console.log("data", data)
                        if (this.objectType) {
                            this.$emit("input", data[0]);
                        } else {
                            this.$emit("input", data[0].id);
                        }
                        this.imageAvatar = data[0].path
                        this.closeCropModal()
                    }
                } catch(e) {
                    this.$message.error(this.$t('upload.error'))
                } finally {
                    this.uploadLoading = false
                }
            })
        },
        closeCropModal() {
            this.cropModal = false
            this.dataUrl = null
            this.file = null
        },
        createCropper() {
            this.cropper = new Cropper(this.$refs.avatarImg, this.cropperOptions)
        },
        async handleFileChange(event) {
            const file = Object.values(event.target.files)[0]
            if(file) {
                const fileSize = await checkImageWidthHeight(file)
                if(fileSize.width > this.minSize && fileSize.height > this.minSize) {
                    let reader = new FileReader()
                    reader.onload = e => {
                        this.dataUrl = e.target.result
                    }
                    reader.readAsDataURL(file)
                    this.file = file
                    this.cropModal = true
                } else
                    this.$message.error(this.$t('upload.max_file_h_w', {size: this.minSize}))
            }
        },





        // IN Type picture
        handleCancel() {
            this.previewVisible = false;
            this.previewImage = null;
        },
        async handlePreview(file) {
            this.previewImage = file.response[0].path;
            this.previewVisible = true;
        },

        handleUploadButton(){
            if(!this.multiple){
                this.fileList = [];
            }
        },
        handleChange(info) {
            try{

                let fileList = [...info.fileList];
                fileList = fileList.slice(- this.limit);


                fileList = fileList.map(file => {
                    if (file.response) {
                        file.id = file.response[0].id
                    }
                    return file;
                });

                this.fileList = fileList;


                let res;
                if(fileList.length > 1){
                    res = fileList.map(el=>{
                        return el.id ? el.id : el.uid
                    })
                } else {
                    res = fileList[0].id ? fileList[0].id : fileList[0].uid
                }


                if (info.file.status === 'done') {
                    this.$message.success(`${info.file.name} файл успешно загружен.`);
                }
                let results;
                if(this.returnArray){
                    if(!Array.isArray(res)){
                        results = [res]
                    } else
                        results = res
                } else {
                    results = res
                }

                this.$emit("input",  results);


            }
            catch{
                this.$message.error(`${info.file.name} ошибка при загрузки файла.`);
            }

        },
    }
}
</script>

<style scoped lang="scss">
.cropper_modal{
    &::v-deep{
        .ant-drawer-wrapper-body,
        .ant-drawer-content{
            overflow: hidden;
        }
        .ant-drawer-content-wrapper{
            height: 100%!important;
        }
        .ant-drawer-header-no-title{
            display: none;
        }
        .ant-drawer-body{
            height: 100%;
            padding: 0px;
        }
        .cr_d_body{
            height: calc(100% - 100px);
        }
        .action_btn{
            position: absolute;
            bottom: 10px;
            right: 15px;
        }
        .cr_d_footer{
            height: 100px;
            border-top: 1px solid var(--border1);
            padding: 5px 15px;
        }
    }
}
</style>
