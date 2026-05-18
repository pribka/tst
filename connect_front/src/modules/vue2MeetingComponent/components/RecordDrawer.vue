<template>
    <DrawerTemplate
        :title="$t('meeting.records')"
        placement="right"
        :width="drawerWidth"
        v-model="meetingRecVisible"
        @close="meetingRecVisible = false">
        <div class="record_list">
            <div 
                v-for="(item, index) in recordList" 
                :key="index"
                data-iframe="true"
                :data-src="item.url"
                class="mb-4">
                <div class="flex justify-between items-center">
                    <div @click="openRecordModal(item)" class="item w-full"> 
                        {{ $t('meeting.record') }} {{ index }} <span class="font-semibold">({{ $moment(item.created_at).format("DD-MM-YYYY HH:mm") }})</span>
                    </div>  
                    <a-button icon="message" type="ui" shape="circle" @click="openComments(item)"></a-button>
                    <a-button class="ml-2" icon="link" shape="circle" type="ui" @click="copyLink(item.url)"></a-button>
                </div>
                <a-divider class="mt-2"></a-divider>
            </div>
        </div>
        <a-empty v-if="!recordList.length" :description="$t('meeting.emptyList')"></a-empty>
        <a-modal 
            :zIndex="3000"
            :width="windowWidth - 20"
            v-model="modalVisible"
            destroyOnClose
            centered>
            <template #footer>
                <a-button type="primary" @click="openLink">{{ $t('meeting.openNewWindow') }}</a-button>
            </template>
            <iframe 
                :width="windowWidth - 60"
                :height="windowHeight - 130" 
                frameborder="0"
                scrolling="auto"
                :src="activeSrc"></iframe>
        </a-modal>
        <CommentsModal v-model="modalComments" :recordId="commentId"/>
    </DrawerTemplate>
</template>

<script>
export default {
    name: "RecordDrawer",
    components: {
        CommentsModal: () => import('./CommentsModal.vue'),
        DrawerTemplate: () => import("@/components/DrawerTemplate.vue")
    },
    props: {
        value: Boolean,
        id: [String]
    },
    data(){
        return{
            meeting: null,
            recordLoading: false,
            recordList: [],
            modalVisible: false,
            activeSrc: null,
            commentId: null,
            modalComments: false
        }
    },
    computed:{
        meetingRecVisible: {
            get(){
                return this.value
            },
            set(val){
                this.$emit('input', val)
            }
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        windowHeight() {
            return this.$store.state.windowHeight
        },
        drawerWidth() {
            if(this.windowWidth > 500)
                return 400
            else {
                return '100%'
            }
        }
    },
    watch:{
        meetingRecVisible(val){
            if(val) this.openRecord()
            else this.recordList = []
        }
    },
    methods:{
        openComments(item){
            this.commentId = item.id
            this.modalComments = true
        },  
        async openRecord() {
            try {
                this.recordLoading = true
                const { data } = await this.$http.get(`/meetings/${this.id}/records/`)

                if(data?.length) {
                    this.recordList = data.map((el )=> { return { ...el, src: el.url }})
                    // this.initLightbox()
                }
              
            } catch(e) {
                console.log(e)
            } finally {
                this.recordLoading = false
            }
        },
        copyLink(url) {
            try {
                this.$message.success(this.$t('meeting.linkCopied'));
                navigator.clipboard.writeText(url);
            } catch(e) {
                // console.log(e)
            }
        },
        openLink(){
            window.open(this.activeSrc, '_blank');
            this.modalVisible = false
        },
        openRecordModal(item){
            this.activeSrc = item.url
            this.modalVisible = true
        },
        initLightbox() {
            try{ 
                this.$nextTick(() => {
                    const items = document.querySelectorAll('.record_list .item')
                    if(items?.length) {
                        items.forEach(itm => {
                            lightGallery(itm, {
                                selector: 'this',
                                thumbnail: false,
                                animateThumb: false,
                                rotateLeft: false,
                                zoom: false,
                                rotateRight: false,
                                fullScreen: false,
                                flipHorizontal: false,
                                flipVertical: false,
                                showThumbByDefault: false,
                                download: false,
                                iframeMaxWidth: '80%'
                            })
                        })
                    }
                })
            }
            catch(e){
                console.log(e)
            }
        },
    }
}
</script>