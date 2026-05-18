<template>
    <div class="section_card">
        <div 
            v-if="item.sport_type.category && item.sport_type.category.name" 
            class="card_row">
            <div class="card_row__label">
                {{ $t('sports.category') }}
            </div>
            <div class="card_row__value">
                {{ item.sport_type.category.name }}
            </div>
        </div>
        <div class="card_row">
            <div class="card_row__label">
                {{ $t('sports.sport_type') }}
            </div>
            <div class="card_row__value">
                {{ item.sport_type.name }}
            </div>
        </div>
        <div class="card_row">
            <div class="card_row__label">
                {{ $t('sports.sectionCount') }}
            </div>
            <div class="card_row__value">
                <div v-if="item.sections_quantity" class="flex items-center justify-between">
                    <span>{{ item.sections_quantity }}</span>
                    <a-button 
                        type="link" 
                        class="more_btn lowercase"
                        size="small"
                        @click="addHandler(item, 'openSectionInformationDrawer')">
                        {{ $t('sports.more') }}
                    </a-button>
                </div>
                <a-button 
                    v-else 
                    type="link" 
                    size="small" 
                    style="text-align: left;"
                    class="more_btn px-0"
                    block
                    @click="addHandler(item, 'openSectionInformationDrawer')">
                    {{ $t('sports.addOnly') }}
                </a-button>
            </div>
        </div>
        <div class="card_row">
            <div class="card_row__label">
                {{ $t('sports.sectionCount2') }}
            </div>
            <div class="card_row__value">
                <div v-if="item.members_quantity" class="flex items-center justify-between">
                    <span>{{ item.members_quantity }}</span>
                    <a-button 
                        type="link" 
                        class="more_btn lowercase"
                        size="small"
                        @click="addHandler(item, 'openSectionPeopleCountDrawer')">
                        {{ $t('sports.more') }}
                    </a-button>
                </div>
                <a-button 
                    v-else 
                    type="link" 
                    size="small" 
                    style="text-align: left;"
                    class="more_btn px-0"
                    block
                    @click="addHandler(item, 'openSectionPeopleCountDrawer')">
                    {{ $t('sports.addOnly') }}
                </a-button>
            </div>
        </div>
        <div class="card_row">
            <div class="card_row__label">
                {{ $t('sports.sectionCount3') }}
            </div>
            <div class="card_row__value">
                <div v-if="item.coaches_quantity" class="flex items-center justify-between">
                    <span>{{ item.coaches_quantity }}</span>
                    <a-button 
                        type="link" 
                        class="more_btn lowercase"
                        size="small"
                        @click="addHandler(item, 'openSectionTrainersCountDrawer')">
                        {{ $t('sports.more') }}
                    </a-button>
                </div>
                <a-button 
                    v-else 
                    type="link" 
                    size="small" 
                    style="text-align: left;"
                    class="more_btn px-0"
                    block
                    @click="addHandler(item, 'openSectionTrainersCountDrawer')">
                    {{ $t('sports.addOnly') }}
                </a-button>
            </div>
        </div>
        <a-button 
            type="danger" 
            class="mt-2"
            size="large"
            block
            ghost
            @click="deleteHandler(item)">
            {{ $t('sports.delete') }}
        </a-button>
    </div>
</template>

<script>
export default {
    props: {
        item: {
            type: Object,
            required: true
        },
        addHandler: {
            type: Function,
            default: () => {}
        },
        deleteHandler: {
            type: Function,
            default: () => {}
        }
    }
}
</script>

<style lang="scss" scoped>
.section_card{
    border: 1px solid #EBEBEB;
    border-radius: 8px;
    color: #000;
    padding: 15px;
    &:not(:last-child){
        margin-bottom: 10px;
    }
}
.card_row{
    &:not(:last-child){
        margin-bottom: 10px;
    }
    &__label{
        opacity: 0.6;
    }
}
</style>