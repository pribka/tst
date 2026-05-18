<template>
    <a-form-model
        ref="linkInvite"
        :model="form"
        class="link_wrapper"
        :rules="rules">
        <div v-if="loading" class="flex justify-center">
            <a-spin />
        </div>
        <a-form-model-item
            v-else
            ref="link"
            :label="$t('team.invite_link')"
            prop="link">
            <div class="link_input">
                <span class="w-full">{{ link }}</span>
                <a-button type="link" class="ant-btn-icon-only" v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }"  :content="$t('team.copy_link')" @click="copyLink()">
                    <i class="fi fi-rr-copy-alt"></i>
                </a-button>
            </div>
            <div class="ant-form-explain mt-2">
                {{ $t('team.send_link_to_admin') }}
            </div>
            <div class="share_links">
                <div class="label mr-2">{{ $t('team.share') }}</div>
                <div 
                    class="share_btn" 
                    v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }" 
                    :content="$t('team.share_telegram')"
                    @click="tgShare()">
                    <img src="@/assets/images/telegram.svg" />
                </div>
                <div 
                    class="share_btn" 
                    v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }" 
                    :content="$t('team.share_whatsapp')"
                    @click="wpShare()">
                    <img src="@/assets/images/WhatsApp.svg" />
                </div>
            </div>
        </a-form-model-item>
    </a-form-model>
</template>

<script>
import { mapState } from 'vuex'
export default {
    computed: {
        ...mapState({
            isMobile: state => state.isMobile
        })
    },
    data() {
        return {
            loading: false,
            link: 'http://d.centersoft.kz:8080/ru/communication/team',
            form: {},
            rules: {}
        }
    },
    methods: {
        tgShare() {
            window.open(`https://t.me/share/url?url=${this.link}&text=${this.$t('team.temp_link_text')}`, '_blank').focus()
        },
        wpShare() {
            window.open(`https://wa.me/?text=${this.$t('team.temp_link_text')} - ${this.link}`, '_blank').focus()
        },
        copyLink() {
            try {
                navigator.clipboard.writeText(this.link)
                this.$message.success(this.$t('team.link_copied'))
            } catch(e) {
                console.log(e)
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.link_wrapper{
    padding: 15px;
}
.link_input{
    background-color: #eff2f5;
    border-radius: var(--borderRadius);
    display: flex;
    align-items: center;
    padding: 0 15px;
}
.share_links{
    display: flex;
    align-items: center;
    margin-top: 10px;
    .share_btn{
        cursor: pointer;
        width: 35px;
        height: 35px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #eff2f5;
        border-radius: 50%;
        img{
            max-width: 18px;
            height: auto;
        }
        &:not(:last-child){
            margin-right: 8px;
        }
    }
}
</style>