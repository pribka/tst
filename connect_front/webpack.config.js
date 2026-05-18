const resolve = dir => require('path').join(__dirname, dir)

module.exports = {
    resolve: {
        alias: {
            '@': resolve('./src'),
            '@app': resolve('./src/modules'),
            'AutoNumeric': resolve('./node_modules/autonumeric/dist/autoNumeric.min')
        }
    }
}
