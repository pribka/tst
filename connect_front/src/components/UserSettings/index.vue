<template>
    <DrawerTemplate
        :title="$t('profile')"
        v-model="visible"
        :width="windowWidth > 1500 ? 1500 : '100%'"
        class="profile_drawer"
        @afterVisibleChange="afterVisibleChange"
        :destroyOnClose="true"
        @close="visible = false">
        <div 
            v-if="loading" 
            class="flex justify-center pt-5">
            <a-spin />
        </div>
        <div 
            v-else 
            :class="!isMobile && 'grid drawer_body'">
            <div v-if="!isMobile" class="profile_menu">
                <template v-if="profileMenu.length">
                    <div 
                        v-if="user" 
                        class="user_info text-center mb-5">
                        <div :key="avatarReload" class="flex justify-center relative">
                            <div>
                                <label for="avatar_upload" class="cursor-pointer">
                                    <a-avatar 
                                        :size="100" 
                                        :src="user.avatar && user.avatar.path"
                                        icon="user" />
                                </label>
                                <a-dropdown :trigger="['click']" :getPopupContainer="trigger => trigger.parentNode">
                                    <div class="avatar_edit__icon">
                                        <div class="ant-btn ant-btn-icon-only flex items-center justify-center ant-btn-circle">
                                            <i class="fi fi-rr-menu-dots-vertical" />
                                        </div>
                                    </div>
                                    <a-menu slot="overlay" @click="onAvatarMenuClick">
                                        <a-menu-item key="upload" class="flex items-center">
                                            <i class="fi fi-rr-cloud-upload-alt mr-2" />
                                            {{ $t('upload_avatar') }}
                                        </a-menu-item>
                                        <a-menu-item v-if="user.avatar && user.avatar.path" key="delete" class="flex items-center" @click="deleteAvatar()">
                                            <i class="fi fi-rr-trash mr-2" />
                                            {{ $t('delete_avatar') }}
                                        </a-menu-item>
                                    </a-menu>
                                </a-dropdown>
                            </div>
                            <input
                                type="file"
                                id="avatar_upload"
                                style="display:none;"
                                ref="avatarUpload"
                                v-on:change="handleFileChange"
                                accept=".jpg, .jpeg, .png, .gif" />
                      
                        </div>
                        <div class="username mt-3 font-semibold text-xl">
                            {{ userName }}
                        </div>
                        <div 
                            v-if="user.email" 
                            class="user_email font-light">
                            {{ user.email }}
                        </div>
                    </div>
                    <div class="menu">
                        <div 
                            v-for="item in profileMenu" :key="item.path" 
                            class="item truncate select-none"
                            :class="item.path === active && 'active'"
                            @click="selectMenu(item)">
                            <i :class="`fi ${item.icon}`"></i>
                            <span class="truncate whitespace-nowrap">{{ item.name }}</span>
                        </div>
                    </div>
                </template>
            </div>
            <div 
                v-if="activeItem" 
                :key="active" 
                class="profile_content" :class="!isMobile && 'w_scroll'">
                <div class="profile_wrapper" :class="!isMobile && 'w_padding'">
                    <h1>
                        {{ activeItem.name }}
                    </h1>
                    <TabsSwitch :activeItem="activeItem" />
                </div>
            </div>
        </div>
        <template v-if="isMobile" #footer>
            <a-button type="ui_ghost" block size="large" @click="visible = false">
                {{ $t('close') }}
            </a-button>
        </template>
        <DrawerTemplate
            title=""
            :width="cropDrawerWidth"
            destroyOnClose
            class="cropper_modal"
            v-model="cropModal"
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
            <template #footer>
                <div class="w-full">
                    <a-button type="primary" size="large" block @click="uploadImage()" class="mb-2" :loading="uploadLoading">
                        {{ $t('upload.upload') }}
                    </a-button>
                    <a-button type="ui" ghost block size="large" @click="closeCropModal()">
                        {{$t('close')}}
                    </a-button>
                </div>
            </template>
        </DrawerTemplate>
    </DrawerTemplate>
</template>

<script>
import { mapState } from 'vuex'
import {checkImageWidthHeight, hashString, getFileExtension} from '@/utils/utils'
import 'cropperjs/dist/cropper.css'
import Cropper from 'cropperjs'
import { errorHandler } from '@/utils/index.js'
export default {
    name: 'UserSettings',
    components: {
        TabsSwitch: () => import('./Tabs/TabsSwitch.vue'),
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue')
    },
    computed: {
        ...mapState({ 
            user: state => state.user.user,
            profileMenu: state => state.user.profileMenu,
            windowWidth: state => state.windowWidth,
            isMobile: state => state.isMobile
        }),
        cropDrawerWidth() {
            if(this.windowWidth > 500)
                return 500
            else
                return this.windowWidth
        },
        visible: {
            get() {
                return this.$store.state.user.settingVisible
            },
            set(val) {
                this.$store.commit('user/SETTING_DRAWER_TOGGLE', val)
            }
        },
        userName() {
            if(this.user.first_name)
                return `${this.user.first_name} ${this.user.last_name && this.user.last_name.substr(0, 1)}`
            else
                return this.user.username
        },
        activeItem() {
            if(this.active && this.profileMenu?.length) {
                const find = this.profileMenu.find(f => f.path === this.active)
                if(find)
                    return find
                else
                    return null
            } else
                return null
        }
    },
    data() {
        return {
            active: '',
            loading: false,
            cropModal: false,
            uploadLoading: false,
            file: null,
            dataUrl: null,
            minSize: 100,
            avatarLoader: false,
            avatarReload: Date.now(),
            sAvatar: '',
            cropperOptions: {
                viewMode: 1,
                aspectRatio: 1 / 1,
                minCropBoxWidth: 100,
                minCropBoxHeight: 100
            }
        }
    },
    watch: {
        '$route.query'(val) {
            if(val.my_profile && val.my_profile === 'open')
                this.openDrawer()
        }
    },
    created () {
        if(this.$route.query?.my_profile)
            this.openDrawer()
   
    },
    methods: {
        onAvatarMenuClick({ key }) {
            if(key === 'upload')
                this.$refs.avatarUpload.click()
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
                    this.$message.error(this.$t('max_file_h_w', {size: this.minSize}))
            }
        },
        async deleteAvatar() {
            this.$confirm({
                title: this.$t('avatar_delete_message'),
                content: '',
                okText: this.$t('remove'),
                closable: true,
                maskClosable: true,
                cancelText: this.$t('close'),
                onOk: async () => {
                    try {
                        await this.$http.post('users/change_avatar/', { 
                            avatar: null
                        })
                        this.$store.commit("user/SET_AVATAR", null)
                        this.$message.success(this.$t('avatar_delete_success'))
                        this.avatarReload = Date.now()
                    } catch(error) {
                        errorHandler({error})
                    }
                }
            })
        },
        uploadImage() {
            this.cropper.getCroppedCanvas().toBlob(async (avatar) => {
                try {
                    const exc = getFileExtension(this.file.name),
                        filename = `${hashString(this.file.name)}.${exc}`

                    this.uploadLoading = true
                    const data = await this.$uploadFile({
                        file: avatar,
                        url: '/common/upload/',
                        fieldName: 'upload',
                        fileName: filename
                    })
                    if(data) {
                        await this.$http.post('users/change_avatar/', { 
                            avatar: data[0].id
                        })
                        this.$store.commit("user/SET_AVATAR", data[0])
                        this.$message.success(this.$t('success_avatar'))
                        this.avatarReload = Date.now()
                        this.closeCropModal()
                    }
                } catch(error) {
                    errorHandler({error})
                } finally {
                    this.uploadLoading = false
                }
            })
        },
        async getMenu() {
            try {
                this.loading = true
                await this.$store.dispatch('user/getProfileMenu')
                this.setStartActive()
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                this.loading = false
            }
        },
        setStartActive() {
            if(this.$route.query?.menu_page)
                this.active = this.$route.query.menu_page
            else if(this.profileMenu?.length) {
                this.active = JSON.parse(JSON.stringify(this.profileMenu[0].path))
            }
        },
        openDrawer() {
            this.visible = true
        },
        selectMenu(item) {
            if(item.path !== this.active) {
                this.active = item.path

                const query = JSON.parse(JSON.stringify(this.$route.query))
                query.menu_page = item.path
                this.$router.push({query})
            }
        },
        close() {
            const query = JSON.parse(JSON.stringify(this.$route.query))
            if(query.menu_page)
                delete query.menu_page
            if(query.my_profile)
                delete query.my_profile 

            this.$router.replace({query})
            this.setStartActive()
        },
        afterVisibleChange(val) {
            if(!val)
                this.close()
            else {
                this.getMenu()
            }
        }
    }
}
</script>

<style lang="scss" scoped>
::v-deep{
    .avatar_edit__icon{
        position: absolute;
        top: 60%;
        right: 30%;
    }
}
.drawer_body{
    height: 100%;
    overflow-y: auto;
    grid-template-columns: 320px 1fr;
    .profile_menu{
        padding: 20px;
        overflow-y: auto;
        height: 100%;
        .menu{
            .item{
                display: flex;
                align-items: center;
                border-radius: var(--borderRadius);
                padding: 12px 10px;
                font-size: 16px;
                cursor: pointer;
                transition: background-color 0.3s ease;
                font-weight: 300;
                &:not(:last-child){
                    margin-bottom: 3px;
                }
                &:hover{
                    background-color: #eff2f5;
                }
                &.active{
                    background: var(--primaryHover);
                    color: var(--blue);
                }
                .fi{
                    margin-right: 10px;
                    font-size: 20px;
                }
            }
        }
    }
    .profile_content{
        &.w_scroll{
            overflow-y: auto;
        }
        .profile_wrapper{
            &.w_padding{
                padding: 20px;
            }
        }
        h1{
            font-weight: 300;
            font-size: 24px;
            margin-bottom: 20px;
        }
    }
}
.cropper_modal{
    &::v-deep{
        .ant-drawer-wrapper-body,
        .ant-drawer-content{
            overflow: hidden;
        }
        .cropper-face{
            border-radius: 50%;
        }
        .cropper-view-box {
            border-radius: 50%;
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
