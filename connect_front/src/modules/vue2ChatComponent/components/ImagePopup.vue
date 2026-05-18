<template>
    <a-modal
        :visible="popupActive"
        @cancel="popupActive = false">
        <div class="flex items-center justify-center">
            <img
                v-if="selectImage"
                :src="selectImage.path"
                :alt="selectImage.name" />
        </div>
        <template slot="footer">
            <a-button @click="popupActive = false">
                {{$t('close')}}
            </a-button>
        </template>
    </a-modal>
</template>

<script>
import {mapState} from 'vuex'
export default {
    name: "ChatImagePopup",
    computed: {
        ...mapState({
            selectImage: state => state.chat.selectImage
        }),
        popupActive: {
            get() {
                return this.$store.state.chat.imagePopup
            },
            set(val) {
                this.$store.commit('chat/SET_IMAGE_POPUP', val)
            }
        }
    },
}
</script>