<template>
    <a-dropdown 
        :trigger="['click']"
        :destroyPopupOnHide="true"
        @visibleChange="visibleChange">
        <a-button 
            type="ui" 
            ghost 
            flaticon 
            :loading="actionLoading"
            shape="circle"
            icon="fi-rr-menu-dots-vertical" />
        <a-menu slot="overlay">
            <template v-if="$slots.dropdown">
                <slot name="dropdown" />
            </template>
            <a-menu-item v-if="loading" class="flex items-center justify-center">
                <a-spin size="small" />
            </a-menu-item>
            <template v-if="actions && !loading">
                <a-menu-item v-if="actions.config && actions.config.availability" class="flex items-center" @click="openWidgetSetting()">
                    <i class="fi fi-rr-settings mr-2" />
                    {{ $t('dashboard.settings') }}
                </a-menu-item>
                <template v-if="!isMobile && actions.pin && actions.pin.availability">
                    <a-menu-item v-if="widget.static" class="flex items-center" @click="pinWidget()">
                        <i class="fi fi-rr-thumbtack mr-2" />
                        {{ $t('dashboard.unpin') }}
                    </a-menu-item>
                    <a-menu-item v-else class="flex items-center" @click="pinWidget()">
                        <i class="fi fi-rr-thumbtack mr-2" />
                        {{ $t('dashboard.pin') }}
                    </a-menu-item>
                </template>
                <!--<template v-if="!isMobile && widget.showMobile">
                    <a-menu-item 
                        v-if="widget.is_mobile"
                        class="flex items-center" 
                        @click="showMobileVersion(false)">
                        <i class="fi-rr-mobile-notch mr-2" />
                        {{ $t('dashboard.hide_mobile') }}
                    </a-menu-item>
                    <a-menu-item 
                        v-else
                        class="flex items-center" 
                        @click="showMobileVersion(true)">
                        <i class="fi-rr-mobile-notch mr-2" />
                        {{ $t('dashboard.show_mobile') }}
                    </a-menu-item>
                </template>-->
                <a-menu-item class="flex items-center" @click="editNameHandler()">
                    <i class="fi fi-rr-pencil mr-2" />
                    {{ $t('dashboard.rename_widget') }}
                </a-menu-item>
                <template v-if="actions.delete && actions.delete.availability">
                    <a-menu-divider />
                    <a-menu-item class="text-red-500 flex items-center" @click="deleteWidget()">
                        <i class="fi fi-rr-trash mr-2" />
                        {{ $t('dashboard.delete') }}
                    </a-menu-item>
                </template>
            </template>
        </a-menu>
    </a-dropdown>
</template>

<script>
import mixins from './mixins.js'
export default {
    mixins: [mixins]
}
</script>