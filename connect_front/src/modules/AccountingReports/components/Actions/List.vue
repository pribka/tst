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
                        @click="open()">
                        <i class="fi fi-rr-search-alt mr-2"></i>
                        Открыть
                    </a-menu-item>
                    <a-menu-item 
                        v-if="actionsList.edit && actionsList.edit.availability" 
                        key="edit"
                        class="flex items-center"
                        @click="edit()">
                        <i class="fi fi-rr-edit mr-2"></i>
                        Редактировать
                    </a-menu-item>
                    <a-menu-item 
                        v-if="actionsList.export_to_1c && actionsList.export_to_1c.availability" 
                        key="edit"
                        class="flex items-center"
                        @click="exportTo1C()">
                        <i class="fi fi-rr-file-export mr-2"></i>
                        Выгрузка в 1С
                    </a-menu-item>
                    <a-menu-item 
                        v-if="actionsList.download && actionsList.download.availability" 
                        key="download"
                        class="flex items-center"
                        @click="download()">
                        <i class="fi fi-rr-download mr-2"></i>
                        Скачать
                    </a-menu-item>
                    <template v-if="actionsList.delete">
                        <a-menu-divider />
                        <a-menu-item 
                            key="delete"
                            class="flex items-center text-red-500"
                            @click="deleteHandler()">
                            <i class="fi fi-rr-trash mr-2"></i>
                            Удалить
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
    name: 'ActionsList',
    mixins: [mixins]
}
</script>