export default {
    organizationChildrenById: state => id => {
        return state.organizationChildren[id]       
    }
}