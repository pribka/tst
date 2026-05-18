<template>
    <a-breadcrumb>
        <a-breadcrumb-item
            v-for="item in list"
            :key="item.key">
            <a @click="setCategory(item.key)"> {{ item.title }}</a>
        </a-breadcrumb-item>
    </a-breadcrumb>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    props: {
        category: Object,
    },
    data() {
        return {
            list: [],
        };
    },
    methods: {
        getChildren(item) {
            let { title, key } = item;
            this.list.push({ title, key });
            if (item.children?.length) {
                this.getChildren(item.children[0]);
            }
        },
        setCategory(id){
			 let query = Object.assign({}, this.$route.query)
            query['category'] = id
            delete query['viewGoods']
            this.$router.replace({query})
            eventBus.$emit("update_products_category", id)
                
        }
    },
    created() {
        if(this.category?.key)
            this.getChildren(this.category);
    },
};
</script>

<style></style>
