<template>
    <div class="search_block" ref="searchBlock">
        <div class="ico">
            <a-spin v-if="searchLoading" size="small" />
            <i v-else class="fi fi-rr-search"></i>
        </div>
        <template v-if="multiple">
            <a-select
                show-search
                :value="searchValue"
                :placeholder="$t('search_employee')"
                style="width: 100%;"
                size="large"
                :default-active-first-option="false"
                :show-arrow="false"
                :filter-option="false"
                :not-found-content="null"
                :getPopupContainer="getPopupContainer"
                @search="onSearch"
                dropdownClassName="custom-search-dropdown"
                @popupScroll="popupScroll"
                @dropdownVisibleChange="onDropdownVisibleChange"
                :open="selectOpen">
                <a-select-option v-for="user in searchList" :key="user.id">
                    <div @click.stop.prevent="handleOptionClick($event, user)">
                        <UserItem 
                            checkedClass="all-users-checked-class"
                            class="user-item"
                            :multiple="multiple"
                            :checkSelected="checkSelected"
                            :itemSelect="itemSelect"
                            :item="user" />
                    </div>
                </a-select-option>
            </a-select>
        </template>
        <template v-else>
            <a-radio-group v-model="selectedUserID" class="w-full">
                <a-select
                    show-search
                    :value="searchValue"
                    :placeholder="$t('search_employee')"
                    style="width: 100%;"
                    size="large"
                    :default-active-first-option="false"
                    :show-arrow="false"
                    :filter-option="false"
                    :not-found-content="null"
                    :getPopupContainer="getPopupContainer"
                    @search="onSearch"
                    dropdownClassName="custom-search-dropdown"
                    @popupScroll="popupScroll"
                    @dropdownVisibleChange="onDropdownVisibleChange"
                    :open="selectOpen">
                    <a-select-option v-for="user in searchList" :key="user.id">
                        <div @click.stop.prevent="handleOptionClick($event, user)">
                            <UserItem 
                                checkedClass="all-users-checked-class"
                                class="user-item"
                                :multiple="multiple"
                                :checkSelected="checkSelected"
                                :itemSelect="itemSelect"
                                :item="user" />
                        </div>
                    </a-select-option>
                </a-select>
            </a-radio-group>
        </template>
    </div>
</template>

<script>
import UserItem from './UserItem.vue'
let timer;
export default {
    name: "UserSearch",
    components: {
        UserItem
    },
    props: {
        multiple: {
            type: Boolean,
            default: false
        },
        checkSelected: {
            type: Function,
            default: () => {}
        },
        itemSelect: {
            type: Function,
            default: () => {}
        },
        singleSelected: {
            type: [String, null],
            default: null
        }
    },
    data() {
        return {
            searchLoading: false,
            searchList: [],
            searchValue: undefined,
            selectOpen: false,
            page: 1,
            hasMore: true,
            searchText: '',
        }
    },
    computed: {
        selectedUserID: {
            get() {
                return this.singleSelected
            },
            set(val) {
                const selectedUser = this.searchList.find(user => user.id === val)
                if (selectedUser) {
                    this.itemSelect(selectedUser)
                }
            }
        }
    },
    methods: {
        getPopupContainer() {
            return this.$refs.searchBlock
        },
        handleOptionClick(e, user) {},
        onDropdownVisibleChange(open) {
            this.selectOpen = open;
            this.page = 1;
            this.searchList = [];
            this.hasMore = open;
            if (open && this.searchText) {
                this.loadMore();
            }
        },
        async loadMore(append = true) {
            if (!this.hasMore || this.searchLoading) return;
            this.searchLoading = true;

            try {
                let params = {
                    page_size: 10,
                    page: this.page,
                    search: this.searchText,
                }
                const { data } = await this.$http.get('user/list/', { params })
                const newItems = data.results || [];
                if (append) {
                    this.searchList = [...this.searchList, ...newItems];
                } else {
                    this.searchList = newItems;
                }
                this.hasMore = Boolean(data.next)
                this.page++;
            } catch (e) {
                console.error(e);
            } finally {
                this.searchLoading = false;
            }
        },
        popupScroll(event) {
            if (this.hasMore) {
                const { target } = event
                if (target && (target.scrollTop + target.offsetHeight >= target.scrollHeight - 10))
                    this.loadMore();
            }
        },
        onSearch(text) {
            this.searchText = text;
            clearTimeout(this.timer);
            this.timer = setTimeout(() => {
                if (text.trim()) {
                    this.searchList = [];
                    this.page = 1;
                    this.hasMore = true;
                    this.loadMore(false);
                } else {
                    this.searchList = [];
                    this.hasMore = false;
                }
            }, 500);
        }
    }
}
</script>

<style lang="scss" scoped>
.search_block{
    position: relative;
    .ico{
        position: absolute;
        height: 36px;
        right: 15px;
        top: 0px;
        z-index: 5;
        display: flex;
        align-items: center;
        font-size: 14px;
        color: var(--gray);
    }
    &::v-deep{
        .ant-select{
            &.ant-select-lg{
                .ant-select-selection--single{
                    height: 36px;
                }
                .ant-select-selection__rendered{
                    line-height: 36px;
                    margin-left: 15px;
                    margin-right: 40px;
                }
            }
        }
        .ant-select-selection {
            border: none !important;
            background: rgba(240, 241, 247, 1) !important;
            border-radius: 8px;
            box-shadow: none !important;
            }
            .custom-search-dropdown {                           
                border-radius: 8px;
                .user-item {
                    &:hover {
                        background: rgba(240, 241, 247, 1) !important;
                    }
                }
                .ant-select-dropdown-menu {
                    max-height: 240px;
                    overflow: auto;
                }
                .ant-select-dropdown-menu-item {
                    padding: 0 !important;
                    border: none !important;
                    box-shadow: none !important;

                    &:hover,
                    &.ant-select-dropdown-menu-item-selected,
                    &.ant-select-dropdown-menu-item-active {
                        background: transparent !important;
                        box-shadow: none !important;
                    }
                    &:not(:last-child){
                        margin-bottom: 4px;
                    }
                }
            }
    }
}
</style>