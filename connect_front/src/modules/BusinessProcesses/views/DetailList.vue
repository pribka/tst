<template>
    <div class="h-full table_list">
        <div class="top_block">
            <PageTitle 
                :title="detailTitle"
                back
                :loading="detailLoading"
                wrapClass="pb-2" />
            <div class="page_header pb-4 flex items-center">
                <a-button 
                    type="primary"
                    icon="plus"
                    size="large"
                    class="mr-2"
                    @click="openCreate()">
                    Добавить
                </a-button>
                <slot />
            </div>
        </div>
        <div class="table_block">
            <Table 
                :page_name="page_name"
                :id="id" 
                :updateModel="updateModel" />
        </div>
    </div>
</template>

<script>
import PageTitle from '../components/PageTitle'
import Table from '../components/Table'
export default {
    components: {
        PageTitle,
        Table
    },
    props: {
        updateModel: {
            type: String,
            default: 'main'
        },
        page_name: {
            type: [String, Number],
            default: ''
        }
    },
    computed: {
        id() {
            return this.$route.params.processId
        }
    },
    data() {
        return {
            detail: null,
            detailTitle: '',
            detailLoading: false
        }
    },
    created() {
        this.getDetail()
    },
    methods: {
        openCreate() {
            this.$store.commit('bprocess/SET_EDIT_DRAWER', true)
            this.$store.commit('bprocess/SET_UPDATE_MODEL', this.updateModel)
        },
        async getDetail() {
            try {
                this.detailLoading = true
                const { data } = await this.$http.get(`/processes/business_process_template/${this.id}/`)
                if(data) {
                    this.detail = data
                    this.detailTitle = data.name
                }
            } catch(e) {
                console.log(e)
                this.$router.push({ name: 'business_processes_main' })
                this.$message.error('Ошибка')
            } finally {
                this.detailLoading = false
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.table_list{
    display: flex;
    flex-direction: column;
    .table_block{
        flex-grow: 1;
    }
}
</style>