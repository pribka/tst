<template>
    <div>
        <ArticlesDrawerActions />
        <OfficialDrawerActions />
        <WebinarDrawerActions />
        <QuestionDrawerActions />
        <KnowledgebaseDrawerActions />
        <PartitionDrawerActions />
        <OrganDrawerActions />
        <TagDrawerActions />
        <NewsDrawerActions />
        <NewsFinanceDrawerActions />
    </div>
</template>

<script>
export default {
    components: {
        ArticlesDrawerActions: () => import('./Articles/ArticlesDrawerActions.vue'),
        NewsDrawerActions: () => import('./News/NewsDrawerActions.vue'),
        NewsFinanceDrawerActions: () => import('./NewsFinance/NewsFinanceDrawerActions.vue'),
        OfficialDrawerActions: () => import('./Official/OfficialDrawerActions.vue'),
        WebinarDrawerActions: () => import('./Webinar/WebinarDrawerActions.vue'),
        QuestionDrawerActions: () => import('./Question/QuestionDrawerActions.vue'),
        KnowledgebaseDrawerActions: () => import('./Knowledgebase/KnowledgebaseDrawerActions.vue'),
        PartitionDrawerActions: () => import('./Partition/PartitionDrawerActions.vue'),
        OrganDrawerActions: () => import('./Organ/OrganDrawerActions.vue'),
        TagDrawerActions: () => import('./Tag/TagDrawerActions.vue')
    }
}
</script>