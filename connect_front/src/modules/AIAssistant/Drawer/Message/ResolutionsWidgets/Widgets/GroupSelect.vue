<template>
    <div class="wdg_input">
        <GroupSelect 
            v-if="isEdit"
            inputType="input"
            :placeholder="$t('ai_assistant.select_group')"
            :candidates="candidates"
            v-model="value"
            @change="changeWorkGroup" />
        <div v-else>
            <div v-if="value" class="flex items-center truncate">
                <div class="mr-2">
                    <a-avatar 
                        :size="20" 
                        icon="team" 
                        :key="value.id"
                        :src="workgroupLogoPath(value)" />
                </div>
                <span class="truncate">{{value.name}}</span>
            </div>
            <div v-else class="field_empty">
                {{ $t('ai_assistant.group_not_specified') }}
            </div>
        </div>
    </div>
</template>

<script>
import props from '../props.js'
import mixins from './mixins.js'
export default {
    props: {...props},
    mixins: [mixins],
    components: {
        GroupSelect: () => import("@apps/DrawerSelect/GroupSelect.vue")
    },
    data() {
        return {
            value: null,
            candidates: []
        }
    },
    created() {
        if(this.intents.resolutions?.[this.widgetKey]?.candidates?.length) {
            this.candidates = this.intents.resolutions[this.widgetKey].candidates.map(item => {
                return {
                    ...item,
                    name: item.repr,
                    workgroup_logo: item.image
                }
            })
        }
        if(this.intents.resolutions?.[this.widgetKey]?.value) {
            const item = this.intents.resolutions[this.widgetKey].value
            this.value = {
                ...item,
                name: item.repr,
                workgroup_logo: item.image
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.wdg_input{
    &::v-deep{
        .ant-input{
            height: initial;
            padding: 0px;
        }
    }
}
</style>
