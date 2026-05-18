<template>
    <div class="error_info">
        <h1>Извините, такой страницы не существует</h1>
        <div class="flex items-center justify-center">
            <a-button type="primary" size="large" class="mr-2" @click="goHome()">
                На главную
            </a-button>
            <a-button type="primary" size="large" ghost class="ml-2" @click="routerBack()">
                Вернуться назад
            </a-button>
        </div>
        <div class="image">
            <img src="@/assets/images/error_404.png" />
        </div>
    </div>
</template>

<script>
import { mapState } from 'vuex'
export default {
    metaInfo() {
        return {
            title: 'Страница не найдена',
            bodyAttrs: {
                class: 'error_page_layout'
            }
        }
    },
    computed: {
        ...mapState({
            routers: state => state.navigation.routerList,
            user: state => state.user.user,
        }),
        frontPage() {
            if(this.routers?.length) {
                return this.routers[0].name
            } else
                return ''
        }
    },
    methods: {
        routerBack() {
            this.$router.go(-1)
        },
        goHome() {
            if(this.user)
                this.$router.push({ name: this.frontPage })
            else
                this.$router.push({ name: 'login' })
        }
    }
}
</script>

<style lang="scss">
.error_page_layout{
    overflow: initial;
}
</style>

<style lang="scss" scoped>
.error_info{
    text-align: center;
    h1{
        font-size: 32px;
        margin-bottom: 30px;
        color: #000000;
    }
    .image{
        margin-top: 50px;
        display: flex;
        justify-content: center;
    }
}
</style>