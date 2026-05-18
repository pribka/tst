<template>
    <div>
        <div class="flex items-center">
            <Profiler
                @click="openDrawer"
                class="cursor-pointer"
                :avatarSize="22"
                :showTaskButton="true"
                :showUserName="showUserName"
                nameClass="text-sm"
                :user="item" />

            <UserDrawer
                v-model="operator"
                :id="record.id"
                :taskId="record.id"
                hide
                :title="$t('task.change_person')"
                :class="showUserName && 'ml-2'"
                @input="update"/>
        </div>

    </div>
</template>

<script>
import { mapMutations, mapState } from 'vuex'
import eventBus from "@/utils/eventBus"
export default {
    components: {
        UserDrawer: () => import("./UserDrawer")
    },
    props: {
        item: {
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
            if(this.user && this.user.id === this.record.owner.id || this.user.id === this.record.operator.id ||  this.user.contractor_list.includes(this.record.contractor.id)   ) {
                return true
            }
            else{
                return false
            }

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
            if(this.myTask)
                eventBus.$emit('open_user_task_drawer', this.record.id)
        },
        async update(val){
            try{
                this.loading = true

                const {data} =  await  this.$http.patch(`/tasks/task/${this.record.id}/update/`, {operator: val.id})
                this.UPDATE_TASK(data)
            }
            catch(e){
                console.error(e)
            }
            finally{
                this.loading = false
            }
        }
    }

}
</script>

<style>

</style>