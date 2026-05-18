import CKEditor from '@ckeditor/ckeditor5-vue2'
import { errorHandler } from '@/utils/index.js'
import eventBus from '@/utils/eventBus'

export default {
    components: {
        ckeditor: CKEditor.component,
    },
    props: {
        value: { type: String, default: '' }, 
        mentionsData: {
            type: Array,
            default: () => []
        },
        useUserMentions: {
            type: Boolean,
            default: false
        },
        userPageSize: {
            type: Number,
            default: 15
        },
        uploadUrl: {
            type: String,
            default: "/common/upload_for_editor/"
        },
        chat_uid: {
            type: [String, Number],
            default: ""
        },
        taskId: {
            type: String,
            default: ''
        },
        injectItems: {
            type: Array,
            default: () => []
        },
        initFocus: {
            type: Boolean,
            default: false
        },
        behaviorStatus: {
            type: Boolean,
            default: true
        },
        enterShifthHand: {
            type: Function,
            default: () => {}
        },
        commentEditor: {
            type: Boolean,
            default: false
        },
        chatEditor: {
            type: Boolean,
            default: false
        },
        missionEditor: {
            type: Boolean,
            default: false
        },
        shouldNotGroupWhenFull: {
            type: Boolean,
            default: false
        },
        placeholder: {
            type: String,
            default: ""
        },
        uploadFieldKey: {
            type: String,
            default: 'upload'
        },
        editorClassName: {
            type: String,
            default: 'w-full'
        },
        // Показывать ли кнопки underline/strikethrough (по умолчанию скрыты)
        showTextDecorations: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        user() {
            return this.$store.state.user.user
        }
    },
    data() {
        return {
            chatMention: {
                loadingAll: false,
                loadedAll: false,
                all: [],
                requestId: 0
            }
        }
    },
    created() {
        if(this.injectItems?.length)
            this.editorConfig.toolbar.items = this.editorConfig.toolbar.items.concat(this.injectItems)
    },
    methods: {
        dataUrlToFile(dataUrl, name) {
            const m = String(dataUrl).match(/^data:(.+);base64,(.*)$/)
            if (!m) return null

            const mime = m[1]
            const b64 = m[2]
            const bin = atob(b64)
            const len = bin.length
            const arr = new Uint8Array(len)

            for (let i = 0; i < len; i++) arr[i] = bin.charCodeAt(i)

            const ext = (mime.split('/')[1] || 'png').split(';')[0]
            const fileName = name || `image_${Date.now()}.${ext}`

            return new File([arr], fileName, { type: mime })
        },

        async blobUrlToFile(blobUrl, name) {
            try {
                const res = await fetch(blobUrl)
                const blob = await res.blob()
                const mime = blob.type || 'image/png'
                const ext = (mime.split('/')[1] || 'png').split(';')[0]
                const fileName = name || `image_${Date.now()}.${ext}`
                return new File([blob], fileName, { type: mime })
            } catch (e) {
                return null
            }
        },

        async extractFilesFromHtml(html) {
            const doc = new DOMParser().parseFromString(String(html || ''), 'text/html')
            const imgs = Array.from(doc.body.querySelectorAll('img'))
            const files = []

            for (const img of imgs) {
                const src = img.getAttribute('src') || ''
                if (!src) continue

                if (src.startsWith('data:')) {
                    const f = this.dataUrlToFile(src)
                    if (f) files.push(f)
                    img.remove()
                    continue
                }

                if (src.startsWith('blob:')) {
                    const f = await this.blobUrlToFile(src)
                    if (f) files.push(f)
                    img.remove()
                    continue
                }

                img.remove()
            }

            return {
                files,
                cleanedHtml: doc.body.innerHTML
            }
        },

        extractFilesFromDataTransfer(dataTransfer) {
            const list = []
            const files = dataTransfer && dataTransfer.files ? Array.from(dataTransfer.files) : []
            files.forEach(f => {
                if (!f) return
                const name = f.name || ''
                const type = f.type || ''
                const safeName = name.length ? name : `file_${Date.now()}`
                const fixed = name.length ? f : new File([f], safeName, { type })
                list.push(fixed)
            })
            return list
        },
        isNotCurrentUser(item) {
            const currentId = this.user?.id
            const id = item?.objectId ?? item?.id
            if (!currentId || !id) return true
            return String(id) !== String(currentId)
        },
        normalizeMentionUser(raw) {
            const u = raw?.user || raw

            if (!u) return null

            const fullName = u.full_name || u.fullName || u.name
            const isActive = u.is_active !== undefined ? u.is_active : true

            if (!isActive) return null
            if (!fullName) return null

            return {
                id: `@${fullName}`,
                name: fullName,
                objectId: u.id,
                objectType: 'user',
                objectClass: 'user_chat_mention',
                avatar: u.avatar,
                online: u.online,
                color: u.color
            }
        },

        getMentionsFromProps() {
            const list = Array.isArray(this.mentionsData) ? this.mentionsData : []
            return list.map(this.normalizeMentionUser).filter(Boolean)
        },
        sendChatEvent(action) {
            eventBus.$emit(action)
        },
        mapChatMemberToMentionItem(r) {
            const u = r && r.user
            if (!u || !u.is_active) return null
            if (!u.full_name) return null
            if (String(u.id) === String(this.user?.id)) return null

            return {
                id: `@${u.full_name}`,
                name: u.full_name,
                objectId: u.id,
                objectType: 'user',
                objectClass: 'user_chat_mention',
                avatar: u.avatar,
                online: u.online,
                color: u.color
            }
        },
        async loadAllChatMembers() {
            const state = this.chatMention
            if (!this.chat_uid) return
            if (state.loadedAll || state.loadingAll) return

            state.loadingAll = true

            try {
                const all = []
                let page = 1
                let next = true

                while (next) {
                    const { data } = await this.$http('/chat/member/list/', {
                        params: {
                            chat: this.chat_uid,
                            page,
                            page_size: this.userPageSize
                        }
                    })

                    const chunk = (data.results || [])
                        .map(this.mapChatMemberToMentionItem)
                        .filter(Boolean)

                    all.push(...chunk)
                    next = Boolean(data.next)
                    page += 1
                }

                state.all = all
                state.loadedAll = true
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                state.loadingAll = false
            }
        },
        async getChatMemberFeed(queryText) {
            const raw = String(queryText || '')
            const normalized = raw.startsWith('@') ? raw.slice(1) : raw

            if (/\s/.test(normalized)) return []

            const q = normalized.trim().toLowerCase()

            if (this.commentEditor && Array.isArray(this.mentionsData) && this.mentionsData.length) {
                const all = this.getMentionsFromProps()
                if (!q) return all
                return all.filter(u => String(u.name || '').toLowerCase().includes(q))
            }

            if (!this.chat_uid) return []

            const state = this.chatMention

            if (!state.loadedAll)
                await this.loadAllChatMembers()

            if (!q) return state.all

            return state.all.filter(u => String(u.name || '').toLowerCase().includes(q))
        },
        renderChatMember(item) {
            if (item.__loading) {
                const el = document.createElement('div')
                el.textContent = 'Загрузка...'
                el.style.opacity = '0.6'
                el.style.padding = '6px 8px'
                return el
            }

            const el = document.createElement('div')
            el.className = 'ck-mention-user'
            el.style.display = 'flex'
            el.style.alignItems = 'center'
            el.style.gap = '8px'
            el.style.padding = '4px 6px'

            const avatar = document.createElement('div')
            avatar.style.width = '20px'
            avatar.style.height = '20px'
            avatar.style.borderRadius = '50%'
            avatar.style.overflow = 'hidden'
            avatar.style.flexShrink = '0'
            avatar.style.background = item.color || '#d9d9d9'
            avatar.style.display = 'flex'
            avatar.style.alignItems = 'center'
            avatar.style.justifyContent = 'center'
            avatar.style.color = '#fff'
            avatar.style.fontSize = '10px'

            if (item.avatar && item.avatar.path) {
                const img = document.createElement('img')
                img.src = item.avatar.path
                img.style.width = '100%'
                img.style.height = '100%'
                img.style.objectFit = 'cover'
                avatar.appendChild(img)
            } else
                avatar.textContent = item.name ? item.name.charAt(0) : '?'

            const name = document.createElement('span')
            name.textContent = item.name
            name.style.whiteSpace = 'nowrap'
            name.className = 'mnt_user_name'

            el.appendChild(avatar)
            el.appendChild(name)

            return el
        },
        changeHandler(event) {
            this.$emit('input', event)
        },
        getFeedItems(queryText) {
            if(!this.taskId)
                return null
            return new Promise( resolve => {

                setTimeout(async () => {
                    let itemsToDisplay = await this.getSubtaskList(this.taskId)
                    itemsToDisplay = itemsToDisplay
                        // Filter out the full list of all items to only those matching the query text.
                        .filter( isItemMatching )
                        // Return 10 items max - needed for generic queries when the list may contain hundreds of elements.
                        .slice( 0, 10 )

                    resolve( itemsToDisplay )
                }, 100 )
            } )

            function isItemMatching(item) {
                const searchString = queryText.toLowerCase();
                return (
                    String(item.name).toLowerCase().includes( searchString ) ||
                    String(item.id).toLowerCase().includes( searchString )
                )
            }
        },
        customItemRenderer( item ) {
            const itemElement = document.createElement( 'div' );
            // itemElement.classList.add('ck-autocomplete-list');
            // itemElement.id = `mention-list-item-id-${ item.userId }`;

            const truncateLength = 10
            let taskName = item.name
            if(taskName.length > truncateLength)
                taskName = taskName.slice(0, truncateLength) + '...'

            itemElement.textContent = item.id;
            // itemElement.setAttribute('href', item.counter)1
            // const usernameElement = document.createElement( 'span' );

            // usernameElement.classList.add( 'custom-item-username' );
            // usernameElement.textContent = item.id;

            // itemElement.appendChild( usernameElement );

            return itemElement;
        },
        async getSubtaskList(parentId) {
            const params = {
                parent: parentId,
                page_size: 'all'
            }

            try {
                const { data } = await this.$http('/tasks/task/list/', { params: params })
                const subtaskList = data.results.map(item => {
                    return {
                        id: `#${item.counter} ${item.name}`,
                        objectType: 'task',
                        objectClass: 'blue_color cursor-pointer',
                        objectId: item.id,
                        name: item.name,
                    }
                })
                return subtaskList
            } catch(error) {
                errorHandler({error, show: false})
            }
        },
    }
}
