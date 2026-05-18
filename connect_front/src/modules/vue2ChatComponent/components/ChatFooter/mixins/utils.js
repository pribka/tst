export default {
    methods: {
        getContainer() {
            if(this.isMobile) {
                return document.querySelector('.chat_page_wrapper')
            } else
                return document.querySelector('.chat_body')
        },

        getMessageText() {
            let m = this.message?.text.trim().length > 0 ? this.message.text : this.messageModal.text

            return m.replace(/\r\n|\r|\n/g, "<br />")
        },
        async dataURItoBlob(dataURI) {
            var mimeString = dataURI.split(',')[0].split(':')[1].split(';')[0]; // тип пантомимы
            var byteString = atob(dataURI.split(',')[1]); // декодирование base64
            var arrayBuffer = new ArrayBuffer(byteString.length); // Создаем буферный массив
            var intArray = new Uint8Array(arrayBuffer); // Создаем представление

            for (var i = 0; i < byteString.length; i++) {
                intArray[i] = byteString.charCodeAt(i);
            }
            return new Blob([intArray], { type: mimeString });
        },
    }
}