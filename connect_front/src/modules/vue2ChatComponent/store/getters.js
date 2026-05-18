export default {
    chatMessages: (state) => (id) => {
        if (state.chatMessage?.[id])
            return state.chatMessage[id]
        else
            return null
    },
    chatMembers: (state) => (id) => {
        if (state.chatMembers?.[id])
            return state.chatMembers[id]
        else
            return null
    },
    replyMessage: state => id => {
        if (state.replyMessage?.[id])
            return state.replyMessage[id]
        else
            return null
    },
    replyMessageModal: state => id => {
        if (state.replyMessageModal?.[id])
            return state.replyMessageModal[id]
        else
            return null
    },
    getFileList: state => id => {
        if (state.fileList?.[id])
            return state.fileList[id]
        else
            return []
    },
    getFileListSend: state => id => {
        if (state.fileList?.[id])
            return state.fileList[id].map(el => el.file)
        else
            return []
    },
    getFileModal: state => id => {
        if (state.fileModal?.[id])
            return state.fileModal[id]
        else
            return false
    },
    chatDraft: state => id => {
        if (state.chatDrafts?.[id])
            return state.chatDrafts[id]
        else
            return null
    },
    getStatusUser: state => user_uid => {

        const find = state.statusUsers.find(item => item.user_uid === user_uid)
        if (find !== undefined) {
            return find
        }
        return false
    },
    getTyping: state => chat_uid => {
        if (state.typingList[chat_uid])
            return state.typingList[chat_uid]
        return false
    },
    getCountMessages: state => chat_uid => {
        const findIndex = state.chatList.findIndex(el => el.chat_uid === chat_uid)
        if (findIndex !== -1) {
            return state.chatList[findIndex].new_message_count
        }
        return 0
    },
    chatHistoryState: state => chat_uid => {
        if (state.chatHistoryStateByChat?.[chat_uid])
            return state.chatHistoryStateByChat[chat_uid]
        return null
    },
    helpDeskList: state => state.helpDeskList,
    helpDeskNext: state => state.helpDeskNext
}
