<template>
    <a-drawer
        :title="$t('team.organization_map')"
        :visible="visible"
        class="org_map_drawer"
        @close="visible = false"
        destroyOnClose
        :zIndex="zIndex"
        :width="drawerWidth"
        placement="right">
        <div class="drawer_body">
            <div class="flex items-center mb-4">
                <flowy-new-block
                    v-for="(block, index) in blocks"
                    :key="index"
                    @drag-start="onDragStartNewBlock"
                    @drag-stop="onDragStopNewBlock">
                    <template v-slot:preview="{}">
                        <demo-block 
                            :block="block" 
                            :title="block.preview.title"
                            :description="block.preview.description"/>
                    </template>
                    <template v-slot:node="{}">
                        <TreeNode 
                            :block="block"
                            :title="block.node.title"
                            :description="block.preview.description"/>
                    </template>
                </flowy-new-block>
            </div>
            <flowy
                class="q-mx-auto"
                :nodes="nodes"
                :beforeMove="beforeMove"
                :beforeAdd="beforeAdd"
                @add="add"
                @move="move"
                @remove="remove"
                @drag-start="onDragStart"></flowy>
        </div>
    </a-drawer>
</template>

<script>
import eventBus from '@/utils/eventBus'
import TreeNode from './TreeNode.vue'
import Vue from 'vue'
Vue.component('TreeNode', TreeNode)
export default {
    name: "OrganizationMapDrawer",
    components: {
        'demo-block': () => import('./Preview.vue'),
        'TreeNode': TreeNode
    },
    props: {
        zIndex: {
            type: Number,
            default: 1010
        }
    },
    computed: {
        windowWidth() {
            return this.$store.state.windowWidth
        },
        drawerWidth() {
            if(this.windowWidth > 1200)
                return this.windowWidth - 250
            else
                return this.windowWidth
        },
    },
    created() {
        eventBus.$on('org_map_open', () => {
            this.visible = true
        })
    },
    data() {
        return {
            dragging: false,
            visible: false,
            blocks: [
                {
                    preview: {
                        title: 'New visitor',
                    },
                    node: {
                        title: 'New visitor',
                        description: '<span>When a <b>new visitor</b> goes to <b>Site 1</span></span>',
                    },
                },
                {
                    preview: {
                        title: 'Update database',
                        icon: 'error',
                    },
                    node: {
                        title: 'Update database',
                        description: '<span>Triggers when somebody performs a <b>specified action</b></span>',
                    },
                },
                {
                    preview: {
                        title: 'Time has passed',
                    },
                    node: {
                        title: 'Time has passed',
                        description: 'Triggers after a specified <b>amount</b> of time',
                    },
                },
                {
                    preview: {
                        title: 'Cannot be added',
                    },
                    node: {
                        title: 'Time has passed',
                        description: 'Triggers after a specified <b>amount</b> of time',
                        canBeAdded: false,
                    },
                },
            ],
            nodes: [
                {
                    id: '1',
                    parentId: -1,
                    nodeComponent: 'TreeNode',
                    data: {
                        text: 'Parent block',
                        title: 'New Visitor',
                        description: '<span>When a <b>new visitor</b> goes to <i>Site 1</i></span>',
                    },
                },
                {
                    id: '2',
                    parentId: '1',
                    nodeComponent: 'TreeNode',
                    data: {
                        text: 'Parent block',
                        title: 'New Visitor',
                        description: '<span>When a <b>new visitor</b> goes to <i>Site 1</i></span>',
                    },
                },
                {
                    id: '3',
                    parentId: '1',
                    nodeComponent: 'TreeNode',
                    data: {
                        text: 'Parent block',
                        title: 'New Visitor',
                        description: '<span>When a <b>new visitor</b> goes to <i>Site 1</i></span>',
                    },
                },
            ]
        }
    },
    methods: {
        onDragStartNewBlock (event) {
            console.log('onDragStartNewBlock', event);
            // contains all the props and attributes passed to demo-node
            const { props } = event
            this.newDraggingBlock = props;
        },
        onDragStopNewBlock (event) {
            console.log('onDragStopNewBlock', event);
            this.newDraggingBlock = null;
        },
        // REQUIRED
        beforeMove ({ to, from }) {
            // called before moving node (during drag and after drag)
            // indicator will turn red when we return false
            // from is null when we're not dragging from the current node tree
            console.log('beforeMove', to, from);

            // we cannot drag upper parent nodes in this demo
            if (from && from.parentId === -1) {
                return false;
            }
            // we're adding a new node (not moving an existing one)
            if (from === null) {
                // we've passed this attribute to the demo-node
                if (this.newDraggingBlock['custom-attribute'] === false) {
                    return false
                }
            }

            return true;
        },
        // REQUIRED
        beforeAdd ({ to, from }) {
            // called before moving node (during drag and after drag)
            // indicator will turn red when we return false
            // from is null when we're not dragging from the current node tree
            console.log('beforeAdd', to, from);

            // we've passed this attribute to the demo-node
            if (this.newDraggingBlock['custom-attribute'] === false) {
                return false
            }

            return true;
        },
        randomInteger () {
            return Math.floor(Math.random() * 10000) + 1;
        },
        generateId (nodes) {
            return this.randomInteger();
        },
        addNode (_event) {
            const id = this.generateId();
            this.nodes.push({
                ..._event.node,
                id,
            });
        },
        remove (event) {
            console.log('remove', event)

            // node we're dragging to
            const { node } = event

            // we use lodash in this demo to remove node from the array
            const nodeIndex = this.nodes.findIndex(f => f.id === node.id)
            this.nodes.splice(nodeIndex, 1);
        },
        move (event) {
            console.log('move', event);

            // node we're dragging to and node we've just dragged
            const { dragged, to } = event;

            // change panentId to id of node we're dragging to
            dragged.parentId = to.id;
        },
        add (event) {
            // every node needs an ID
            const id = this.generateId();

            // add to array of nodes
            this.nodes.push({
                id,
                ...event.node,
            });
        },
        onDragStart (event) {
            console.log('onDragStart', event);
            this.dragging = true;
        },
    },
    beforeDestroy() {
        eventBus.$off('org_map_open')
    }
}
</script>

<style lang="scss" scoped>
.org_enter_drawer{
    &::v-deep{
        .ant-drawer-wrapper-body,
        .ant-drawer-content{
            overflow: hidden;
            padding: 0px;
        }
        .ant-drawer-header{
            padding-left: 20px;
            padding-right: 20px;
        }
        .ant-drawer-body{
            height: calc(100% - 40px);
            padding: 0px;
        }
        .drawer_body{
            height: 100%;
            overflow: auto;
            padding: 20px;
            width: 100%;
        }
    }
}
</style>