<template>
    <div>
        <div class="flex items-center">
            <Profiler
                @click="openDrawer"
                class="cursor-pointer"
                :avatarSize="22"
                :showUserName="showUserName"
                nameClass="text-sm"
                :user="text" />

            <UserDrawer
                id="changeUser"
                ref="changeUserRef"
                @input="update"
                hide
                title="Выбрать пользователя"/>
        </div>
    </div>
</template>

<script>
import { mapMutations, mapState } from 'vuex'
import eventBus from "@/utils/eventBus"
export default {
    components: {
        UserDrawer: () => import("@apps/DrawerSelect/index.vue")
    },
    props: {
        text: {
            type: [Object, String],
            required: true
        },
        record: {
            type: [Object, String],
            required: true
        },
        showUserName: {
            type: Boolean,
            default: true
        },
        pageName: {
            type: String,
            default: ''
        }

    },
    data(){
        return{
            operator: "",
            loading: false
        }
    },
    computed:{
        ...mapState({
            user: state => state.user.user,
        }),
        myTask() {
            return this.user?.id === this.record?.owner?.id || 
                this.user?.id === this.record?.operator?.id ||  
                this.user?.contractor_list?.includes(this.record?.contractor?.id)
        },
        filtersUserDrawer(){
            if(this?.record.contractor){
                return {contractor_profile__contractor: this.record.contractor?.id}
            }
            return null
        },
    },
    methods:{
        ...mapMutations({
            UPDATE_TASK: "task/UPDATE_TASK"
        }),
        openDrawer(){
            if(this.record?.can_update_operator) {
                this.$refs?.changeUserRef?.open()
            }
        },
        update(user){
            const payload = {
                operator: user.id
            }
            const url = `/tasks/task/${this.record.id}/update_operator/`
               
            this.$http.put(url, payload)
                .then(({ data }) => {
                    // this.$store.commit('task/UPDATE_TASK', data)
                    eventBus.$emit(`table_row_${this.pageName}`, {
                        action: 'update',
                        row: data
                    })
                })
                .catch(error => {
                    console.error(error)
                    this.$message.error('Не удалось совершить изменения')
                })

        }
    }

}
</script>