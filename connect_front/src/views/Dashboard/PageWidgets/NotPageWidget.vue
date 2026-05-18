<template>
    <div class="p-6">
        <a-alert banner>
            <p slot="description">
                {{ $t("widget_not_found", { widgetName: pageMeta?.pageWidget }) }}
            </p>
        </a-alert>
        <div 
            v-if="pageMeta" 
            class="mt-4">
            <a-collapse v-model="activeKey">
                <a-collapse-panel 
                    key="1" 
                    :header="$t('page_configuration')">
                    <pre>
                        <code>
                            {{ pageMeta }}
                        </code>
                    </pre>
                </a-collapse-panel>
            </a-collapse>
        </div>
    </div>
</template>

<script>
export default {
    computed: {
        pageMeta() {
            return this.$route?.meta ? this.$route?.meta : null
        }
    },
    data() {
        return {
            activeKey: []
        }
    }
}
</script>
