import { mapActions, mapMutations, mapState } from 'vuex'
import {checkImageWidthHeight, getFileExtension, hashString} from '@/utils/utils'
import Cropper from 'cropperjs'
import { errorHandler } from '@/utils/index.js'
export default {
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth
        }),
        cropDrawerWidth() {
            if(this.windowWidth > 500)
                return 400
            else
                return this.windowWidth
        },
    },
    data() {
        return {
            minSize: 100,
            cropModal: false,
            file: null,
            dataUrl: null,
            uploadLoading: false,
            cropperOptions: {
                viewMode: 1,
                aspectRatio: 1 / 1,
                minCropBoxWidth: 100,
                minCropBoxHeight: 100
            }
        }
    },
    methods: {
        ...mapMutations({
            setLoading: "workgroups/setLoading",
            clearGroups: "workgroups/clearGroups",
            clearProjects: "workgroups/clearProjects",
        }),

        ...mapActions({
            getGroupTypes: "workgroups/getGroupTypes",
            getSocialTypes: "workgroups/getSocialTypes",
            createGroupS: "workgroups/createGroup",
            updateGroupS: "workgroups/updateGroup",
            postSocLink: "workgroups/postSocialLink",
            getInfo: "workgroups/getInfo",
            getAllGroupsS: "workgroups/getMyGroups"
        }),
        closeCropModal() {
            this.cropModal = false
            this.dataUrl = null
            this.file = null
        },
        uploadImage() {
            this.cropper.getCroppedCanvas().toBlob(async (avatar) => {
                try {
                    const exc = getFileExtension(this.file.name),
                        filename = `${hashString(this.file.name)}.${exc}`

                    this.uploadLoading = true
                    const data = await this.$uploadFile({
                        file: avatar,
                        url: '/common/upload/',
                        fieldName: 'upload',
                        fileName: filename
                    })

                    if(data?.length) {
                        this.form.workgroup_logo = data[0]
                        this.closeCropModal()
                    }
                } catch(error) {
                    errorHandler({error})
                } finally {
                    this.uploadLoading = false
                }
            })
        },
        createCropper() {
            this.cropper = new Cropper(this.$refs.avatarImg, this.cropperOptions)
        },
        async handleFileChange(event) {
            const file = Object.values(event.target.files)[0]
            if(file) {
                const fileSize = await checkImageWidthHeight(file)
                if(fileSize.width > this.minSize && fileSize.height > this.minSize) {
                    let reader = new FileReader()
                    reader.onload = e => {
                        this.dataUrl = e.target.result
                    }
                    reader.readAsDataURL(file)
                    this.file = file
                    this.cropModal = true
                } else
                    this.$message.error(this.$t('max_file_h_w', {size: this.minSize}))
            }
        },
        async init() {
            this.loading = true
            this.visible = true
            this.setLoading(true)
            this.groupTypes = await this.getGroupTypes()
            this.listLinks = await this.getSocialTypes()

            this.loading = false
            this.setLoading(false)
        },
        async initUpdate() {
            this.edit = true
            const res = await this.getInfo(this.id)

            if(res.organization?.id)
                res.organization = res.organization.id

            this.form =
            {
                ...res,
                workgroup_type: res.workgroup_type.id
            }

            if(res.workgroup_logo) {
                this.form.workgroup_logo = res.workgroup_logo
            }
            this.form.funds_currency = null
            this.sLinks = this.form.social_links.map((item) => {
                return {
                    content: item.social_link,
                    type: item.social_web_type.id,
                    key: Date.now()
                }
            })
        },

        // Загрузка соц сетей
        async uploadSocLink() {
            let ids = [];
            try {
                this.sLinks.forEach(async (item) => {
                    if (this.getValidUrl(item.content)) {
                        const response = await this.postSocLink(
                            {
                                social_web_type: item.type,
                                social_link: this.getValidUrl(item.content),
                            }
                        )

                        ids.push(response.id)


                    } else {
                        return false
                    }

                });
                setTimeout(() => {
                    this.form.social_links = ids;

                }, 500);
            }
            catch (error) {
                errorHandler({error})
            }


        },
        getValidUrl(url = "") {
            let RegExp = /^((ftp|http|https):\/\/)?(www\.)?([A-Za-zА-Яа-я0-9]{1}[A-Za-zА-Яа-я0-9\-]*\.?)*\.{1}[A-Za-zА-Яа-я0-9-]{2,8}(\/([\w#!:.?+=&%@!\-\/])*)?/;

            if (RegExp.test(url)) {
                let newUrl = window.decodeURIComponent(url);
                newUrl = newUrl.trim().replace(/\s/g, "");
                if (/^(:\/\/)/.test(newUrl)) {
                    return `http${newUrl}`;
                }
                if (!/^(f|ht)tps?:\/\//i.test(newUrl)) {
                    return `http://${newUrl}`;
                }
                return newUrl;
            } else {
                this.$messgae.error(this.$t('wgr.invalid_link'))
            }
        },

        // Методы для работы  с соцсетями
        // Добавить
        add() {
            // Добавляем новую соц сеть
            if (this.sLinks.length < 6) {
                this.sLinks.push({
                    content: "",
                    type: null,
                    key: Date.now(),
                });
            }
        },
        // Удалить
        deleteItem(elem) {
            // Удаляем соцсеть
            const index = this.sLinks.findIndex(
                (item) => item.key === elem.key
            );
            this.sLinks.splice(index, 1);
        },


    }
}
