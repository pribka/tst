<template>
    <div v-if="user">
        <div class="my_personal">
            <div class="item">
                <div class="label">
                    Идентификатор:
                </div>
                <div class="val">
                    {{ user.id }}
                </div>
            </div>
            <div 
                v-if="user.last_name" 
                class="item">
                <div class="label">
                    Фамилия:
                </div>
                <div class="val">
                    {{ user.last_name }}
                </div>
            </div>
            <div 
                v-if="user.first_name" 
                class="item">
                <div class="label">
                    Имя:
                </div>
                <div class="val">
                    {{ user.first_name }}
                </div>
            </div>
            <div 
                v-if="user.middle_name" 
                class="item">
                <div class="label">
                    Отчество:
                </div>
                <div class="val">
                    {{ user.middle_name }}
                </div>
            </div>
            <div 
                v-if="user.email" 
                class="item">
                <div class="label">
                    E-mail:
                </div>
                <div class="val">
                    {{ user.email }}
                </div>
            </div>
            <div 
                v-if="user.phone" 
                class="item">
                <div class="label">
                    Телефон:
                </div>
                <div class="val">
                    {{ user.phone }}
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { mapState } from 'vuex'
export default {
    computed: {
        ...mapState({
            user: state => state.user.user
        })
    }
}
</script>

<style lang="scss">
.my_personal{
    .item{
        // display: flex;
        &:not(:last-child){
            margin-bottom: 15px;
        }
        .label{
            min-width: 200px;
            font-weight: 700;
        }
        .val{
            
        }
    }
}
</style>