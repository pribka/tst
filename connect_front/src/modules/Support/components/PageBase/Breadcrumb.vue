<template>
    <div class="breadcrumb">
        <router-link :to="initRoute" tag="div" class="breadcrumb__item">
            {{ $t('support.companyWiki') }}
        </router-link>
        <router-link
            v-for="item in breadcrumb"
            :key="item.id"
            tag="div"
            :to="getRoute(item)"
            class="breadcrumb__item"
            :class="item.last && 'last'"
            @click.native="handleClick(item)">
            {{ item.name }}
        </router-link>
    </div>
</template>

<script>
export default {
    props: {
        activePage: {
            type: Object,
            required: true
        },
        pageType: {
            type: String,
            default: ''
        },
        clearActiveLinks: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        initRoute() {
            return {
                path: '/company-wiki',
                query: this.$route.query
            }
        },
        breadcrumb() {
            if(this.pageType === 'sections') {
                return [
                    {
                        id: this.activePage.id,
                        name: this.activePage.name,
                        type: 'sections',
                        last: true
                    }
                ]
            }
            if(this.pageType === 'chapters') {
                return [
                    {
                        id: this.activePage.sections[0].id,
                        name: this.activePage.sections[0].name,
                        type: 'sections'
                    },
                    {
                        id: this.activePage.id,
                        name: this.activePage.name,
                        type: 'chapters',
                        last: true
                    }
                ]
            }
            if(this.pageType === 'pages') {
                return [
                    {
                        id: this.activePage.section[0].id,
                        name: this.activePage.section[0].name,
                        type: 'sections'
                    },
                    {
                        id: this.activePage.chapter[0].id,
                        name: this.activePage.chapter[0].name,
                        type: 'chapters'
                    },
                    {
                        id: this.activePage.id,
                        name: this.activePage.name,
                        type: 'pages',
                        last: true
                    }
                ]
            }
            return []
        }
    },
    methods: {
        handleClick(page) {
            if(!page.last) {
                this.clearActiveLinks()
            }
        },
        getRoute(page) {
            if(page.last)
                return this.$route.fullPath

            return {
                name: 'company-wiki',
                params: {
                    wikiType: page.type,
                    wikiId: String(page.id)
                },
                query: this.$route.query
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.breadcrumb{
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    &__item{
        display: flex;
        align-items: center;
        color: var(--gray);
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
        &:not(.last){
            cursor: pointer;
            &:hover{
                color: var(--blue);
            }
        }
        &:not(:last-child){
            &::after{
                font-family: 'icomoon' !important;
                speak: never;
                font-style: normal;
                font-weight: normal;
                font-variant: normal;
                text-transform: none;
                line-height: 1;
                -webkit-font-smoothing: antialiased;
                -moz-osx-font-smoothing: grayscale;
                content: "\ec7a";
                display: block;
                margin: 0 5px;
                color: var(--gray);
            }
        }
    }
}
</style>
