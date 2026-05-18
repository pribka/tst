<template>
    <a-dropdown :trigger="['click']" overlayClassName="lang_select">
        <a-spin :spinning="langLoading" size="small">
            <div class="action_btn">
                <a-button type="link" class="text-current flex items-center">
                    <span class="uppercase" style="font-size: 18px;">{{ user.language }}</span>
                    <i class="fi fi-rr-angle-small-down" style="opacity: 0.6;" />
                </a-button>
            </div>
        </a-spin>
        <a-menu slot="overlay">
            <a-menu-item v-for="lang in langList" :key="lang" class="flex items-center justify-between" style="padding: 7px 10px 7px 10px;" @click="changeLang(lang)">
                <span :class="checkActive(lang) && 'blue_color'">{{ $t(lang) }}</span>
                <div style="min-width: 20px;" class="ml-2">
                    <i v-if="checkActive(lang)" style="font-size: 12px;" class="fi fi-rr-check" />
                </div>
            </a-menu-item>
        </a-menu>
    </a-dropdown>
</template>

<script>
import { langList, loadedLanguages } from '@/config/i18n-setup'
import { mapState } from 'vuex'
import { errorHandler } from '@/utils/index.js'
import { clearGlobalConfigCache } from '@/utils/configCache'
export default {
    computed: {
        ...mapState({
            isMobile: state => state.isMobile,
            user: state => state.user.user
        }),
    },
    data() {
        return {
            langList,
            loadedLanguages,
            langLoading: false,
        }
    },
    methods: {
        checkActive(lang) {
            return this.user?.language === lang
        },
        async changeLang(language) {
            try {
                if(this.checkActive(language))
                    return;
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
