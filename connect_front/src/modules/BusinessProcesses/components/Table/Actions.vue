<template>
    <a-dropdown>
        <a-menu slot="overlay">
            <a-menu-item 
                key="1" 
                @click="share()">
                Поделиться
            </a-menu-item>
            <!--<a-menu-item key="2">
                Редактировать
            </a-menu-item>-->
            <template v-if="isAuthor">
                <a-menu-divider />
                <a-menu-item 
                    key="3" 
                    class="text_red"
                    @click="deleteHandler(record)">
                    Удалить
                </a-menu-item>
            </template>
        </a-menu>
        <a-button
            :loading="actionLoader && actionLoader[record.id] ? true : false"
            type="link" 
            icon="menu" 
            class="text_current" />
    </a-dropdown>
</template>

<script>
import { mapState } from 'vuex'
export default {
    props: {
        record: {
            type: Object,
            required: true
        },
        deleteHandler: {
            type: Function,
            default: () => {}
        },
        actionLoader: {
            type: Object,
            default: () => null
        },
        updateModel: {
            type: String,
            default: 'main'
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        isAuthor() {
            if(this.user && this.user.id === this.record.owner.id) {
                return true
            } else
                return null
        }
    },
    methods: {
        share() {
            this.$store.commit('share/SET_SHARE_PARAMS', {
                model: 'processes.FinancialApplicationModel',
                shareId: this.record.id,
                object: this.record,
                bodySelector: '.task_body_wrap',
                shareUrl: `${window.location.origin}/ru/dashboard?bprocess=${this.record.id}`,
                shareTitle: `Заявка - ${this.record.name}`
            })
        }
    }
}
</script>