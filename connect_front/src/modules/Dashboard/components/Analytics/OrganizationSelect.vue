<template>
    <div class="flex">
        <a-select
            v-for="select in filters.selects"
            :key="select.id"
            :allowClear="true"
            class="w-full"
            :showSearch="windowWidth > 786 ? true : false"
            :maxTagCount="windowWidth > 786 ? 3 : 10"
            size="default"
            :placeholder="$t('dashboard.parent_organization_placeholder')"
            :loading="select.loading"
            v-model="select.value"
            dropdownClassName="filter_i_select"
            :getPopupContainer="trigger => trigger.parentElement"
            @select="selectHandler(select.id)"
            :filter-option="false"
            @popupScroll="scrollHandler($event, select.id)">
            <a-select-option
                v-for="option in select.options.list"
                :key="option.id"
                :value="option.id">
                {{ option.string_view ? option.string_view : option.name }}
            </a-select-option>
            <div slot="notFoundContent" class="flex justify-center p-1">
                <a-empty :description="$t('dashboard.no_data')" />
            </div>
        </a-select>
    </div>
</template>

<script>
export default {
    props: {
        filters: {
            type: Object,
            required: true
        },
        parentOrganization: {
            type: String,
            default: null
        }
    },
    data() {
        return {
            rootOrganizations: {
                loading: false,
                page: 0,
                next: true,
                list: []
            },
            windowWidth: 0,
            start: null,
            end: null,
        }
    },
    computed: {
        parentId() {
            return this.filters?.selects?.[0]?.parent || null
        }
    },
    created() {
        const selects = this.filters.selects.find(selectItem => selectItem.id === 'parent')
        const isOptionListEmpty = !selects.options.list?.length
        if (isOptionListEmpty) {
            this.initParentOptions()
        }
    },
    methods: {
        async initParentOptions(organizationId) {
            const select = this.filters.selects.find(selectItem => selectItem.id === 'parent')
            this.resetSelectOptions('parent')
            select.loading = true
            const options = await this.getSelectOptions('parent')
            select.loading = false

            select.options.list = options
            if (organizationId) {
                select.value = JSON.parse(JSON.stringify(organizationId))
            } else {
                select.value = select.options.list[0].id
            }
            this.selectHandler('parent')
        },
        resetSelectOptions(selectId) {
            const select = this.filters.selects.find(selectItem => selectItem.id === selectId)
            if (select) {
                select.options.page = 0
                select.next = true
                select.loading = false
    
                select.options.list = []
            }
        },
        async selectHandler(selectId) {
            // const displaySelect = this.filters.selects.find(selectItem => selectItem.id === 'displayed')
            // if (displaySelect) {
            //     this.resetSelectOptions('displayed')

            //     displaySelect.loading = true
            //     const options = await this.getSelectOptions('displayed')
            //     displaySelect.loading = false

            //     displaySelect.options.list.push(...options)
            //     displaySelect.value = displaySelect.options.list[0].id
            // }
            this.$emit('updateFilters')
        },
        async getSelectOptions(selectId) {
            const url = this.getSelectURL();
            const select = this.filters.selects.find(selectItem => selectItem.id === selectId);
            select.options.page++;
            const params = {
                page: select.options.page,
                page_size: 10,
                page_name: 'analytics_widget'
            };
            try {
                const { data } = await this.$http.get(url, { params });
                select.options.next = data.next;
                if (!data?.results) {
                    console.error(this.$t('dashboard.select_options_error')); // Перевод на русский
                    return [];
                }
                if (this.parentId) {
                    return data.results.map(relation => relation.contractor);
                }
                return data.results;
            } catch(error) {
                console.error(this.$t('dashboard.select_options_fetch_error')); // Перевод на русский
                return [];
            }
        },
        getSelectURL() {
            if (this.parentId) {
                return `/users/my_organizations/${this.parentId}/relations/`;
            }
            return `users/my_organizations/?display=root`;
        },
        async scrollHandler(event, selectId) {
            const target = event.target;
            const select = this.filters.selects.find(selectItem => selectItem.id === selectId);
            const isBottomScrolling = target.scrollTop + target.offsetHeight === target.scrollHeight;

            if (select.options.next && !select.loading && isBottomScrolling) {
                try {
                    select.loading = true;
                    const options = await this.getSelectOptions(selectId);
                    select.options.list.push(...options);
                } catch (error) {
                    console.error(this.$t('dashboard.scroll_data_error'), error); // Перевод на русский
                } finally {
                    select.loading = false;
                }
            }
        },

    }
}
</script>

<style>

</style>