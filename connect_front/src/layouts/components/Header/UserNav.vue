<template>
    <div
        v-if="user"
        class="user_menu">
        <a-dropdown 
            destroyPopupOnHide
            :trigger="['click']"
            overlayClassName="us_menu_drop">
            <div class="ant-dropdown-link flex items-center">
                <a-spin :spinning="loading">
                    <a-avatar
                        class="cursor-pointer"
                        :size="32"
                        avResize
                        shape="square"
                        :key="user.avatar && user.avatar.path ? user.avatar.path : true"
                        :src="user.avatar && user.avatar.path">
                        <i class="fi fi-rr-user" />
                    </a-avatar>
                </a-spin>
                <!--<div class="ml-2 mr-1 user_name truncate">
                    {{ userName }}
                </div>
                <i class="fi fi-rr-angle-small-down"></i>-->
            </div>
            <template #overlay>
                <a-menu>
                    <a-menu-item
                        key="1"
                        class="flex items-center"
                        @click="openSetting()">
                        <i class="fi fi-rr-user mr-2"></i> 
                        <span>{{$t('profile')}}</span>
                    </a-menu-item>
                    <a-menu-item
                        v-if="myPoints"
                        key="18"
                        class="flex items-center"
                        @click="openDeliveryPoints()">
                        <i class="fi fi-rr-marker mr-2"></i> 
                        <span>{{$t('my_delivery_points')}}</span>
                    </a-menu-item>
                    <a-menu-item
                        v-if="oldLk"
                        key="14"
                        class="flex items-center"
                        @click="openLk()">
                        <i class="fi fi-rr-link-alt mr-2"></i>
                        <span>{{$t('old_lk')}}</span>
                    </a-menu-item>
                    <!--<a-menu-item
                        key="interface"
                        class="flex items-center"
                        @click="openSetting({name: 'menu_page', value: 'interface'})">
                        <i class="fi fi-rr-settings-sliders mr-2"></i> 
                        <span>{{$t('interface')}}</span>
                    </a-menu-item>-->
                    <a-menu-item
                        key="12"
                        class="flex items-center"
                        @click="openSetting({name: 'menu_page', value: 'change-password'})">
                        <i class="fi fi-rr-lock mr-2"></i> 
                        <span>{{$t('change_password')}}</span>
                    </a-menu-item>
                    <a-menu-item
                        v-if="false"
                        key="13"
                        class="flex items-center"
                        @click="openSetting({name: 'menu_page', value: 'interface'})">
                        <i class="fi fi-rr-settings-sliders mr-2"></i>
                        <span>{{$t('interface')}}</span>
                    </a-menu-item>
                    <a-sub-menu key="other">
                        <template #title>
                            <span class="flex items-center">
                                <i class="fi fi-rr-exclamation mr-2" />
                                {{$t('other')}}
                            </span>
                        </template>
                        <a-menu-item
                            key="3"
                            class="flex items-center"
                            @click="cacheClear()">
                            <i class="fi fi-rr-refresh mr-2"></i>
                            {{$t('clear_cache')}}
                        </a-menu-item>
                        <a-menu-item
                            key="16"
                            class="flex items-center"
                            @click="versionModal = true">
                            <i class="fi fi-rr-interrogation mr-2"></i>
                            {{$t('client_version')}}
                        </a-menu-item>
                        <template v-if="serverType === 'dev'">
                            <a-menu-item
                                key="20"
                                class="flex items-center"
                                @click="openUIComponents()">
                                <i class="fi fi-rr-layout-fluid mr-2"></i>
                                <span>{{$t('ui_components')}}</span>
                            </a-menu-item>
                            <a-menu-item
                                key="11"
                                class="flex items-center"
                                @click="pushModalVis = true">
                                <i class="fi fi-rr-comment-alt mr-2"></i>
                                <span>{{$t('send_push')}}</span>
                            </a-menu-item>
                            <a-menu-item
                                key="5"
                                class="flex items-center"
                                @click="cacheClear2()">
                                <i class="fi fi-rr-refresh mr-2"></i>
                                {{$t('clear_cache_all')}}
                            </a-menu-item>
                            <a-modal
                                :title="$t('send_push')"
                                :destroyOnClose="true"
                                :visible="pushModalVis"
                                @cancel="pushModalVis = false">
                                <template slot="footer">
                                    <a-form-model
                                        ref="pushForm"
                                        :label-col="labelCol"
                                        :wrapper-col="wrapperCol"
                                        :model="form"
                                        :rules="rules">
                                        <a-form-model-item ref="title" :label="$t('title')" prop="title">
                                            <a-input v-model="form.message.title" />
                                        </a-form-model-item>
                                        <a-form-model-item ref="body" :label="$t('text')" prop="body">
                                            <a-textarea
                                                v-model="form.message.body"
                                                :auto-size="{ minRows: 2, maxRows: 6 }"/>
                                        </a-form-model-item>
                                        <a-form-model-item ref="click_action" :label="$t('link')" prop="click_action">
                                            <a-input v-model="form.message.click_action" />
                                        </a-form-model-item>
                                    </a-form-model>
                                    <a-button 
                                        type="primary" 
                                        @click="sendPush()">
                                        {{$t('send')}}
                                    </a-button>
                                </template>
                            </a-modal>
                        </template>
                    </a-sub-menu>
                    <a-menu-divider />
                    <a-menu-item
                        key="2"
                        class="text_red flex items-center"
                        @click="logOut()">
                        <i class="fi fi-rr-power mr-2"></i>
                        {{$t('logout')}}
                    </a-menu-item>
                </a-menu>
            </template>
        </a-dropdown>
        <a-modal
            :title="$t('client_version')"
            destroyOnClose
            :visible="versionModal"
            @cancel="versionModal = false">
            <div class="mb-3">
                <strong class="mr-2">{{$t('host')}}:</strong>
                <span>
                    {{ host }}
                </span>
            </div>
            <div class="mb-3">
                <strong class="mr-2">{{$t('client_version')}}:</strong>
                <span>
                    {{ version }}
                </span>
            </div>
            <div v-if="buildData">
                <strong class="mr-2">{{$t('build_date')}}:</strong>
                <span>
                    {{ buildData }}
                </span>
            </div>
            <template slot="footer">
                <a-button 
                    type="default" 
                    @click="versionModal = false">
                    {{$t('close')}}
                </a-button>
            </template>
        </a-modal>
        <component v-if="showPoints" :is="MyDeliveryPoints" />
    </div>
</template>


<script>
import {mapState} from 'vuex'
import eventBus from '@/utils/eventBus.js'
import { errorHandler } from '@/utils/index.js'
import { unregisterBrowserPush } from '@/utils/webPush'
export default {
    data() {
        return {
            loading: false,
            showPoints: false,
            pushModalVis: false,
            labelCol: { span: 24 },
            wrapperCol: { span: 24 },
            versionModal: false,
            form: {
                token: 'f(HcKZt%AkCrsWVaxC}xhbtu6t[IQOcx5A$Nxdao^s1U1V1J&2{%JKn',
                message: {
                    title: 'Test',
                    body: 'Test',
                    click_action: 'https://bpms.gos24.kz/ru'
                }
            },
            rules: {},
            host: process.env.VUE_APP_URL,
            version: process.env.VUE_APP_VERSION,
            buildData: process.env.VUE_APP_BUILD_DATE
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user,
            dbList: state => state.dbList,
            serverType: state => state.serverType,
            pushAuth: state => state.pushAuth,
            config: state => state.config.config
        }),
        userName() {
            if(this.user.first_name && this.user.last_name)
                return this.user.first_name + ' ' + this.user.last_name.substr(0, 1)
            else
                return this.user.first_name || this.user.username
        },
        oldLk() {
            if(this.config?.old_cabinet_url)
                return this.config.old_cabinet_url
            else
                return null
        },
        myPoints() {
            return this.config?.order_setting?.myPoints || false
        },
        MyDeliveryPoints() {
            if(this.myPoints)
                return () => import('@apps/LogisticMonitor/components/MyDeliveryPoints.vue')
            return null
        }
    },
    methods: {
        openUIComponents() {
            eventBus.$emit('open_ui_drawer')
        },
        openDeliveryPoints() {
            this.showPoints = true
            eventBus.$emit('open_delivery_points_drawer')
        },
        openLk() {
            window.open(this.oldLk, '_blank')
        },
        sendPush() {
            this.$refs.pushForm.validate(async valid => {
                if (valid) {
                    await this.$http2.post('/subscribe/send/', this.form)
                } else {
                    console.log('error submit!!');
                    return false;
                }
            })
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
        openSetting(params = null) {
            const query = JSON.parse(JSON.stringify(this.$route.query))
            query.my_profile = 'open'

            if(params?.name) {
                query[params.name] = params.value
            }

            this.$router.push({query})
        },
        async cacheClear(reload = true) {
            try {
                this.loading = true
                for(const key in this.dbList) {
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
        async deleteDb(name) {
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
                await this.cacheClear(false)
                await this.$store.dispatch('user/logout')
                location.reload()
            } catch(error) {
                errorHandler({error})
            } finally {
                this.loading = false
            }
        }
    }
}
</script>

<style lang="scss">
.us_menu_drop{
    &.ant-dropdown{
        .ant-dropdown-menu-submenu-title{
            .ant-dropdown-menu-submenu-arrow{
                top: 8px;
            }
        }
    }
}
</style>

<style lang="scss" scoped>
::v-deep{
    .ant-dropdown-menu-submenu-title{
        display: flex;
        align-items: center;
        .ant-dropdown-menu-submenu-arrow{
            top: 2px;
        }
    }
}
.user_menu{
    .ant-avatar-string{
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
    }
    .user_name{
        line-height: 22px;
        font-size: 15px;
        text-transform: capitalize;
        max-width: 150px;
    }
    .user_icon{
        &.anticon{
            &.anticon-down{
                font-size: 10px;
            }
        }
    }
    .ant-dropdown-link{
        transition: background .1s ease-in;
        cursor: default;
        .ant-avatar{
            background: #eff2f5;
            color: var(--text);
        }
        &.ant-dropdown-open,
        &:hover{
            background: #eff2f5;
        }
        &::v-deep{
            .ant-avatar{
                border-radius: 6px;
                img{
                    border-radius: 6px;
                }
            }
        }
    }
}
</style>
