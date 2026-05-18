<template>
    <div class="chat_aside__header flx">
        <a-input-search
            :placeholder="$t('chat.search')"
            v-model="searchText"
            allowClear
            :size="isMobile ? 'large' : 'default'"
            @change="chatSearch"/>
        <a-button
            v-if="!isMobile"
            v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }"
            :content="$t('chat.new_chat')"
            @click="$store.commit('chat/TOGGLE_CREATE_CHAT', true)"
            class="ml-2  new_chat_button px-3 lg:px-0 flex items-center justify-center"
            type="link">
            <i class="fi fi-rr-edit"></i>
        </a-button>
    </div>
</template>

<script>
import { debounce } from "lodash";
export default {
    name: "ChatHeader",
    computed: {
        searchLoading:{
            get(){
                return this.$store.state.chat.searchLoading
            },

            set(value){
                this.$store.commit('chat/setValueState', {name: 'searchLoading', value})
            }
        },
        searchText:{
            get(){
                return this.$store.state.chat.searchText
            },

            set(value){
                this.$store.commit('chat/setValueState', {name: 'searchText', value})
            }
        },
       
        searchPage:{
            get(){
                return this.$store.state.chat.searchPage
            },

            set(value){
                this.$store.commit('chat/setValueState', {name: 'searchPage', value})
            }
        },
        searchStart:{
            get(){
                return this.$store.state.chat.searchStart
            },

            set(value){
                this.$store.commit('chat/setValueState', {name: 'searchStart', value})
            }
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    methods: {
        chatSearch:debounce(async function() {
            if(this.searchText.length > 1) {
                this.searchLoading = true
                this.searchStart = true
                try {
                    this.$store.commit('chat/CLEAR_SEARCH_RESULT')
                   
                    this.$store.dispatch('chat/search', {val: this.searchText, page: this.searchPage})
                } catch(e) {}
                finally{
                    setTimeout(() => {
                        this.searchLoading = false
                    }, 1000);
                }
                
            } else{ 
                this.$store.commit('chat/CLEAR_SEARCH_RESULT')
                this.searchStart = false
            }
        },500
        )},
    
}
</script>

<style lang="scss" scoped>
.chat_aside__header{
    @media (max-width: 900px) {
        padding: 10px 15px;
    }
}
</style>