<template>
    <div>
        <PageTitle title="Бизнес-процессы" />
        <MainList />
    </div>
</template>

<script>
import MainList from '../components/MainList.vue'
import PageTitle from '../components/PageTitle.vue'
export default {
    components: {
        MainList,
        PageTitle
    }
}
</script>