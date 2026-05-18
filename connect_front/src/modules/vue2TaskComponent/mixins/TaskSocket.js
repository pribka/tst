export default {
    sockets: {
        listeners(val) { 
            if(val)
                this.viewUsers = val
            else
                this.viewUsers = []
        }
    },
    created() {
        this.$socket.client.emit("tasks") 
    },
    beforeDestroy() {
        // this.$socket.client.emit("leave_doc_view_room", this.id) 
    }
}