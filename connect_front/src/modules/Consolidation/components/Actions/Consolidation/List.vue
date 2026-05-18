<template>
    <div>
        <a-dropdown 
            :trigger="dropTrigger"
            destroyPopupOnHide
            @visibleChange="visibleChange">
            <a-button 
                :loading="actionLoading" 
                icon="menu" 
                type="link" />
            <a-menu slot="overlay">
                <template v-if="!actionLoading && actionsList && listVisible">
                    <a-menu-item
                        v-if="actionsList.open && actionsList.open.availability"
                        key="open"
                        class="flex items-center"
                        @click="openConsolidation()">
                        <i class="fi fi-rr-search-alt mr-2"></i>
                        {{$t('Open')}}
                    </a-menu-item>
                    <a-menu-item 
                        v-if="actionsList.edit && actionsList.edit.availability" 
                        key="edit"
                        class="flex items-center"
                        @click="edit()">
                        <i class="fi fi-rr-edit mr-2"></i>
                        {{$t('Edit')}}
                    </a-menu-item>
                    <a-menu-item 
                        v-if="actionsList.download && actionsList.download.availability" 
                        key="download"
                        class="flex items-center"
                        @click="documentDownload()">
                        <i class="fi fi-rr-download mr-2"></i>
                        {{$t('Download')}}
                    </a-menu-item>
                    <template v-if="actionsList.delete">
                        <a-menu-divider />
                        <a-menu-item 
                            key="delete"
                            class="flex items-center text-red-500"
                            @click="deleteHanlder()">
                            <i class="fi fi-rr-trash mr-2"></i>
                            {{$t('Delete')}}
                        </a-menu-item>
                    </template>
                </template>
            </a-menu>
        </a-dropdown>
    </div>
</template>

<script>
import mixins from './mixins'
export default {
    mixins: [mixins]
}
</script>