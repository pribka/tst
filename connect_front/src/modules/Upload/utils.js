export const getFileExtension = (filename) => {
    let ext = /^.+\.([^.]+)$/.exec(filename)
    return ext == null ? "" : ext[1]
}

export const hashString = (s) => {
    return s.split("").reduce(function(a,b){a=((a<<5)-a)+b.charCodeAt(0);return a&a},0)
}

export const checkImageWidthHeight = (file) => {
    return new Promise(function (resolve) {
        let img = new Image();
        img.onload = function () {
            const width = img.width,
                height = img.height;

            resolve({width, height});
        };
        img.src = window.URL.createObjectURL(file);
    })
}
