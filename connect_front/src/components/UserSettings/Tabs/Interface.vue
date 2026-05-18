<template>
    <div class="setting_lists">
        <!--<div class="other_item">
            <div
                class="label"
                @click="eyeVersion = !eyeVersion">
                {{ $t('monochrome_mode') }}
            </div>
            <a-switch 
                v-model="eyeVersion" 
                size="large" />
        </div>-->
        <div class="other_item">
            <div class="w-full"> 
                <div class="mb-1 font-light" style="font-size: 16px;">{{ $t('language') }}</div>
                <a-select 
                    :default-value="user.language" 
                    size="large" 
                    :getPopupContainer="getPopupContainer"
                    :loading="langLoading"
                    :style="`width: 100%;${isMobile ? 'max-width: 100%;' : 'max-width: 300px;'}`"
                    @change="changeLang">
                    <a-select-option 
                        v-for="lang in langList" 
                        :key="lang"
                        :value="lang">
                        {{ $t(lang) }}
                    </a-select-option>
                </a-select>
            </div>
        </div>
        <!--<a-tabs v-if="isMobile" default-active-key="mobile" class="mt-3">
            <a-tab-pane key="mobile" :tab="$t('mobile_version')">
                <InterfaceMenuMobile2 />
            </a-tab-pane>
        </a-tabs>-->
    </div>
</template>

<script>
import { updateTheme } from '@/config/dynamicTheme'
//import InterfaceMenuDesc from '../components/InterfaceMenuDesc.vue'
//import InterfaceMenuMobile2 from '../components/InterfaceMenuMobile2.vue'
import { langList, loadedLanguages } from '@/config/i18n-setup'
import { mapState } from 'vuex'
import { errorHandler } from '@/utils/index.js'
import { clearGlobalConfigCache } from '@/utils/configCache'
export default {
    components: {
        //InterfaceMenuDesc,
        //InterfaceMenuMobile2
    },
    computed: {
        ...mapState({
            isMobile: state => state.isMobile,
            user: state => state.user.user
        }),
        documentReverse: {
            get() {
                return this.$store.state.documentReverse
            },
            set(val) {
                this.$store.commit('TOGGLE_DOCUMENT_REVERSE', val)
            }
        },
        eyeVersion: {
            get() {
                return this.$store.state.eyeVersion
            },
            set(val) {
                this.$store.commit('TOGGLE_EYE_VERSION', val)
            }
        },
        asideType: {
            get() {
                return this.$store.state.asideType
            },
            set(val) {
                this.$store.commit('TOGGLE_ASIDE_TYPE', val)
            }
        }
    },
    data() {
        return {
            langList,
            loadedLanguages,
            langLoading: false,
            palette: [
                {
                    color: '#f5222d'
                },
                {
                    color: '#fa541c'
                },
                {
                    color: '#faad14'
                },
                {
                    color: '#13c2c2'
                },
                {
                    color: '#52c41a'
                },
                {
                    color: '#1890ff'
                },
                {
                    color: '#2f54eb'
                },
                {
                    color: '#722ed1'
                }
            ]
        }
    },
    methods: {
        getPopupContainer(trigger) {
            return trigger.parentNode
        },
        chnageColor(color) {
            updateTheme(color)
        },
        async changeLang(language) {
            try {
                this.langLoading = true
                const { data } = await this.$http.put('/users/update_profile/', {
                    language,
                    contact_phone: this.user.contact_phone,
                    job_title: this.user.job_title,
                    birthday: this.user.birthday
                })
                if(data) {
                    await clearGlobalConfigCache().catch(() => null)
                    location.reload()
                }
            } catch(error) {
                errorHandler({error})
            } finally {
                this.langLoading = false
            }
        }
    }
}
</script>


<style lang="scss" scoped>
.setting_lists{
    .card_select{
        margin-bottom: 30px;
        &__label{
            margin-bottom: 10px;
            font-size: 16px;
        }
        &::v-deep{
            .ant-radio-group{
                display: grid;
                gap: 8px;
                grid-template-columns: repeat(1, minmax(0, 1fr));
                @media (min-width: 800px) {
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                }
                @media (min-width: 1000px) {
                    grid-template-columns: repeat(3, minmax(0, 1fr));
                }
                @media (min-width: 1200px) {
                    max-width: 900px;
                    grid-template-columns: repeat(4, minmax(0, 1fr));
                }
                .ant-radio-wrapper{
                    border: 1px solid var(--border2);
                    border-radius: var(--borderRadius);
                    text-align: center;
                    padding-left: 50px;
                    padding-right: 50px;
                    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
                    background: #ffffff;
                    &:hover{
                        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
                    }
                    .ant-radio{
                        display: none;
                    }
                    &.ant-radio-wrapper-checked{
                        border-color: var(--blue);
                        background: #eff2f5;
                    }
                    img{
                        max-width: 110px;
                        margin: 0 auto;
                    }
                    .r_label{
                        margin-top: 10px;
                        color: var(--gray);
                        font-weight: 300;
                        color: #000000;
                    }
                }
            }
        }
    }
    .other_item{
        &:not(.color_palette){
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        &.disabled{
            cursor: default;
            .label{
                opacity: 0.6;
            }
        }
        .label{
            width: 100%;
            font-size: 16px;
            cursor: pointer;
            font-weight: 300;
            -webkit-touch-callout: none; /* iOS Safari */
            -webkit-user-select: none;   /* Chrome/Safari/Opera */
            -khtml-user-select: none;    /* Konqueror */
            -moz-user-select: none;      /* Firefox */
            -ms-user-select: none;       /* Internet Explorer/Edge */
            user-select: none;  
            padding: 15px 0;
        }
    }
}
</style>
