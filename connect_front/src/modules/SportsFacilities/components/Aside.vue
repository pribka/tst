<template>
    <aside class="sports_facilities_aside" :class="isMobile && 'mb-4 mobile_aside'">
        <div class="aside_block">
            <div class="block_label">{{ $t('sports.objectPassport') }}</div>
            <template v-if="project">
                <div v-if="project.organization" class="aside_row">
                    <div class="aside_row__label">{{ $t('sports.organization') }}:</div>
                    <div class="aside_row__value">{{ project.organization.name }}</div>
                </div>
                <div v-if="project.author" class="aside_row">
                    <div class="aside_row__label">{{ $t('sports.responsible') }}:</div>
                    <div class="aside_row__value">
                        <Profiler
                            :avatarSize="22"
                            :user="project.author" />
                    </div> 
                </div>
            </template>
            <a-skeleton v-else active :paragraph="{ rows: 4 }" />
        </div>
        <div class="aside_block">
            <a-dropdown v-if="isMobile">
                <a-button type="primary" size="large" block>
                    <div class="flex items-center justify-between">
                        <template v-if="tab === 'info'">
                            {{ $t('sports.tabInformation') }}
                        </template>
                        <template v-if="tab === 'files'">
                            {{ $t('sports.tabDocuments') }}
                        </template>
                        <template v-if="tab === 'history'">
                            {{ $t('sports.tabChangeHistory') }}
                        </template>
                        <i class="fi fi-rr-angle-small-down"></i>
                    </div>
                </a-button>
                <a-menu slot="overlay">
                    <a-menu-item @click="tab = 'info'">
                        {{ $t('sports.tabInformation') }}
                    </a-menu-item>
                    <a-menu-item @click="tab = 'files'">
                        {{ $t('sports.tabDocuments') }}
                    </a-menu-item>
                    <a-menu-item @click="tab = 'history'">
                        {{ $t('sports.tabChangeHistory') }}
                    </a-menu-item>
                </a-menu>
            </a-dropdown>
            <div v-else class="block_tabs lg:flex items-center">
                <!--<a-button type="primary" :block="isMobile" class="px-2" :class="isMobile && 'mb-2'" :ghost="checkPageActive('full_sports_facilities_repair')" size="large" @click="changePage('full_sports_facilities_repair')">
                    {{ $t('sports.tabInformation') }}
                </a-button>-->
                <a-button type="primary" :block="isMobile" class="px-2" :ghost="checkPageActive('full_sports_facilities_files')" size="large" @click="changePage('full_sports_facilities_files')">
                    {{ $t('sports.tabDocuments') }}
                </a-button>
                <a-button type="primary" :block="isMobile" class="px-2" :ghost="checkPageActive('full_sports_facilities_history')" size="large" @click="changePage('full_sports_facilities_history')">
                    {{ $t('sports.tabChangeHistory') }}
                </a-button>
            </div>
            <template v-if="mobileShowInfo">
                <div v-if="checkAsideInfo" class="mt-4">
                    <template v-if="project">
                        <div class="block_label label_large">
                            {{ $t('sports.projectMainInfo') }}
                        </div>
                        <!--<div class="mb-2">
                            <div class="row_status">
                                {{ $t('sports.repairNeed') }}
                            </div>
                        </div>
                        <div class="mb-4">
                            <div class="row_status">
                                {{ $t('sports.equipmentNeed') }}
                            </div>
                        </div>-->
                        <div v-if="project.location" class="aside_row">
                            <div class="aside_row__label">{{ $t('sports.location') }}:</div>
                            <div class="aside_row__value">{{ project.location.full_name }}</div>
                        </div>
                        <div v-if="project.ownership_form" class="aside_row">
                            <div class="aside_row__label">{{ $t('sports.ownershipType') }}:</div>
                            <div class="aside_row__value">{{ project.ownership_form.name }}</div>
                        </div>
                        <div v-if="project.owner_name" class="aside_row">
                            <div class="aside_row__label">{{ $t('sports.ownerOrganization') }}:</div>
                            <div class="aside_row__value">{{ project.owner_name }}</div>
                        </div>
                        <div v-if="project.owner_bin" class="aside_row">
                            <div class="aside_row__label">{{ $t('sports.bin') }}:</div>
                            <div class="aside_row__value">{{ project.owner_bin }}</div>
                        </div>
                        <div v-if="purpose" class="aside_row">
                            <div class="aside_row__label">{{ $t('sports.purpose') }}:</div>
                            <div class="aside_row__value">{{ purpose }}</div>
                        </div>
                        <div v-if="facility_type.type1" class="aside_row">
                            <div class="aside_row__label">{{ $t('sports.sportsFacilityType') }}:</div>
                            <div class="aside_row__value">{{ facility_type.type1 }}</div>
                        </div>
                        <div v-if="facility_type.type2" class="aside_row">
                            <div class="aside_row__label">{{ $t('sports.sportsFacilitySubtype') }}:</div>
                            <div class="aside_row__value">{{ facility_type.type2 }}</div>
                        </div>
                        <div v-if="project.building_year" class="aside_row">
                            <div class="aside_row__label">{{ $t('sports.constructionYear') }}:</div>
                            <div class="aside_row__value">{{ project.building_year }}</div>
                        </div>
                        <div v-if="project.bandwidth" class="aside_row">
                            <div class="aside_row__label">{{ $t('sports.capacity') }}:</div>
                            <div class="aside_row__value">{{ project.bandwidth }}</div>
                        </div>
                        <div v-if="project.storeys_number" class="aside_row">
                            <div class="aside_row__label">{{ $t('sports.storeys') }}:</div>
                            <div class="aside_row__value">{{ project.storeys_number }}</div>
                        </div>
                        <div v-if="project.area" class="aside_row">
                            <div class="aside_row__label">{{ $t('sports.area') }}:</div>
                            <div class="aside_row__value">{{ project.area }} м<sup>2</sup></div>
                        </div>
                    </template>
                    <a-skeleton v-else active :paragraph="{ rows: 4 }" />
                </div>
            </template>
            <div v-if="mobileShowFiles" class="mt-4">
                <Files :actionInfo="actions" />
            </div>
            <div v-if="mobileShowHistory" class="mt-4">
                <History />
            </div>
        </div>
    </aside>
</template>

<script>
import { mapState } from 'vuex'
import Files from '../views/Files.vue'
import History from '../views/History.vue'

export default {
    components: {
        Files,
        History
    },
    computed: {
        ...mapState({
            project: state => state.facilities.project,
            actions: state => state.facilities.projectActions
        }),
        purpose() {
            if(this.project?.purpose) {
                if(this.project.purpose.parent) {
                    if(this.project.purpose.parent.parent) {
                        return this.project.purpose.parent.parent.name
                    } else
                        return this.project.purpose.parent.name
                } else
                    return this.project.purpose.name
            }
            return null
        },
        facility_type() {
            if(this.project?.facility_type) {
                if(this.project.facility_type.parent) {
                    if(this.project.facility_type.parent.parent) {
                        return {
                            type1: this.project.facility_type.parent.parent.name,
                            type2: this.project.facility_type.name
                        }
                    } else {
                        return {
                            type1: this.project.facility_type.parent.name,
                            type2: this.project.facility_type.name
                        }
                    }
                } else
                    return {
                        type1: this.project.facility_type.name,
                        type2: null
                    }
            }
            return null
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        checkAsideInfo() {
            if(this.isMobile) {
                if(this.$route.name === 'full_sports_facilities_files')
                    return false
            }
            return true
        },
        mobileShowInfo() {
            if(this.isMobile)
                return this.tab === 'info' ? true : false
            else
                return true 
        },
        mobileShowFiles() {
            if(this.isMobile)
                return this.tab === 'files' ? true : false
            else
                return false 
        },
        mobileShowHistory() {
            if(this.isMobile)
                return this.tab === 'history' ? true : false
            else
                return false 
        }
    },
    data() {
        return {
            tab: 'info',
            showInfo: true
        }
    },
    methods: {
        changePage(name) {
            if(this.$route.name !== name)
                this.$router.push({name})
        },
        checkPageActive(name) {
            if(name === 'full_sports_facilities_repair') {
                if(this.$route.name === 'full_sports_facilities_repair' || this.$route.name === 'full_sports_facilities_sections' || this.$route.name === 'full_sports_facilities_technical')
                    return false
            }
            if(name === 'full_sports_facilities_files' && this.$route.name === 'full_sports_facilities_files') {
                return false
            }
            if(name === 'full_sports_facilities_history' && this.$route.name === 'full_sports_facilities_history') {
                return false
            }
            return true
        }
    }
}
</script>

<style lang="scss" scoped>
.sports_facilities_aside{
    &.mobile_aside{
        background: #EFF2F5;
        border-radius: 8px;
        padding-left: 20px;
        padding-right: 20px;
        .aside_block{
            &:not(:last-child){
                border-bottom: 1px solid #c0c2c4;
            }
        }
    }
    &:not(.mobile_aside){
        .aside_block{
            padding-left: 20px;
            padding-right: 20px;
            background: #EFF2F5;
            border-radius: 8px;
            &:not(:last-child){
                margin-bottom: 20px;
            }
        }
    }
    .row_status{
        background: #FFA940;
        color: #000;
        border-radius: 8px;
        height: 40px;
        padding: 0 15px;
        font-size: 13px;
        line-height: 40px;
        display: inline-block;
    }
    .block_tabs{
        &::v-deep{
            .ant-btn{
                font-size: 13px;
                &:not(:last-child){
                    margin-right: 8px;
                }
            }
        }
    }
    .aside_block{
        color: #000;
        padding-bottom: 20px;
        padding-top: 20px;
        .block_label{
            font-size: 16px;
            margin-bottom: 10px;
            &.label_large{
                font-size: 18px;
            }
        }
    }
    .aside_row{
        word-wrap: break-word;
        &__label{
            opacity: 0.6;
        }
        &:not(:last-child){
            margin-bottom: 10px;
        }
        &__value{
            max-width: 300px;
        }
    }
}
</style>