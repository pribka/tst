<template>
    <div>
        <a-tooltip 
            overlayClassName="button_tooltip"
            destroyTooltipOnHide
            title="HELP — вопросы, предложения, замечания">
            <div 
                class="add_button"
                @click="openIssueModal()">
                <i class="fi fi-rr-headphones"></i>
            </div>
        </a-tooltip>
        <!-- <a-dropdown>
            <div class="add_button">
                <i class="fi fi-rr-question"></i>
            </div>
            <a-menu 
                slot="overlay" 
                class="add_drop">
                <a-menu-item 
                    key="techSupportKey" 
                    @click="openIssueModal()">
                    <i class="fi fi-rr-headphones"></i>
                    Вопрос в ТП
                </a-menu-item>
                <a-menu-item 
                    key="1" 
                    @click="createNews()">
                    <i class="fi fi-rr-browser"></i>
                    Создать новость
                </a-menu-item>
                <a-menu-item 
                    key="2" 
                    @click="createTask()">
                    <i class="fi fi-rr-list-check"></i>
                    Создать задачу
                </a-menu-item>
                <a-menu-item 
                    key="3" 
                    @click="createMeeting()">
                    <i class="fi fi-rr-video-camera"></i>
                    Создать собрание
                </a-menu-item>
                <a-menu-item 
                    key="4" 
                    @click="createGroup()">
                    <i class="fi fi-rr-users"></i>
                    Создать группу
                </a-menu-item>
                <a-menu-item 
                    key="5" 
                    @click="createProject()">
                    <i class="fi fi-rr-file-chart-line"></i>
                    Создать проект
                </a-menu-item>
            </a-menu>
        </a-dropdown> -->
        <TechSupport 
            ref="techSupport"/>
    </div>
</template>

<script>
import ru from './lang/ru.json'

export default {
    name: 'CommandButton',
    components: {
        TechSupport: () => import('./TechSupport.vue')
    },
    methods: {
        // createTask() {
        //     this.$store.dispatch('task/sidebarOpen', {})
        // },
        // createMeeting() {
        //     this.$store.commit('meeting/SET_EDIT_DRAWER', { show: true, model: 'main' })
        // },
        // createGroup() {
        //     this.$router.replace({
        //         query: { createGroup: true  }
        //     })
        // },
        // createProject() {
        //     this.$router.replace({
        //         query: { createProject: true }
        //     })
        // },
        // createNews() {
        //     this.$store.commit('dashboard/TOGGLE_EDIT_DRAWER', true)
        // }
        openIssueModal() {
            this.$nextTick(() => {
                this.$refs.techSupport.openIssueModal()
            })
        }
    },
    created() {
        if(!this.$i18n.messages.ru.order) {
            const messages = {
                ...this.$i18n.messages.ru,
                ...ru
            }
            this.$i18n.setLocaleMessage('ru', messages)
        }
    },

}
</script>

<style lang="scss">
.button_tooltip {
    .ant-tooltip-inner{
        color: var(--text1);
        background-color: #fff;
    }
}
</style>

<style lang="scss">
.add_drop{
    &::v-deep{
        .ant-dropdown-menu-item{
            display: flex;
            align-items: center;
            i{
                margin-right: 6px;
            }
        }
    }
}
.add_button{
    border-radius: 50%;
    background: var(--blue);
    width: 50px;
    height: 50px;
    position: fixed;
    bottom: 30px;
    right: 30px;
    z-index: 10;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-size: 28px;
    cursor: pointer;
    animation: pulse 2s infinite;
    transform: scale(1);
}
@keyframes pulse {
  0% {
    transform: scale(0.95);
    box-shadow: 0 0 0 0 rgba(29, 101, 192, 0.7);
  }
  
  70% {
    transform: scale(1);
    box-shadow: 0 0 0 15px rgba(29, 101, 192, 0);
  }
  
  100% {
    transform: scale(0.95);
    box-shadow: 0 0 0 0 rgba(29, 101, 192, 0);
  }
}
</style>