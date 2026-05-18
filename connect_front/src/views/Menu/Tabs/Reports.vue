<template>
    <div>
        <a-button :loading="loading" type="primary" @click="getReport">Сформировать отчет</a-button>
    </div>
</template>

<script>
export default {
    data(){
        return {
            loading: false,
            file: null,
            docType: 'office'
        }
    },
    methods: {
        async getReport(){
            try{ 
                this.loading = true
                window.open(process.env.VUE_APP_URL + '/api/v1/crm/get_report/', '_blank')
                
                setTimeout(() => {
                
                }, 3000);
            }catch(e){
                console.log(e)
            }
            finally {
                this.loading = false
            }
        }
    }
}
</script>

<style>

</style>