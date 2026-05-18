<template>
    <div>
        <div class="support_org_select__trigger" @click="openSelect">
            <slot :value="value" :open="openSelect" />
        </div>

        <DrawerTemplate
            v-model="visible"
            :width="windowWidth"
            :wrapClassName="drawerWrapClass"
            :title="$t('Organization')"
            @close="visible = false">
            <div class="support_org_select__content">
                <a-input-search
                    class="search_input"
                    :loading="searchLoading"
                    v-model="search"
                    ref="searchInput"
                    :placeholder="$t('org_name')"
                    @input="onSearch" />

                <div v-if="recentList.length" class="recent_list">
                    <div class="recent_list__label">{{ $t('old_selected') }}</div>
                    <div class="recent_list__items">
                        <div
                            v-for="item in recentList"
                            :key="item.id"
                            :title="item.name"
                            class="recent_list__item cursor-pointer"
                            :class="checkSelected(item)"
                            @click="selectWork(item)">
                            <div v-if="checkSelected(item) === 'active'" class="recent_list__active">
                                <i class="fi fi-rr-check" />
                            </div>
                            <a-avatar :size="28" icon="team" :src="workgroupLogoPath(item)" />
                        </div>
                    </div>
                </div>

                <div class="support_org_select__list">
                    <div
                        v-for="item in workList"
                        :key="item.id"
                        :title="item.name"
                        class="support_org_select__item cursor-pointer"
                        :class="checkSelected(item)"
                        @click="selectWork(item)">
                        <a-avatar :size="28" icon="team" :src="workgroupLogoPath(item)" />
                        <div class="support_org_select__item_name truncate">
                            {{ item.name }}
                        </div>
                    </div>
                    <div v-if="page === 1 && loading" class="flex justify-center py-2">
                        <a-spin size="small" />
                    </div>
                    <infinite-loading
                        ref="orgInfiniteMobile"
                        :identifier="infiniteId"
                        :force-use-infinite-wrapper="infiniteWrapperSelector"
                        @infinite="getWorkList"
                        v-bind:distance="10">
                        <div slot="spinner"><a-spin v-if="page !== 1" size="small" /></div>
                        <div slot="no-more"></div>
                        <div slot="no-results"></div>
                    </infinite-loading>
                </div>
            </div>
            <template #footer>
                <a-button type="ui_ghost" size="large" block @click="visible = false">
                    {{ $t('close') }}
                </a-button>
            </template>
        </DrawerTemplate>
    </div>
</template>

<script>
import DrawerTemplate from '@/components/DrawerTemplate.vue'
import mixin from './mixins'

export default {
    components: {
        DrawerTemplate
    },
    mixins: [mixin],
    computed: {
        drawerWrapClass() {
            return `support_org_select_mobile_drawer_${this._uid}`
        },
        infiniteWrapperSelector() {
            return `.${this.drawerWrapClass} .drawer_body`
        }
    }
}
</script>

<style lang="scss" scoped>
.support_org_select__trigger{
    display: inline-flex;
    max-width: 100%;
}

.support_org_select__content{
    width: 100%;
}

.support_org_select__list{
    width: 100%;
    padding-top: 8px;
}

.support_org_select__item{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 10px;
    border-radius: 10px;
    transition: all 0.2s ease;

    &:hover,
    &.active{
        background: #f3f7ff;
    }
}

.support_org_select__item_name{
    min-width: 0;
}

.recent_list{
    padding-top: 12px;
}

.recent_list__label{
    color: #888888;
    font-size: 12px;
    line-height: 1;
    margin-bottom: 8px;
}

.recent_list__items{
    display: flex;
    align-items: center;
    gap: 8px;
}

.recent_list__item{
    position: relative;
    overflow: hidden;
    border-radius: 50%;
}

.recent_list__active{
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(0, 0, 0, 0.45);
    color: #ffffff;
    font-size: 10px;
    z-index: 1;
}

.search_input{
    &::v-deep{
        .ant-input{
            background: #f7f9fc;
            border-color: #f7f9fc;
            box-shadow: none !important;
            min-height: 36px;
        }
    }
}
</style>
