<template>
    <div class="flex items-center rounded">
        <slot name="grab"></slot>
        
        <div class="flex-grow">
            {{ item.title }}
        </div>
        <a-button 
            type="ui" 
            ghost
            shape="circle"
            class="text_red" 
            flaticon
            icon="fi-rr-trash"
            @click="removeItem">
        </a-button>
    </div>
</template>

<script>
export default {
    props: {
        item: {
            type: Object,
            required: true,
        },
    },

    data() {
        return {
            edit: false,
            newCustomTitle: '',
        };
    },

    computed: {
        hasCustomTitle() {
            return (
                this.item.customTitle &&
        this.item.customTitle !== this.item.title
            );
        },
    },

    methods: {
        startEdit() {
            // this.edit = true;
            // this.newCustomTitle = this.item.customTitle || this.item.title;
        },
        cancelEdit() {
            this.edit = false;
        },
        save() {
            this.item.customTitle = this.newCustomTitle;
            this.cancelEdit();
        },
        setDefaultName() {
            this.item.customTitle = this.item.title;
        },
        removeItem() {
            this.$store.commit('reports/REMOVE_LIST_ITEM', { listKey: 'grouping', item: this.item })
        }

    },
};
</script>
