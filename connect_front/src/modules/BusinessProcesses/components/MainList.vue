<template>
    <div class="process">
        <div 
            v-if="loading" 
            class="flex justify-center">
            <a-spin />
        </div>
        <div class="process_grid grid grid-cols-5 gap-4">
            <router-link 
                v-for="item in list" 
                :key="item.id"
                :to="{ name: 'business_processes_list', params: { processId: item.id } }"
                class="item flex items-center">
                <div class="ava mr-4">
                    <a-avatar 
                        :size="50"
                        icon="bars"
                        :src="item.image" />
                </div>
                <div class="name font-semibold">
                    {{ item.name }}
                </div>
            </router-link>
        </div>
    </div>
</template>

<script>
export default {
    computed: {
        list() {
            return this.$store.state.bprocess.processList
        }
    },
    data() {
        return {
            loading: false
        }
    },
    created() {
        this.getList()
    },
    methods: {
        async getList() {
            try {
                this.loading = true
                await this.$store.dispatch('bprocess/getMainList')
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.process_grid{
    .item{
        border-radius: var(--borderRadius);
        padding: 10px;
        background: var(--mainBg);
        cursor: pointer;
        .name{
            color: var(--text);
        }
    }
}
</style>