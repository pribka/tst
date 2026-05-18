export const itemProps = {
    mentionsData: {
        type: Array,
        default: () => []
    },
    bodySelector: {
        type: String,
        default: 'body'
    },
    item: {
        type: Object,
        required: true
    },
    user: {
        type: Object,
        required: true
    },
    related_object: {
        type: [String, Number],
        required: true
    },
    model: {
        type: String,
        required: false
    },
    parent: {
        type: Object,
        default: null
    },
    extendDrawerZIndex: {
        type: Number,
        default: 1000
    },
    showUsers: {
        type: Boolean,
        default: true
    },
    showEmoji: {
        type: Boolean,
        default: true
    },
    showFileUpload: {
        type: Boolean,
        default: true
    },
    addTaskCheck: {
        type: Boolean,
        default: true
    },
    shareCheck: {
        type: Boolean,
        default: true
    },
    pushNewComment: {
        type: Function,
        default: () => {}
    },
    updateComment: {
        type: Function,
        default: () => {}
    },
    deleteComment: {
        type: Function,
        default: () => {}
    },
    modal: {
        type: Boolean,
        default: false
    },
    reply: {
        type: Boolean,
        default: true
    },
    openCheck: {
        type: Boolean,
        default: true
    },
    updateNewComment: {
        type: Function,
        default: () => {}
    },
    toggleNewCommentCount: {
        type: Function,
        default: () => {}
    },
    getModalContainer: {
        type: Function,
        default: () => document.body
    },
    closeMainInput: {
        type: Function,
        default: () => {}
    },
    setBlockLeft: {
        type: Function,
        default: () => {}
    },
    blockLeft: {
        type: Boolean,
        default: false
    },
    useShare: {
        type: Boolean,
        default: false
    },
    useVisibility: {
        type: Boolean,
        default: false
    },
    commentDateTimeFormat: {
        type: String,
        default: 'HH:mm'
    },
}

export const inputProps = {
    mentionsData: {
        type: Array,
        default: () => []
    },
    related_object: {
        type: [String, Number],
        required: true
    },
    model: {
        type: String,
        required: false
    },
    parent: {
        type: Object,
        default: null
    },
    showUsers: {
        type: Boolean,
        default: true
    },
    oneUpload: {
        type: Boolean,
        default: false
    },
    createFounder: {
        type: Boolean,
        default: true
    },
    showEmoji: {
        type: Boolean,
        default: true
    },
    showFileUpload: {
        type: Boolean,
        default: true
    },
    closeEditorFunc: {
        type: Function,
        default: () => {}
    },
    pushNewComment: {
        type: Function,
        default: () => {}
    },
    updateComment: {
        type: Function,
        default: () => {}
    },
    modal: {
        type: Boolean,
        default: false
    },
    inputPlaceholder: {
        type: String,
        default: () => 'comment.addComment'
    },
    editData: {
        type: Object,
        default: () => null
    },
    getModalContainer: {
        type: Function,
        default: () => document.body
    },
    setBlockLeft: {
        type: Function,
        default: () => {}
    },
    blockLeft: {
        type: Boolean,
        default: false
    },
    useVisibility: {
        type: Boolean,
        default: false
    },
    defaultPublic: {
        type: Boolean,
        default: false
    },
}

export const modalProps = {
    mentionsData: {
        type: Array,
        default: () => []
    },
    related_object: {
        type: [String, Number],
        required: true
    },
    model: {
        type: String,
        required: false
    },
    pDeleteComment: {
        type: Function,
        default: () => {}
    },
    allowComments: {
        type: Boolean,
        default: true
    },
    createFounder: {
        type: Boolean,
        default: true
    },
    oneUpload: {
        type: Boolean,
        default: false
    },
    showEmoji: {
        type: Boolean,
        default: true
    },
    showFileUpload: {
        type: Boolean,
        default: true
    },
    showUsers: {
        type: Boolean,
        default: true
    },
    getModalContainer: {
        type: Function,
        default: () => document.body
    },
    setBlockLeft: {
        type: Function,
        default: () => {}
    },
    blockLeft: {
        type: Boolean,
        default: false
    },
    commentDateTimeFormat: {
        type: String,
        default: 'HH:mm'
    }
}

export const mainProps = {
    mentionsData: {
        type: Array,
        default: () => []
    },
    bodySelector: {
        type: String,
        default: 'body'
    },
    related_object: { // id элемента к которому привязываем комментарии, можем привязать к чему угодно
        type: [String, Number],
        required: true
    },
    model: { // Может быть news, file, club
        type: String,
        required: false
    },
    extendDrawerZIndex: {
        type: Number,
        default: 1000
    },
    mainClass: {
        type: String,
        default: ''
    },
    allowComments: {
        type: Boolean,
        default: true
    },
    showUsers: {
        type: Boolean,
        default: true
    },
    oneUpload: {
        type: Boolean,
        default: false
    },
    createFounder: {
        type: Boolean,
        default: true
    },
    showEmoji: {
        type: Boolean,
        default: true
    },
    showFileUpload: {
        type: Boolean,
        default: true
    },
    addTaskCheck: {
        type: Boolean,
        default: true
    },
    shareCheck: {
        type: Boolean,
        default: true
    },
    modalContainer: {
        type: Boolean,
        default: true
    },
    commentLimit: {
        type: Boolean,
        default: false
    },
    limitCount: {
        type: Number,
        default: 2
    },
    injectContainer: {
        type: Boolean,
        default: false
    },
    injectContainerSelector: {
        type: Function,
        default: () => document.body
    },
    initScroll: {
        type: Boolean,
        default: false
    },
    useVisibility: {
        type: Boolean,
        default: false
    },
    defaultPublic: {
        type: Boolean,
        default: false
    },
    suffix_socket_name:{
        type: String,
        default: ''
    },
    commentDateTimeFormat: {
        type: String,
        default: 'HH:mm'
    },
}
