<template>
    <div class="flex items-center" :class="position">
        <a-pagination
            :show-size-changer="pageSizeOptions.length > 1"
            :page-size="pageSize"
            :pageSizeOptions="pageSizeOptions"
            class="pager_wrapper"
            :current="page"
            :defaultPageSize="Number(size)"
            @showSizeChange="sizeSwicth"
            @change="changeSwicth"
            :total="Number(count)"
            show-less-items>
            <template slot="buildOptionText" slot-scope="props">
                {{ props.value }}
            </template>
        </a-pagination>
    </div>
</template>

<script>
export default {
    name: 'PagerWidget',
    props: {
        hash: {
            type: Boolean,
            default: true
        },
        count: {
            type: Number,
            required: true
        },
        pageSizeOptions: {
            type: Array,
            default: () => ['15', '30', '50']
        },
        position: {
            type: String,
            default: 'justify-end'
        },
        defaultSize: {
            type: Number,
            default: 15
        },
        changeSize: {
            type: Function,
            default: () => {}
        },
        changePage: {
            type: Function,
            default: () => {}
        },
        scrollElements: {
            type: Array,
            default: () => []
        },
        pageSize: {
            type: Number,
            required: true
        },
        // reactiveOptions: {
        //     type: Object,
        //     required: true
        // },
        page: {
            type: Number
        }
    },
    data() {
        return {
            // page: 1,
            size: this.defaultSize,
            // pageSize: this.page_size
        }
    },
    methods: {
        scrollTop() {
            if(this.scrollElements.length) {
                this.scrollElements.forEach(elem => {
                    let scrollElements = document.querySelectorAll(elem)
                    if(scrollElements.length)
                        scrollElements.forEach(scrollElem => scrollElem.scrollTop = 0)
                })
            } else
                document.body.scrollIntoView({ behavior: 'smooth', block: 'start' })
        },
        sizeSwicth(current, pageSize) {
            if(this.hash) {
                this.sizeChangeHash(pageSize)
            } else {
                this.scrollTop()
                // RETURN
                // this.page = 1
                this.changePage(1)
                this.changeSize(pageSize)
            }
        },
        sizeChangeHash(pageSize) {
            let query = Object.assign({}, this.$route.query)
            if(query.page_size) {
                if(Number(query.page_size) !== pageSize) {
                    this.scrollTop()
                    query.page_size = pageSize
                    if(query.page)
                        delete query.page
                    this.$router.push({query})
                }
            } else {
                this.scrollTop()
                query.page_size = pageSize
                if(query.page)
                    delete query.page
                this.$router.push({query})
            }
        },
        changeSwicth(page) {
            if(this.hash) {
                this.changePaginationHash(page)
            } else {
                this.scrollTop()
                this.changePage(page)
            }
        },
        changePaginationHash(page) {
            let query = Object.assign({}, this.$route.query)
            if(query.page) {
                if(Number(query.page) !== page) {
                    this.scrollTop()
                    // RETURN
                    // query.page = page
                    this.$router.push({query})
                }
            } else {
                this.scrollTop()
                // RETURN
                // query.page = page
                this.$router.push({query})
            }
        }
    }
}
</script>
