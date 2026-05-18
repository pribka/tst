<template>
    <div :ref="`groupNews${id}`">
        <div 
            v-if="actions && actions.add_news"
            class="w-full flex justify-center mb-5">
            <a-button
                icon="fi-rr-plus"
                flaticon
                @click="activeNewPost = true">
                {{ $t("wgr.create_post") }}
            </a-button>
        </div>

        <a-spin 
            :spinning="loadingNews" 
            class="mt-4 flex justify-center" />

        <template v-if="!roleLoader">
            <template v-if="!loadingNews">
                <a-empty
                    v-if="
                        (!isStudent &&
                            !requestData.public_or_private &&
                            userPosts.length === 0) ||
                            (isStudent && userPosts.length === 0)
                    "
                    class="mt-10"
                    :description="$t('wgr.news_not_found')" />
            </template>

            <!--<a-result 
                v-if="!isStudent && requestData.public_or_private"
                :title="$t('wgr.no_partisipants_group')">
                <template #icon>
                    <a-icon 
                        type="lock" 
                        theme="twoTone" />
                </template>
            </a-result>-->
        </template>
        
        <!-- Новости -->
        <template v-if="isStudent || isFounder">
            <a-card
                v-for="post in userPosts"
                :key="post.id"
                class="mb-6 lg:mb-base">
                <div>
                    <!-- Шапка с профилем -->
                    <div class="post-header flex justify-between mb-4">
                        <div class="flex items-center">
                            <Profiler
                                :user="post.author_profile"
                                :getPopupContainer="getPopupContainer"
                                :subtitle="{
                                    text: $moment(post.pub_date).format('DD.MM.YYYY'),
                                    class: 'text_current text-xs'
                                }" />
                        </div>
                        <a-dropdown v-if="isFounder">
                            <a-button 
                                type="ui"
                                flaticon
                                ghost
                                shape="circle"
                                icon="fi-rr-menu-dots-vertical">
                            </a-button>
                            <a-menu slot="overlay">
                                <template v-if="isFounder">
                                    <a-menu-item @click="editNews(post)">
                                        {{ $t('wgr.edit') }}
                                    </a-menu-item>
                                    <!-- <a-menu-item @click="deleteNews(post)">
                                        {{ $t('wgr.delete') }}
                                    </a-menu-item> -->
                                </template>
                                <!-- <a-menu-item @click="shareNews()">
                                    {{ $t('wgr.share') }}
                                </a-menu-item> -->
                            </a-menu>
                        </a-dropdown>
                    </div>

                    <!-- Название и опсиание -->
                    <div>
                        <h4 class="text-xl mb-2 break-words">{{ post.title }}</h4>
                    </div>
                    <div class="post-content leading-7 break-words">
                        <TextViewer :body="post.content" />
                    </div>

                    <NewsFiles 
                        v-if="post.attachments && post.attachments.length" 
                        :news="post" />

                    <!-- Комментарии -->
                    <a-divider></a-divider>

                    <div class="flex justify-between w-full -mt-4">
                           
                        <Comments  class="w-full" :commentLimit="true" :related_object="post.id" model="news" :extendDrawerZIndex="1010" />
                    </div>
                </div>
            </a-card>
            <a-button :loading="loadingNews" v-show="moreNews" @click="getMoreNews" class="mt-4" block type="primary">Загрузить еще</a-button> 

            <DrawerTemplate 
                v-if="actions && actions.add_news"
                v-model="activeNewPost" 
                :width="isMobile ? windowWidth : 700"
                @close="clearAll" 
                destroyOnClose>
                <template #title>
                    <div class="drawer_title">
                        {{ isUpdateMode ? $t('wgr.edit_post') : $t('wgr.create_post') }}
                    </div>
                </template>
                <div class="news_form">
                    <a-form-model 
                        :key="1" 
                        ref="postForm" 
                        :model="dataNewNews" 
                        :rules="rulesPost">
                        <a-form-model-item prop="title"  :label="$t('wgr.title_news')">
                            <a-input size="large" v-model="dataNewNews.title" />
                        </a-form-model-item>
                        <a-form-model-item prop="content" class="-mt-4" :label="$t('wgr.description')">
                            <Ckeditor v-model="dataNewNews.content" />
                        </a-form-model-item>
                                
                        <a-form-model-item 
                            ref="attachments"
                            prop="attachments">
                            <FileAttach
                                :zIndex="1500"
                                ref="fileAttach"
                                :attachmentFiles="fileList">
                                <template v-slot:openButton>
                                    <a-button class="flex justify-center items-center mb-2">
                                        <i class="fi fi-rr-download mr-2"></i> 
                                        <span>Загрузить файл</span>    
                                    </a-button> 
                                </template>
                            </FileAttach>
                        </a-form-model-item>
                    </a-form-model>
                </div>
                <template #footer>
                    <a-button 
                        :loading="loadingPostBtn" 
                        size="large" 
                        block
                        class="px-10" 
                        type="primary"
                        @click="isUpdateMode ? updatePost() : createPost()">
                        {{ $t(isUpdateMode ? 'wgr.save_post' : 'wgr.create_post') }}
                    </a-button>
                </template>
            </DrawerTemplate>
        </template>
    </div>
</template>

<script>
import { mapActions, mapGetters, mapState } from 'vuex'
import DrawerTemplate from "@/components/DrawerTemplate.vue"
import locale from 'ant-design-vue/es/date-picker/locale/ru_RU'

export default {
    components: {
        Comments: () => import('@apps/vue2CommentsComponent'),
        Ckeditor: () => import('@apps/CKEditor'),
        FileAttach: () => import('@apps/vue2Files/components/FileAttach'),
        NewsFiles: () => import('../modules/NewsFiles'),
        TextViewer: () => import('@apps/CKEditor/TextViewer.vue'),
        DrawerTemplate
    },
    props: {
        id: {
            type: [String, Number],
            required: true
        },
        actions: {
            type: Object,
            default: () => null
        }
    },
    data(){
        return {
            locale,
            rulesPost: {
                title: [
                    { required: true, message: this.$t('wgr.field_require'), trigger: 'blur' },
                ],
                content: [{ required: true, message: this.$t('wgr.field_require'), trigger: 'blur' },],
            },

            dataNewNews: {
                title: "",
                content: "",
                image: "",
                workgroups: null,
                attachments: []
            },
            currentEditNews: false,
            files: [],
            filesNews: [],
            attachments: [],
            // ?????????????????
            fileList: [],
            // ?????????????????
            roles: [],
            usersCommented: [],

            suggestedFriends: [],
            userLatestPhotos: [],
            activeNewPost : false,
            pageNews: 1,
            moreNews: false,
            isFounder: false,
            isStudent: false,
            loadingPostBtn: false,
            loadingNews: false,
            userPosts: [],
            activeTab: "1",
            roleLoader: false,
            isUpdateMode: false
        
        }
    }, 
    computed:{
        ...mapGetters({
            requestData : "workgroups/info" 
        }),
        ...mapState({
            windowWidth: state => state.windowWidth
        }),
        isMobile() {
            return this.$store.state.isMobile
        },
    },
    watch: {
        '$route.params.id'() {
            this.userPosts = []
            this.getRoles()
            this.getAllNews()
        }
    },
    created() {
        // this.init()
        this.getRoles()
    }, 
    methods:{
        ...mapActions({
            getRolesS: "workgroups/getRoles",
            getInfos: "workgroups/getInfo",
            createNews: "workgroups/postNews",
            updateNews: "workgroups/updateNews",
            deleteNewsAction: "workgroups/deleteNews",
            getNews: "workgroups/getAllNews"
        }),
        getPopupContainer() {
            return this.$refs[`groupNews${this.id}`]
        },
        clearAll(){
            this.isUpdateMode = false
            this.dataNewNews = {
                title: "",
                content: "",
                image: "",
                workgroups: null,
                attachments: []
            }
            this.activeTab = "1"
            this.activeNewPost = false
        },

        async createPost(){
            this.loadingPostBtn = true
            try{ 
                if(this.activeTab === "1"){
                    this.$refs['postForm'].validate(async v=>{
                        if(v){
                            await this.postNews()
                           
                        } else {
                            this.$message.error(this.$t('wgr.fill_all_fields'))
                        }
             
                    })
                }
            } 
            catch(error){
                this.$message.error(this.$t('wgr.error') + error)
            }
            finally{
                setTimeout(() => {
                    this.loadingPostBtn = false 
                }, 1000);
            }
            
        },
        async updatePost() {

            this.loadingPostBtn = true
            try{ 
                if(this.activeTab === "1"){
                    this.$refs['postForm'].validate(async v=>{
                        if(v){
                            await this.changeNews()
                        } else {
                            this.$message.error(this.$t('wgr.fill_all_fields'))
                        }
             
                    })
                }
            } 
            catch(error){
                this.$message.error(this.$t('wgr.error') + error)
            }
            finally{
                setTimeout(() => {
                    this.loadingPostBtn = false 
                }, 1000);
            }
            
        },

       
        async getMoreNews() {
            this.pageNews += 1
            await this.getAllNews()
        },

        // Поулчение всех новостей
        async getAllNews() {
            try{
                this.loadingNews = true
                if(this.isStudent || this.isFounder || !this.requestData.public_or_private) {
                    const res = await this.getNews({ page: this.pageNews, workgroups: this.id })
    
                    res.results.forEach((el) => {
                        this.userPosts.push(el)
                    })
                    if (res.next === null)
                        this.moreNews = false
                    else
                        this.moreNews = true
                }
            }catch(error){
                this.loadingNews = false 
                this.$message.error(this.$t('wgr.error') + error)
            }
            finally{
                this.loadingNews = false 
            }
        },

        // Создать новость
        async postNews() {
            try{
                this.dataNewNews.workgroups = this.id
                this.dataNewNews.attachments = this.fileList.map(file => file.id)

                const res = await this.createNews(this.dataNewNews)
                this.$message.success(this.$t('wgr.news_created'))      
                this.userPosts.unshift(res);
                this.activeNewPost = false;
                  
                this.dataNewNews = {
                    title: "",
                    content: "",
                    image: null,
                    workgroups: "",
                    attachments: []
                };
                this.fileList.splice(0)
            } 
            catch(error){
                this.$message.error(this.$t('wgr.error') + error)
            }
            
          
        },

        async changeNews() {
            try{
                this.dataNewNews.workgroups = this.id

                this.dataNewNews.attachments = this.fileList.map(file => file.id)

                const res = await this.updateNews({newsId: this.currentEditNews, data: this.dataNewNews})
                if(res) {
                    const postIndex = this.userPosts.findIndex(post => post.id === this.currentEditNews)
                    if(postIndex !== -1) {
                        this.userPosts[postIndex].title = res.title
                        this.userPosts[postIndex].content = res.content
                        this.userPosts[postIndex].attachments = res.attachments
                    }
                }
                this.$message.success(this.$t('wgr.news_created'))      
                // this.userPosts.unshift(res);
                this.activeNewPost = false;
                  
                this.dataNewNews = {
                    title: "",
                    content: "",
                    image: null,
                    workgroups: "",
                    attachments: []
                };
            } catch(error){
                this.$message.error(this.$t('wgr.error') + error)
            } finally {
                this.currentEditNews = false
                this.fileList = []
            }
        },

        async getRoles() {
            try {
                this.roleLoader = true
                const res = await this.getRolesS(this.id);
                if (res[0].id) {
                    this.roles = res;
                    res.forEach((item) => {
                        if (
                            item.membership_role.code === "FOUNDER" ||
                            item.membership_role.code === "MODERATOR"
                        ) {
                            this.isFounder = true;
                            this.isStudent = true;
                        } else if (
                            item.membership_role.code === "MEMBER"   
                        ) {
                            this.isStudent = true;
                        } 
                    });
                }
            } catch(e) {
                console.log(e)
                this.roleLoader = false
            } finally {
                this.roleLoader = false
                this.getAllNews()
            }
        },

        async editNews(news) {
            this.isUpdateMode = true
            // this.filesNews = [...this.dataNewNews.attachments] 
            this.activeNewPost = true
            this.currentEditNews = news.id
            this.dataNewNews = {
                title: news.title,
                content: news.content,
                image: news.image,
                workgroups: news.workgroups,
                attachments: news.attachments
            }

            if(news.attachments?.length) {
                this.fileList = [...news.attachments]
                this.dataNewNews.attachments = news.attachments.map(file => file.id)
            }


        },
        async deleteNews(news) {
            this.$confirm({
                title: 'Вы действительно хотите удалить эту публикацию?',
                okText: 'Удалить',
                zIndex: 99999,
                okType: 'danger',
                cancelText: 'Отмена',
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$store.dispatch('workgroups/deleteNews', news.id)
                            .then(() => {
                                if(this.visible)
                                    this.visible = false
                                    
                                resolve()
                            })
                            .catch(e => {
                                console.log(e)
                                reject()
                            })
                    })
                }
            })
        },

    }
}
</script>

<style lang="scss">
.news_form{
    .ck-editor__editable{
        min-height: 300px;
        max-height: 400px;
    }
}
</style>