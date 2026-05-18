<template>
    <div class="setting_lists">
        <div 
            class="other_item" 
            :class="miniMenu && 'disabled'">
            <div
                class="label"
                @click="setHideMenu()">
                Скрыть меню
            </div>
            <a-switch 
                v-model="hideMenu" 
                size="large" 
                :disabled="miniMenu ? true : false" />
        </div>
        <div 
            class="other_item" 
            :class="hideMenu && 'disabled'">
            <div
                class="label"
                @click="setMiniMenu()">
                Маленькое меню
            </div>
            <a-switch 
                v-model="miniMenu" 
                size="large" 
                :disabled="hideMenu ? true : false" />
        </div>
        <div class="other_item">
            <div
                class="label"
                @click="rightMenu = !rightMenu">
                Меню справа
            </div>
            <a-switch 
                v-model="rightMenu" 
                size="large" />
        </div>
        <div class="other_item">
            <div
                class="label"
                @click="hideFooter = !hideFooter">
                Скрыть подвал
            </div>
            <a-switch 
                v-model="hideFooter" 
                size="large" />
        </div>
        <div class="other_item">
            <div
                class="label"
                @click="eyeVersion = !eyeVersion">
                Версия для слабовидящих
            </div>
            <a-switch 
                v-model="eyeVersion" 
                size="large" />
        </div>
        <!--<div class="other_item">
                        <a-switch v-model="documentReverse" size="small" />
                        <div
                            class="label"
                            @click="documentReverse = !documentReverse">
                            Форма документа слева
                        </div>
                    </div>
                    <div class="other_item">
                        <a-switch size="small" />
                        <div
                            class="label">
                            Ночной режим
                        </div>
                    </div>-->
    </div>
</template>

<script>
export default {
    computed: {
        hideFooter: {
            get() {
                return this.$store.state.hideFooter
            },
            set(val) {
                this.$store.commit('TOGGLE_HIDE_FOOTER', val)
            }
        },
        hideMenu: {
            get() {
                return this.$store.state.hideMenu
            },
            set(val) {
                this.$store.commit('TOGGLE_HIDE_MENU', val)
            }
        },
        miniMenu: {
            get() {
                return this.$store.state.miniMenu
            },
            set(val) {
                this.$store.commit('TOGGLE_MINI_MENU', val)
            }
        },
        rightMenu: {
            get() {
                return this.$store.state.rightMenu
            },
            set(val) {
                this.$store.commit('TOGGLE_RIGHT_MENU', val)
            }
        },
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
        }
    },
    methods: {
        setHideMenu() {
            if(!this.miniMenu)
                this.hideMenu = !this.hideMenu
        },
        setMiniMenu() {
            if(!this.hideMenu)
                this.miniMenu = !this.miniMenu
        }
    }
}
</script>

<style lang="scss">
.setting_lists{
    .other_item{
        display: flex;
        align-items: center;
        justify-content: space-between;
        &:not(:last-child){
            border-bottom: 1px solid var(--border2);
        }
        &.disabled{
            cursor: default;
            .label{
                opacity: 0.6;
            }
        }
        &:not(:last-child){
            margin-bottom: 8px;
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