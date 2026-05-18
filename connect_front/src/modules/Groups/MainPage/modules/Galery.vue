<template>
    <div ref="groupLightWrap">
        <!-- Галерея -->
        <a-card
            v-if="isStudent"
            :title="isMobile ? false : $t('wgr.gallery')"
            size="small"
            class="lg:mt-base"
            :class="isMobile ? 'galery_card_mobile' : 'mt-6'">
            <a-row 
                type="flex" 
                :gutter="6" 
                v-if="galeryImages.length > 0">
                <a-col
                    :span="8"
                    v-for="(img, index) in galeryImages"
                    :key="index">
                    <a 
                        v-if="index < 9" 
                        :href="img.path"
                        class="gp_lgth"
                        :title="img.name">
                        <img
                            :src="img.path"
                            :alt="img.name"
                            style="
                                        max-height: 60px;
                                        object-fit: contain;
                                        cursor: pointer;
                                    "
                            class="rounded mb-4 user-latest-image responsive"/>
                    </a>
                </a-col>
            </a-row>
            <div 
                v-else
                class="flex items-center justify-center -mt-2 mb-2" >
                <a-empty :description="$t('wgr.image_not_found')" />
            </div>
            <a-button
                v-if="isFounder"
                type="dashed"
                icon="upload"
                class="mt-2 w-full"
                @click="activeAddGalery = true">
                {{ $t("wgr.add_image") }}
            </a-button>
        </a-card>

        <!--<a-modal
            :title="$t('wgr.gallery')"
            width="800px"
            forceRender
            :zIndex="1010"
            :footer="null"
            @cancel="activeGalery = false"
            :visible="activeGalery">
            <div >

                <swiper
                    :options="swiperOptionTop"
                    class="gallery-top"
                    ref="mySwiper">
                    <swiper-slide
                        v-for="item in galeryImages"
                        :key="item.id">
                      
                        <img
                            class="responsive swiper-lazy"
                            style="max-height: 80vh; object-fit: contain"

                            :data-src="item.path"
                            :alt="item.name"/>
                        <div class="swiper-lazy-preloader swiper-lazy-preloader-white"></div>
                        <a-popconfirm :title="$t('wgr.delete_image')+'?'"
                                      :ok-text="$t('wgr.yes')"  @confirm="deleteImageInGalery(item)" 
                                      :cancel-text="$t('wgr.no')">
                            <a-button
                                v-if="isFounder"
                                type="danger"
                                icon="close"
                                class="btn-delete-galery"></a-button>
                        </a-popconfirm>
                    </swiper-slide>

                    <div
                        class="swiper-button-next swiper-button-white"
                        slot="button-next"></div>
                    <div
                        class="swiper-button-prev swiper-button-white"
                        slot="button-prev"></div>
                </swiper>

            </div>
        </a-modal>-->

        <!-- Загрузить галерею -->
        <a-modal 
            :title="$t('wgr.add_image')" 
            :zIndex="1010"
            :cancelText="$t('wgr.cancel')"
            :okText="$t('wgr.upload_file')" 
            @cancel="activeAddGalery = false" 
            @ok="postImageGalery" 
            :visible="activeAddGalery">
            <Upload 
                v-model="uploadImages" 
                drag 
                listType="picture" 
                multiple 
                :limit="10" />
        </a-modal>
    </div>
</template>

<script>
import {mapActions, mapGetters} from 'vuex'
import Upload from '@apps/Upload'
import 'swiper/css/swiper.css'
export default {
    name: "GroupsAndProjectGalery",
    components: {
        Upload
    },
    created() {
        if(this.id !== 0)
            this.getGalery()
    },
    watch: {
        id(val){
            if(val !== 0)
                this.getGalery()
        }
    },
    data() {
        return {
            uploadImages: [],
            galeryImages: [],
            filesGalery: [],
            activeTab: "1",
            activeGalery: false,
            activeAddGalery: false,


            swiperOptionTop: {
                spaceBetween: 10,
                navigation: {
                    nextEl: ".swiper-button-next",
                    prevEl: ".swiper-button-prev",
                },
                lazy: true,
                loop: true

            },
            swiperOptionThumbs: {
                spaceBetween: 10,
                centeredSlides: true,
                slidesPerView: "auto",
                touchRatio: 0.2,
                slideToClickedSlide: true,
            },
        };
    },
    props: {
        isFounder: {
            type: Boolean,
            required: true
        },
        isStudent: {
            type: Boolean,
            required: true
        },
        id: {
            type: [String, Number],
            default: null
        }
    },
    computed:{
        ...mapGetters({
            requestData : "workgroups/info"
        }),
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    methods: {
        ...mapActions({
           
            postGalery: "workgroups/postImageGalery",
            getGaleryS: "workgroups/getGalery",
            deleteImageGalery: "workgroups/deleteImageGalery",
            

        }),
        // Добавление изображений галереии
        async postImageGalery() {
            try{
                const res = await this.postGalery({id: this.id, files: this.uploadImages})
                this.galeryImages = res.gallery_files;
                this.uploadImages = []
                this.activeAddGalery = false;
                this.initLightgallery()
            }
            catch(error){
                this.$message.error(this.$t('wgr.error') + error)
            }
        },
        // Открыть галерею
        openGalery(index){
            this.$refs.mySwiper.$swiper.slideTo(index+1, 0)
            this.activeGalery = true
        },

        // ПОлучить изображеиня галереии
        async getGalery() {
            try {
                const res = await this.getGaleryS(this.id)
                this.galeryImages = res.gallery_files;
                this.initLightgallery()
            } catch(e) {
                console.log(e)
            }
        },
        initLightgallery() {
            if(this.galeryImages?.length) {
                this.$nextTick(() => {
                    const lightboxWrap = this.$refs[`groupLightWrap`],
                        lightbox = lightboxWrap.querySelectorAll('.gp_lgth')

                    if(lightbox?.length) {
                        lightGallery(lightboxWrap, {
                            selector: ".gp_lgth",
                            thumbnail: true,
                            animateThumb: true,
                            rotateLeft: true,
                            rotateRight: true,
                            flipHorizontal: false,
                            flipVertical: false,
                            fullScreen: true,
                            showThumbByDefault: true,
                            download: true,
                            speed: 300
                        })
                    }
                })
            }
        },
        // Удлаить изображение из галереии
        async deleteImageInGalery(item) {
            try{
                this.loading = true
                let files = [item.id]
                const res = await this.deleteImageGalery({id: this.id, files})

                this.galeryImages = res.gallery_files;
                if(res.gallery_files.length > 0){
                    this.$refs.mySwiper.$swiper.slideTo(0, 0)
                } else {
                    this.activeGalery = false
                }
                this.initLightgallery()
            }
            catch(error){
                this.$message.error(this.$t('wgr.error') + error)
            }
            finally{
                this.loading = false
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.gallery-thumbs {
    height: 20% !important;
    box-sizing: border-box;
    padding: 10px 0;
}
.gallery-thumbs .swiper-slide {
    width: 25%;
    height: 100%;
    opacity: 0.4;
}
.gallery-thumbs .swiper-slide-active {
    opacity: 1;
}
.gallery-top {
    height: 80% !important;
    width: 100%;
}
.btn-delete-galery{
    position: absolute;
    top: 15px;
     right: 15px;
      z-index: 10;
}
.swiper-slide{
    display: flex;
    align-items: center;
    justify-content: center;
}
.swiper-button-next,
.swiper-button-prev {
    /* background-color: white; */
    /* background-color: rgba(255, 255, 255, 0.5); */
    right:10px;
    padding: 30px;
    color: #000 !important;
    fill: black !important;
    stroke: black !important;
}
</style>

<style lang="scss">
.galery_card_mobile {
    border: none;
    .ant-card-head {
        padding: 0;
        border: none;
    }
    .ant-card-body {
        padding: 0;
    }
}
</style>