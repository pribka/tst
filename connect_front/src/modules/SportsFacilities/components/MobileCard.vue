<template>
    <div class="sport_card">
        <div class="card_header">
            <div class="flex items-center">
                <a-button type="primary" size="large">
                    {{ $t('sports.status') }}: {{ item.status.name }}
                </a-button>
                <a-button 
                    v-if="item.repub_comp"
                    type="success" 
                    size="large" 
                    class="ml-2"
                    flaticon 
                    icon="fi-rr-check" />
            </div>
            <div v-if="!isMobile" class="card_header__right">
                <a-button type="link" size="large" class="flex items-center" @click="openProject()">
                    {{ $t('sports.open') }}
                    <i class="fi fi-rr-arrow-up-right ml-3 text-xs"></i>
                </a-button>
            </div>
        </div>
        <div class="card_body" @click="openProject()">
            <div v-if="item.image && item.image.path" class="card_img mb-3">
                <div class="card_img__wrap">
                    <img 
                        :data-src="item.image.path" 
                        :alt="item.image.name" 
                        class="lazyload" />
                </div>
            </div>
            <div class="body_row">
                {{ item.name }}
            </div>
            <div class="body_row">
                {{ $t('sports.constructionYear') }}: {{ item.building_year }}
            </div>
            <div v-if="item.facility_type" class="body_row blue_color">
                {{ item.facility_type.full_name }}
            </div>
            <div v-if="item.ownership_form" class="body_row">
                <span>{{ $t('sports.ownershipType') }}:</span> <div>{{ item.ownership_form.name }}</div>
            </div>
            <div v-if="item.owner_name" class="body_row">
                <span>{{ $t('sports.owner') }}:</span> <div>{{ item.owner_name }}</div>
            </div>
            <div class="mt-3">
                <div class="body_row_wrap">
                    <div class="body_row">
                        <span>{{ $t('sports.capacity') }}:</span> <div>{{ item.bandwidth }}</div>
                    </div>
                    <div class="body_row">
                        <span>{{ $t('sports.area') }}:</span> <div>{{ item.area }} м<sup>2</sup></div>
                    </div>
                    <!--<div class="body_row">
                        <span>Количество кружков:</span> <div>12</div>
                    </div>-->
                </div>
                <div v-if="item.location" class="body_row_wrap">
                    <div class="body_row">
                        <span>{{ $t('sports.location') }}:</span> <div>{{ item.location.name }}</div>
                    </div>
                    <div v-if="item.location.full_name" class="flex items-center blue_color cursor-pointer">
                        <i class="fi fi-rr-marker mr-2" />
                        {{ item.location.full_name }}
                    </div>
                </div>
            </div>
        </div>
        <!--<div class="card_footer">
            <a-button size="large">
                {{ $t('sports.repairNeed') }}
            </a-button>
            <a-button size="large">
                {{ $t('sports.equipmentNeed') }}
            </a-button>
        </div>-->
    </div>
</template>

<script>
export default {
    props: {
        item: {
            type: Object,
            required: true
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    methods: {
        openProject() {
            this.$router.push({ name: 'full_sports_facilities_pasport', params: { id: this.item.id } })
        }
    }
}
</script>

<style lang="scss" scoped>
.sport_card{
    padding: 15px;
    border: 1px solid var(--border2);
    border-radius: var(--borderRadius);
    display: flex;
    flex-direction: column;
    background: #ffffff;
    @media (min-width: 768px) {
        padding: 20px 20px 20px 20px; /*20px 20px 10px 20px*/
    }
    .card_img{
        overflow: hidden;
        position: relative;
        height: 110px;
        width: 180px;
        border-radius: 4px;
        cursor: pointer;
        &__wrap{
            height: 100%;
            left: 0;
            margin: 0;
            overflow: hidden;
            position: absolute;
            top: 0;
            width: 100%;
            display: flex;
            align-items: flex-start;
            img{
                object-fit: contain;
                vertical-align: middle;
                -o-object-fit: contain;
                max-height: 100%;
                border-style: none;
                border-radius: 4px;
                opacity: 0;
                transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
                &.lazyloaded{
                    opacity: 1;
                }
            }
        }
    }
    .card_footer{
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        padding-top: 20px;
        &::v-deep{
            .ant-btn{
                margin-bottom: 10px;
                color: #000;
                border-color: #FFA940;
            }
        }
    }
    .card_header{
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .card_body{
        padding-top: 20px;
        .body_row_wrap{
            background: #FAFAFA;
            border-radius: 8px;
            padding: 15px;
            &:not(:last-child){
                margin-bottom: 5px;
            }
        }
        .body_row{
            color: #000;
            word-wrap: break-word;
            &.blue_color{
                color: var(--blue);
            }
            &:not(:last-child){
                margin-bottom: 10px;
            }
            span{
                opacity: 0.6;
                padding-right: 10px;
            }
            div{
                max-width: 400px;
            }
        }
    }
}
</style>