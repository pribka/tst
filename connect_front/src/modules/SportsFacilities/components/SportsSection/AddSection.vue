<template>
    <a-modal
        :title="$t('sports.sectionAdd')"
        :visible="visible"
        :afterClose="afterClose"
        :footer="false"
        @cancel="visible = false">
        <div ref="sectionFormWrap">
            <a-form-model
                ref="sectionForm"
                :model="form"
                :rules="rules">
                <a-form-model-item 
                    ref="category" 
                    :label="$t('sports.category')" 
                    prop="category">
                    <TreeSelect
                        v-model="form.category"
                        apiUrl="/sports_facilities/sport_categories/"
                        :treeDefaultExpandedKeys="treeDefaultExpandedKeys"
                        @change="changeSportCategory('category')"
                        @initLoading="sportsCategoryInitLoading" />
                </a-form-model-item>
                <a-form-model-item 
                    ref="sport_type" 
                    :label="$t('sports.sport_type')" 
                    prop="sport_type">
                    <DSelect
                        v-model="form.sport_type"
                        size="large"
                        apiUrl="/sports_facilities/sport_types/"
                        class="w-full"
                        oneSelect
                        usePopupContainer
                        :getPContainer="getPContainer"
                        :params="{
                            category: sportTypesParams()
                        }"
                        :listObject="false"
                        valueKey="code"
                        infinity
                        initList
                        :key="`${form.category}`"
                        :disabled="form.category ? false : true"
                        labelKey="name"
                        placeholder="Выбрать"
                        :default-active-first-option="false"
                        :filter-option="false"
                        :not-found-content="null" />
                </a-form-model-item>
                <a-button 
                    type="primary" 
                    size="large" 
                    block 
                    :loading="formLoading"
                    @click="formSubmit()">
                    {{ $t('sports.addOnly') }}
                </a-button>
                <a-button 
                    type="ui" 
                    class="mt-2"
                    ghost
                    size="large" 
                    block
                    @click="visible = false">
                    {{ $t('sports.close') }}
                </a-button>
            </a-form-model>
        </div>
    </a-modal>
</template>

<script>
import eventBus from '@/utils/eventBus'
import TreeSelect from '@apps/DrawerSelect/TreeSelect.vue'
import DSelect from '@apps/DrawerSelect/Select.vue'
export default {
    components: {
        TreeSelect,
        DSelect
    },
    props: {
        getSections: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
            isEdit: false,
            treeDefaultExpandedKeys: [],
            visible: false,
            formLoading: false,
            form: {
                category: null,
                sport_type: null
            },
            rules: {
                category: [
                    { required: true, message: this.$t('sports.formError'), trigger: 'blur' }
                ],
                sport_type: [
                    { required: true, message: this.$t('sports.formError'), trigger: 'blur' }
                ]
            },
        }
    },
    methods: {
        formSubmit() {
            this.$refs.sectionForm.validate(async valid => {
                if (valid) {
                    try {
                        this.formLoading = true
                        const { data } = await this.$http.post(`/sports_facilities/${this.$route.params.id}/section/create/`, this.form)
                        if(data) {
                            this.visible = false
                            this.$message.success(this.$t('sports.sectionAddSuccess'))
                            this.getSections()
                        }
                    } catch(e) {
                        console.log(e)
                        this.$message.error(this.$t('sports.error'))
                    } finally {
                        this.formLoading = false
                    }
                } else {
                    return false;
                }
            });
        },
        afterClose() {
            this.form = {
                category: null,
                sport_type: null
            }
        },
        getPContainer() {
            return this.$refs.sectionFormWrap
        },
        sportTypesParams() {
            if(this.form.category)
                return this.form.category
        },
        changeSportCategory() {
            this.form.sport_type = null
        },
        sportsCategoryInitLoading(onLoadData) {
            if(this.isEdit) {
                function transformTreeToFlatArray(sportTypes) {
                    let flatArray = []
                    let expandedKeys = []

                    sportTypes.forEach(item => {
                        let current = item.sport_type.category
                        let lastParentCode = null

                        while (current) {
                            const { code, name, parent } = current

                            if (parent)
                                lastParentCode = parent.code

                            const hasChildren = !!parent

                            const flatItem = {
                                id: code,
                                code: code,
                                value: code,
                                title: name,
                                isLeaf: !hasChildren,
                                pId: lastParentCode,
                                loaded: false
                            }

                            flatArray.push(flatItem)
                            onLoadData({
                                dataRef: flatItem
                            })

                            if (hasChildren)
                                expandedKeys.push(code)

                            if (!parent) {
                                this.treeDefaultExpandedKeys.push(code)
                                break
                            }

                            current = parent
                        }
                    })

                    this.treeDefaultExpandedKeys = this.treeDefaultExpandedKeys.concat(expandedKeys)
                }
                const sportTypes = this.editData.sport_type
                transformTreeToFlatArray.call(this, sportTypes)
            }
        },
    },
    mounted() {
        eventBus.$on('addSection', () => {
            this.visible = true
        })
    },
    beforeDestroy() {
        eventBus.$off('addSection')
    }
}
</script>