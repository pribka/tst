<template>
    <div class="profile">
        <div 
            v-if="loading" 
            class="flex justify-center pt-5">
            <a-spin />
        </div>
        <div v-else>
            <div class="profile_menu truncate">
                <template v-if="profileMenu.length">
                    <div 
                        v-if="user"  
                        class="user text-center">
                        <div class="flex justify-center relative">
                            <label for="avatar_upload" class="cursor-pointer">
                                <a-avatar 
                                    :size="100" 
                                    :key="user.avatar ? user.avatar.path : false"
                                    :src="user.avatar && user.avatar.path"
                                    icon="user" />
                            </label>
                            <a-dropdown :trigger="['click']">
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
                            
                            <input
                                type="file"
                                id="avatar_upload"
                                style="display:none;"
                                ref="avatarUpload"
                                v-on:change="handleFileChange"
                                accept=".jpg, .jpeg, .png, .gif" />
                        
                        </div>
                        <div class="user_name mt-3 font-semibold text-xl">
                            {{ userName }}
                        </div>
                        <div 
                            v-if="user.email" 
                            class="user_email font-light">
                            {{ user.email }}
                        </div>
                    </div>

                    <template v-if="user">
                        <div v-if="user.has_demo_data || has_onboarding_tasks" class="mt-2 flex gap-2 flex-col">
                            <a-button 
                                v-if="user && user.has_demo_data"
                                class="delete_demo mt-2" 
                                type="flat_primary" 
                                block
                                size="large"
                                @click="deleteDemoData()">
                                {{ $t('delete_demodata') }}
                            </a-button>
                            <a-button 
                                v-if="has_onboarding_tasks"
                                type="flat_primary"
                                block
                                size="large"
                                @click="deleteDemoTask()">
                                Удалить ознакомительные задачи
                            </a-button>
                        </div>
                    </template>

                    <div class="menu">
                        <div 
                            v-for="item in profileMenu" 
                            :key="item.path" 
                            class="item truncate select-none"
                            @click="selectMenu(item)">
                            <i :class="`fi ${item.icon}`"></i>
                            <span class="truncate whitespace-nowrap">
                                {{ item.name }}
                            </span>
                        </div>
                        <div
                            v-if="support"
                            class="item truncate select-none justify-between"
                            @click="supportVisible = true">
                            <div class="flex items-center">
                                <i class="fi fi-rr-interrogation"></i>
                                <span class="truncate whitespace-nowrap">
                                    Справка
                                </span>
                            </div>
                            <a-badge :count="unreadCount" :number-style="{ backgroundColor: '#52c41a' }" />
                        </div>
                        <div
                            v-if="myPoints"
                            class="item truncate select-none"
                            @click="openDeliveryPoints()">
                            <i class="fi fi-rr-marker"></i>
                            <span class="truncate whitespace-nowrap">
                                Мои точки доставки
                            </span>
                        </div>
                        <div 
                            class="item truncate select-none"
                            @click="otherVisible = true">
                            <i class="fi fi-rr-exclamation"></i>
                            <span class="truncate whitespace-nowrap">
                                Прочее
                            </span>
                        </div>
                        <div 
                            class="item truncate select-none text_red"
                            @click="logOut()">
                            <i class="fi fi fi-rr-power"></i>
                            <span class="truncate whitespace-nowrap">
                                {{ $t('exit') }}
                            </span>
                        </div>
                    </div>

                    <LangBtn />
                    <!--<ShowSnowBtn />-->
                </template>
            </div>
        </div>

        <DrawerTemplate
            title=""
            width="100%"
            height="100%"
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
            <div class="cr_d_footer">
                <a-button type="primary" size="large" block @click="uploadImage()" class="mb-2" :loading="uploadLoading">
                    Загрузить
                </a-button>
                <a-button type="ui" ghost block size="large" @click="closeCropModal()">
                    {{$t('close')}}
                </a-button>
            </div>
        </DrawerTemplate>

        <DrawerTemplate
            v-model="otherVisible"
            class="activity_views other_us_menu"
            height="auto"
            title="Прочее"
            destroyOnClose
            @close="otherVisible = false">
            <menu>
                <li>
                    <div 
                        class="link" 
                        @click="cacheClear()">
                        <i class="fi fi-rr-refresh icon"></i>
                        <span>Очистить кэш</span>
                    </div>
                </li>
                <li>
                    <div 
                        class="link" 
                        @click="openVersion()">
                        <i class="fi fi-rr-interrogation icon"></i>
                        <span>Версия клиента</span>
                    </div>
                </li>
            </menu>
            <template slot="footer">
                <a-button 
                    type="ui_ghost" 
                    size="large"
                    block
                    @click="otherVisible = false">
                    Закрыть
                </a-button>
            </template>
        </DrawerTemplate>

        <DrawerTemplate
            v-if="support"
            v-model="supportVisible"
            class="activity_views other_us_menu"
            height="auto"
            title="Справка"
            destroyOnClose
            @close="supportVisible = false">
            <menu>
                <li>
                    <div 
                        class="link justify-between" 
                        @click="portalNews()">
                        <div class="flex items-center">
                            <i class="fi fi-rr-megaphone icon"></i>
                            <span>Лента новостей</span>
                        </div>
                        <a-badge :count="unreadCount" :number-style="{ backgroundColor: '#52c41a' }" />
                    </div>
                </li>
                <li>
                    <div 
                        class="link" 
                        @click="openHelp()">
                        <i class="fi fi-rr-messages-question icon"></i>
                        <span>Справка</span>
                    </div>
                </li>
                <li v-if="user && user.support_chat">
                    <div 
                        class="link" 
                        @click="openSupportChat()">
                        <i class="fi fi-rr-paper-plane icon"></i>
                        <span>Чат технической поддержки</span>
                    </div>
                </li>
            </menu>
            <template slot="footer">
                <a-button 
                    type="ui_ghost" 
                    size="large"
                    block
                    @click="supportVisible = false">
                    Закрыть
                </a-button>
            </template>
        </DrawerTemplate>
        <DrawerTemplate
            title="Версия клиента"
            destroyOnClose
            height="auto"
            v-model="versionModal"
            @close="versionModal = false">
            <div class="mb-3">
                <strong class="mr-2">Хост:</strong>
                <span>
                    {{ host }}
                </span>
            </div>
            <div class="mb-3">
                <strong class="mr-2">Версия клиента:</strong>
                <span>
                    {{ version }}
                </span>
            </div>
            <div v-if="builddata">
                <strong class="mr-2">Дата билда:</strong>
                <span>
                    {{ builddata }}
                </span>
            </div>
            <template slot="footer">
                <a-button 
                    type="ui_ghost" 
                    size="large"
                    block
                    @click="versionModal = false">
                    Закрыть
                </a-button>
            </template>
        </DrawerTemplate>
    </div>
</template>

<script>

import { mapState } from 'vuex'
import eventBus from '@/utils/eventBus.js'
import {checkImageWidthHeight, hashString, getFileExtension} from '@/utils/utils'
import 'cropperjs/dist/cropper.css'
import Cropper from 'cropperjs'
import { errorHandler } from '@/utils/index.js'
import { unregisterBrowserPush } from '@/utils/webPush'
export default {
    components: {
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue'),
        //ShowSnowBtn: () => import('./components/ShowSnowBtn.vue'),
        LangBtn: () => import('./components/LangBtn.vue')
    },
    computed: {
        ...mapState({
            isMobile: state => state.isMobile,
            user: state => state.user.user,
            config: state => state.config.config,
            pushAuth: state => state.pushAuth,
            profileMenu: state => state.user.profileMenu,
            windowWidth: state => state.windowWidth,
            serverType: state => state.serverType,
            dbList: state => state.dbList
        }),
        myPoints() {
            return this.config?.order_setting?.myPoints || false
        },
        support() {
            return this.config?.header_setting?.support || false
        },
        userName() {
            if(this.user.first_name)
                return `${this.user.first_name} ${this.user.last_name && this.user.last_name.substr(0, 1)}`
            else
                return this.user.username
        },
        has_onboarding_tasks() {
            return this.user?.has_onboarding_tasks
        },
    },
    data() {
        return {
            loading: false,
            cropModal: false,
            otherVisible: false,
            supportVisible: false,
            versionModal: false,
            unreadCount: 0,
            cropperOptions: {
                aspectRatio: 1 / 1,
                minCropBoxWidth: 100,
                minCropBoxHeight: 100
            },
            uploadLoading: false,
            file: null,
            dataUrl: null,
            minSize: 100,
            avatarLoader: false,
            sAvatar: '',
            host: process.env.VUE_APP_URL,
            version: process.env.VUE_APP_VERSION,
            builddata: process.env.VUE_APP_BUILD_DATE
        }
    },
    created () {
        this.getMenu()
        if(this.support)
            this.getNewsCount()
    },
    methods: {
        onAvatarMenuClick({ key }) {
            if(key === 'upload')
                this.$refs.avatarUpload.click()
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
        deleteDemoTask() {
            this.$confirm({
                title: 'Вы действительно хотите удалить ознакомительные задачи?',
                content: '',
                okText: 'Удалить',
                okType: 'danger',
                closable: true,
                maskClosable: true,
                cancelText: 'Закрыть',
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post('/tasks/onboarding/delete/')
                            .then(() => {
                                this.$message.success('Ознакомительные задачи успешно удалены')
                                setTimeout(() => {
                                    window.location.reload()
                                }, 2000)
                                resolve()
                            })
                            .catch(error => {
                                errorHandler({error})
                                reject(e)
                            })
                    })
                }
            })
        },
        async deleteDemoData() {
            this.$confirm({
                title: this.$t('delete_demodata_q'),
                content: '',
                okText: this.$t('remove'),
                okType: 'danger',
                zIndex: 2000,
                closable: true,
                maskClosable: true,
                cancelText: this.$t('Close'),
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post('/demo/delete/')
                            .then(({data}) => {
                                if(data?.message) {
                                    this.$message.success(data.message)
                                    setTimeout(() => {
                                        window.location.reload()
                                    }, 1500)
                                }
                                resolve()
                            })
                            .catch(error => {
                                errorHandler({error})
                                reject(e)
                            })
                    })
                }
            })
        },
        async getNewsCount() {
            try {
                const { data } = await this.$http.get('/news/news/unread_count/')
                if(data?.unread_count) {
                    this.unreadCount = data.unread_count
                }
            } catch(error) {
                errorHandler({error, show: false})
            }
        },
        changeCount() {
            if(this.unreadCount > 0) {
                this.unreadCount -= 1
            } else {
                this.unreadCount = 0
            }
        },
        portalNews() {
            this.supportVisible = false
            const query = {...this.$route.query, newList: 'true'}
            this.$router.push({ query })
        },
        openHelp() {
            this.supportVisible = false
            const query = {...this.$route.query}
            query.help = true
            if(query.newList)
                delete query.newList
            this.$router.push({ query })
        },
        openSupportChat() {
            this.$router.push({ name: 'chat', query: { chat_id: this.user.support_chat } })
        },
        openDeliveryPoints() {
            eventBus.$emit('open_delivery_points_drawer')
        },
        openVersion() {
            this.versionModal = true
            this.otherVisible = false
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
                        const res = await this.$http.post('users/change_avatar/', { 
                            avatar: data[0].id
                        })

                        if(res) {
                            this.$store.commit("user/SET_AVATAR", data[0])
                            this.$message.success(this.$t('success_avatar'))
                            this.closeCropModal()
                        }
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
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                this.loading = false
            }
        },
        selectMenu(item) {
            if(item.path) {
                const query = JSON.parse(JSON.stringify(this.$route.query))
                query.menu_page = item.path
                query.my_profile = 'open'
                this.$router.push({query})
            }
        },

        async cacheClear2() {
            try {
                this.loading = true
                await this.$http.get('/app_info/update_front_cache/')
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                this.loading = false
                location.reload()
            }
        },


        // LOGOUT 
        async cacheClear(reload = true) {
            try {
                this.loading = true
                for(let key in this.dbList) {
                    await this.deleteDb(this.dbList[key])
                }
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                this.loading = false

                if(reload)
                    location.reload()
            }
        },
        deleteDb(name) {
            return new Promise((resolve, reject) => {
                const req = indexedDB.deleteDatabase(name)
                req.onerror = () => {
                    reject(false)
                }

                req.onsuccess = () => {
                    resolve(true)
                }

                req.onblocked = () => {
                    resolve(true)
                    console.log("Couldn't delete database due to the operation being blocked")
                }
            })
        },
        async pushUnrigister() {
            if(this.pushAuth) {
                try {
                    await unregisterBrowserPush({ unsubscribe: true })
                } catch(error) {
                    errorHandler({error})
                }
            }
        },
        async logOut() {
            try {
                this.loading = true
                await this.pushUnrigister()
                await this.$store.dispatch('user/logout')
                await this.cacheClear(false)
                // this.$router.push({name: 'login'})
                location.reload()
            } catch(error) {
                errorHandler({error})
            } finally {
                this.loading = false
            }
        }
    },
    mounted() {
        eventBus.$on('read_news_count', () => {
            this.changeCount()
        })
    },
    beforeDestroy() {
        eventBus.$off('read_news_count')
    }
}
</script>

<style lang="scss" scoped>
$fullscreen: calc(var(--vh, 1vh) * 100);
.cropper_modal{
    &::v-deep{
        .ant-drawer-wrapper-body,
        .ant-drawer-content{
            overflow: hidden;
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
        .cropper-face{
            border-radius: 50%;
        }
        .cropper-view-box {
            border-radius: 50%;
        }
    }
}
.profile{
    height: 100%;
    overflow-y: auto;
    .profile_menu{
        padding: 15px;
        .menu{
            background: #fff;
            border-radius: var(--borderRadius);
            margin-top: 20px;
            .item{
                display: flex;
                align-items: center;
                padding: 15px;
                font-size: 18px;
                cursor: pointer;
                transition: background-color 0.3s ease;
                font-weight: 300;
                &:not(:last-child){
                    border-bottom: 1px solid var(--borderColor);
                }
                &.active{
                    color: var(--blue);
                }
                .fi{
                    margin-right: 15px;
                    font-size: 22px;
                }
            }
        }
    }
 
}
.profile_drawer_body{
    margin-top: -25px;
    h1{
        font-weight: 300;
        font-size: 24px;
        margin-bottom: 20px;
    }
}
.user {
    max-width: 320px;
    margin: 0 auto;
    margin-bottom: 10px;
}
.avatar_edit__icon{
    position: absolute;
    top: 60%;
    right: 30%;
}
.other_us_menu{
    menu{
        width: 100%;
        padding: 0px;
        margin: 0px;
        li{
            list-style: none;
            color: #000;
            .link{
                display: flex;
                align-items: center;
                font-weight: 300;
                padding: 13px 0;
                font-size: 17px;
                .icon{
                    margin-right: 10px;
                }
            }
            &:not(:last-child){
                margin-bottom: 0px!important;
            }
        }
    }
}
.profile_drawer{
    &::v-deep{
        .ant-drawer-content-wrapper {
            height: 100% !important;
        }
        .ant-drawer-body{
            padding: 0px;
        }
    }
}
</style>
