<template>
    <div>
        <div class="mb-4" :class="!isMobile && 'flex items-center'">
            <a-button 
                v-if="isAuthor" 
                type="primary" 
                icon="plus"
                :class="!isMobile ? 'mr-4' : 'mb-2'"
                :block="isMobile"
                size="large"
                @click="triggerFileDialog">
                {{ $t('gallery.addGalleryPhoto') }}
            </a-button>
            <input
                type="file"
                ref="fileInput"
                multiple
                accept=".jpg,.jpeg,.gif,.png"
                style="display: none"
                @change="handleFileChange" />
            <div v-if="count" style="color:#000;">
                {{ $t('gallery.photo_count', { count }) }}
            </div>
        </div>
        <a-empty v-if="empty" description="Галерея пуста" />
        <div ref="g_lght_wrap" class="grid gap-4 grid-cols-1 xl:grid-cols-2 2xl:grid-cols-3">
            <div v-for="item in results" :key="item.id" class="file_card">
                <div class="card_actions">
                    <a-button 
                        v-if="useMainPhoto && item.is_main"
                        type="primary" 
                        flaticon 
                        v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }"
                        :content="$t('gallery.main_photo')"
                        class="mr-1"
                        icon="fi-rr-heart" />
                    <template v-if="isAuthor">
                        <a-button 
                            type="text" 
                            flaticon 
                            v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }"
                            :content="$t('gallery.edit')"
                            icon="fi-rr-edit"
                            @click="editGalleryFile(item)" />
                        <a-button 
                            type="text" 
                            flaticon 
                            v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }"
                            :content="$t('gallery.delete')"
                            class="ml-1"
                            icon="fi-rr-trash"
                            @click="deleteGalleryFile(item)" />
                    </template>
                </div>
                <a :href="item.path" target="_blank" :data-sub-html="item.description" :data-thumb="item.path" class="file_card_wrap g_lht_l">
                    <img 
                        :data-src="item.path" 
                        :alt="item.name" 
                        class="lazyload" />
                </a>
            </div>
        </div>
        <!--<infinite-loading
            ref="gallery_infinity"
            @infinite="getGallery"
            v-bind:distance="10">
            <div
                slot="spinner"
                class="flex items-center justify-center inf_spinner">
                <a-spin />
            </div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>-->
        <a-drawer
            v-if="isAuthor"
            :title="$t('gallery.addGalleryPhoto')"
            placement="right"
            :width="drawerWidth"
            :visible="visible"
            destroyOnClose
            :after-visible-change="afterVisibleChange"
            @close="visible = false">
            <div class="iu_list">
                <div v-for="(file, index) in uploadedFiles" :key="index" class="iu_list__item w-full">
                    <div class="img_block">
                        <div class="img_wrap">
                            <img 
                                :src="file.preview" 
                                :alt="file.name" />
                        </div>
                    </div>
                    <div class="md:ml-4 grow w-full">
                        <div class="flex items-center mb-2">
                            <a-input 
                                v-model="file.description" 
                                :placeholder="$t('gallery.description')" 
                                :maxLength="255"
                                size="large" />
                            <a-button 
                                type="danger" 
                                size="large"
                                class="ml-2"
                                ghost
                                flaticon
                                icon="fi-rr-trash"
                                @click="deleteFile(index)" />
                        </div>
                        <a-checkbox 
                            v-if="useMainPhoto"
                            v-model="file.is_main" 
                            @change="mainChange(index)">
                            {{ $t('gallery.setMainPhoto') }}
                        </a-checkbox>
                    </div>
                </div>
            </div>
            <div class="mt-3">
                <a-button type="link" :block="isMobile" icon="plus" @click="triggerFileDialog">
                    {{ $t('gallery.addPhoto') }}
                </a-button>
            </div>
            <div class="grid gap-2 md:gap-4 grid-cols-1 md:grid-cols-2 mt-4">
                <a-button 
                    type="primary" 
                    :loading="saveLoading" 
                    size="large" 
                    block 
                    @click="saveFiles()">
                    {{ $t('gallery.save') }}
                </a-button>
                <a-button size="large" block @click="visible = false">
                    {{ $t('gallery.cancel') }}
                </a-button>
            </div>
        </a-drawer>
        <a-modal
            v-if="isAuthor"
            :title="$t('gallery.edit')"
            :visible="modalVisible"
            destroyOnClose
            :footer="false"
            :afterClose="afterEditClose"
            @cancel="modalVisible = false">
            <a-form-model
                ref="editGalleryForm"
                :model="editItem">
                <a-form-model-item ref="description" :label="$t('gallery.description')" prop="description">
                    <a-textarea
                        v-model="editItem.description"
                        size="large"
                        :maxLength="255"
                        :placeholder="$t('gallery.description')"
                        :auto-size="{ minRows: 3, maxRows: 5 }"/>
                </a-form-model-item>
                <a-form-model-item v-if="useMainPhoto" ref="is_main" prop="is_main">
                    <a-checkbox v-model="editItem.is_main">
                        {{ $t('gallery.setMainPhoto') }}
                    </a-checkbox>
                </a-form-model-item>
                <a-button type="primary" size="large" :loading="editLoading" block @click="formSubmit()">
                    {{ $t('gallery.save') }}
                </a-button>
                <a-button type="ui" class="mt-2" size="large" block @click="modalVisible = false">
                    {{ $t('gallery.close') }}
                </a-button>
            </a-form-model>
        </a-modal>
    </div>
</template>

<script>
//import InfiniteLoading from 'vue-infinite-loading'
import { mapState } from 'vuex'
export default {
    props: {
        sourceId: {
            type: String,
            required: true
        },
        useMainPhoto: {
            type: Boolean,
            default: true
        },
        isAuthor: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            count: 0,
            next: true,
            results: [],
            loading: false,
            saveLoading: false,
            page: 0,
            empty: false,
            uploadedFiles: [],
            visible: false,
            lightboxInstance: null,
            modalVisible: false,
            editLoading: false,
            editItem: {
                is_main: false,
                description: ""
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
            if(this.windowWidth > 978)
                return 978
            else {
                return '100%'
            }
        }
    },
    created() {
        this.getGallery()
    },
    methods: {
        formSubmit() {
            this.$refs.editGalleryForm.validate(async valid => {
                if (valid) {
                    try {
                        this.editLoading = true
                        const { data } = await this.$http.put(`/gallery/${this.editItem.id}/?related_object=${this.sourceId}`, this.editItem)
                        if(data) {
                            this.$message.success(this.$t('gallery.fileUpdated'))
                            this.modalVisible = false
                            this.listReload()
                        }
                    } catch(e) {
                        console.log(e)
                    } finally {
                        this.editLoading = false
                    }
                } else {
                    console.log('error submit!!');
                    return false;
                }
            })
        },
        afterEditClose() {
            this.editItem = {
                is_main: false,
                description: ""
            }
        },
        editGalleryFile(item) {
            this.editItem = item
            this.modalVisible = true
            console.log(item, 'item')
        },
        deleteGalleryFile(item) {
            this.$confirm({
                title: this.$t('gallery.deleteMessage'),
                content: '',
                okText: this.$t('gallery.delete2'),
                okType: 'danger',
                zIndex: 2000,
                closable: true,
                maskClosable: true,
                cancelText: this.$t('gallery.close'),
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.delete(`/gallery/${item.id}/`, {
                            params: {
                                related_object: this.sourceId
                            }
                        })
                            .then(() => {
                                this.$message.success(this.$t('gallery.fileDeleted'))
                                this.listReload()
                                resolve()
                            })
                            .catch(e => {
                                console.log(e)
                                this.$message.error(this.$t('gallery.deletedError'))
                                reject(e)
                            })
                    })
                }
            })
        },
        async saveFiles() {
            try {
                this.saveLoading = true
                for(const i in this.uploadedFiles) {
                    const data = await this.$uploadFile({
                        file: this.uploadedFiles[i].file,
                        url: '/common/upload/',
                        fieldName: 'upload',
                        fileName: this.uploadedFiles[i].name
                    })
                    if(data?.length) {
                        this.uploadedFiles[i].file = data[0]
                    }
                    await this.$http.post('/gallery/', {
                        ...this.uploadedFiles[i],
                        file: this.uploadedFiles[i].file.id,
                        related_object: this.sourceId
                    })
                }
                this.$message.success(this.$t('gallery.fileLoadSuccess'))
                this.visible = false
                this.listReload()
            } catch(error) {
                console.error(error); // Лог ошибки для отладки
        
                // Проверяем, есть ли ответ сервера с описанием ошибки
                if (error.response?.data?.description) {
                    const descriptions = error.response.data.description;
                    // Если это массив, выводим все ошибки в одной строке
                    if (Array.isArray(descriptions)) {
                        this.$message.error(descriptions.join('; '));
                    } else {
                        this.$message.error(descriptions);
                    }
                } else {
                    // Универсальное сообщение, если нет данных об ошибке
                    this.$message.error(this.$t('gallery.fileLoadError'));
                }
            } finally {
                this.saveLoading = false
            }
        },
        deleteFile(index) {
            this.uploadedFiles.splice(index, 1)
            if(!this.uploadedFiles.length) {
                this.visible = false
            }
        },
        mainChange(fIndex) {
            this.uploadedFiles.forEach((file, index) => {
                if(index !== fIndex)
                    this.uploadedFiles[index].is_main = false
            })
        },
        afterVisibleChange(vis) {
            if(!vis) {
                this.uploadedFiles = []
            }
        },
        triggerFileDialog() {
            this.$refs.fileInput.click()
        },
        handleFileChange(event, open = true) {
            const files = Array.from(event.target.files)
                .filter((file) => file.type.startsWith("image/"))
                .map((file) => ({
                    file,
                    preview: URL.createObjectURL(file),
                    name: file.name,
                    is_main: false,
                    description: ""
                }))
            this.uploadedFiles = this.uploadedFiles.concat(files)
            if(open)
                this.visible = true
            this.resetFileInput()
        },
        resetFileInput() {
            this.$refs.fileInput.value = null
        },
        async getGallery() {
            try {
                this.loading = true
                //this.page += 1
                let params = {
                    //page: this.page,
                    page_size: 9,
                    related_object: this.sourceId
                }
                const { data } = await this.$http.get('/gallery/', {
                    params
                })
                if(data) {
                    this.count = data.length
                    this.results = this.results.concat(data)
                }
                if(this.page === 1 && !this.results.length)
                    this.empty = true

                this.lightboxInit()
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        },
        lightboxInit() {
            this.$nextTick(() => {
                const lightboxWrap = this.$refs[`g_lght_wrap`],
                    lightbox = lightboxWrap.querySelectorAll('.g_lht_l')
                if(lightbox?.length) {
                    if(window.lgData[lightboxWrap.getAttribute('lg-uid')]) {
                        console.log(1)
                        window.lgData[lightboxWrap.getAttribute('lg-uid')].destroy(true)
                    }
                    lightGallery(lightboxWrap, {
                        selector: ".g_lht_l",
                        thumbnail: true,
                        rotateLeft: true,
                        rotateRight: true,
                        flipHorizontal: false,
                        flipVertical: false,
                        fullScreen: true,
                        animateThumb: true,
                        showThumbByDefault: false,
                        download: true,
                        speed: 300
                    })
                }
            })
        },
        /*async getGallery($state) {
            if(!this.loading && this.next) {
                try {
                    this.loading = true
                    this.page += 1
                    let params = {
                        page: this.page,
                        page_size: 9,
                        related_object: this.sourceId
                    }
                    const { data } = await this.$http.get('/gallery/', {
                        params
                    })
                    if(data) {
                        this.count = data.count
                        this.next = data.next
                    }
                    if(data?.results?.length)
                        this.results = this.results.concat(data.results)
                    if(this.page === 1 && !this.results.length)
                        this.empty = true
                    if(this.next)
                        $state.loaded()
                    else
                        $state.complete()
                } catch(e) {
                    console.log(e)
                } finally {
                    this.loading = false
                }
            }
        },*/
        listReload() {
            this.page = 0
            this.empty = false
            this.results = []
            this.next = true
            this.count = 0
            this.getGallery()
            /*this.$nextTick(() => {
                this.$refs['gallery_infinity'].stateChanger.reset()
            })*/
        }
    }
}
</script>

<style lang="scss" scoped>
.iu_list{
    &__item{
        border-bottom: 1px solid #E8E8E8;
        padding-bottom: 20px;
        @media (min-width: 992px) {
            display: flex;
            align-items: center;
            flex-direction: row;
            padding-bottom: 25px;
        }
        &:not(:last-child){
            margin-bottom: 20px;
            @media (min-width: 992px) {
                margin-bottom: 25px;
            }
        }
    }
    .img_block{
        width: 100%;
        height: 200px;
        overflow: hidden;
        position: relative;
        border-radius: 4px;
        margin-bottom: 15px;
        @media (min-width: 992px) {
            width: 145px;
            height: 80px;
            margin-bottom: 0px;
        }
        .img_wrap{
            background: rgba(0, 0, 0, .1);
            height: 100%;
            left: 0;
            margin: 0;
            overflow: hidden;
            position: absolute;
            top: 0;
            width: 100%;
            img{
                object-fit: cover;
                -o-object-fit: cover;
                vertical-align: middle;
                width: 100%;
            }
        }
    }
}
.file_card{
    overflow: hidden;
    position: relative;
    padding-bottom: 54.1%;
    width: 100%;
    .card_actions{
        position: absolute;
        top: 10px;
        right: 10px;
        z-index: 5;
        display: flex;
        align-items: center;
        &::v-deep{
            .ant-btn{
                &:not(.ant-btn-primary){
                    background-color: #F5F5F5;
                }
                border: 0px;
            }
        }
    }
    .file_card_wrap{
        height: 100%;
        left: 0;
        margin: 0;
        overflow: hidden;
        position: absolute;
        top: 0;
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid #EBEBEB;
        img{
            object-fit: contain;
            vertical-align: middle;
            -o-object-fit: contain;
            max-height: 100%;
            border-style: none;
            opacity: 0;
            transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
            &.lazyloaded{
                opacity: 1;
            }
        }
    }
}
</style>
