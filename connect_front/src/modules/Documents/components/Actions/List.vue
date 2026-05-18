<template>
    <div>
        <a-dropdown 
            :trigger="dropTrigger"
            :destroyPopupOnHide="true"
            @visibleChange="visibleChange">
            <a-button 
                :loading="loading" 
                icon="menu" 
                type="link" />
            <a-menu slot="overlay">
                <a-menu-item 
                    v-if="!actionsList && actionLoading"
                    key="menu_loader"
                    class="flex justify-center">
                    <a-spin size="small" />
                </a-menu-item>
                <template v-if="!actionLoading && listVisible">
                    <a-menu-item 
                        key="open"
                        class="flex items-center"
                        @click="openDocument()">
                        <i class="fi fi-rr-search-alt mr-2"></i>
                        Открыть документ
                    </a-menu-item>
                    <a-menu-item 
                        key="copy"
                        class="flex items-center"
                        @click="copyDocument()">
                        <i class="fi fi-rr-copy-alt mr-2"></i>
                        Скопировать
                    </a-menu-item>
                </template>
                <template v-if="actionsList">
                    <a-menu-item 
                        v-if="actionsList.send" 
                        key="sign"
                        class="flex items-center"
                        @click="documentSign()">
                        <i class="fi fi-rr-memo-circle-check mr-2"></i>
                        Отправить на подпись
                    </a-menu-item>
                    <a-menu-item 
                        v-if="actionsList.edit && !record.locked" 
                        key="edit"
                        class="flex items-center"
                        @click="edit()">
                        <i class="fi fi-rr-edit mr-2"></i>
                        Редактировать
                    </a-menu-item>
                    <template v-if="actionsList.delete && !record.locked">
                        <a-menu-divider />
                        <a-menu-item 
                            key="delete"
                            class="flex items-center text-red-500"
                            @click="deleteHanlder()">
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
    mixins: [mixins]
}
</script>