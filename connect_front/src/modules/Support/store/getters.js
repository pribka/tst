export default {
    canCreate: state => !!state.actions?.create,
    canUpdate: state => !!state.actions?.update,
    canDelete: state => !!state.actions?.delete
}
