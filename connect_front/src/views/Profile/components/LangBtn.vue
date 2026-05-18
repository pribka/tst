<template>
    <a-spin class="w-full" size="small" :spinning="langLoading">
        <div class="lang_select_btn w-full flex items-center justify-between cursor-pointer mt-4 px-4" @click="activity = true">
            <span style="font-size: 18px;">{{ $t(user.language) }}</span>
            <i class="fi fi-rr-angle-small-down ml-2" style="opacity: 0.6;" />
        </div>
        <ActivityDrawer 
            :vis="activity" 
            useVis
            :cDrawer="closeDrawer">
            <ActivityItem v-for="lang in langList" :key="lang" @click="changeLang(lang)">
                <div class="flex items-center justify-between w-full">
                    <span :class="checkActive(lang) && 'blue_color'">{{ $t(lang) }}</span>
                    <div style="min-width: 20px;" class="ml-2">
                        <i v-if="checkActive(lang)" style="font-size: 14px;opacity: 0.6;" class="fi fi-rr-check" />
                    </div>
                </div>
            </ActivityItem>
        </ActivityDrawer>
    </a-spin>
</template>

<script>
import { langList, loadedLanguages } from '@/config/i18n-setup'
import { mapState } from 'vuex'
import { errorHandler } from '@/utils/index.js'
import { ActivityItem, ActivityDrawer } from '@/components/ActivitySelect'
import { clearGlobalConfigCache } from '@/utils/configCache'
export default {
    components: {
        ActivityItem,
        ActivityDrawer
    },
    computed: {
        ...mapState({
            isMobile: state => state.isMobile,
            user: state => state.user.user
        })
    },
    data() {
        return {
            langList,
            loadedLanguages,
            langLoading: false,
            activity: false
        }
    },
    methods: {
        closeDrawer() {
            this.activity = false
        },
        checkActive(lang) {
            return this.user?.language === lang
        },
        async changeLang(language) {
            try {
                this.closeDrawer()
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
