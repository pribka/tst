<template>
    <div class="flex">
        <div class="mr-3">
        
           

            <!-- element that initializes the dropdown -->
            <a-popover :title="title" v-if="profile !== null">
                <template slot="content">
                    <div class="p-4 flex">
                        <div>
                            <a-avatar class="m-0" :src="avatar"  />
                        </div>
                        <div class="flex-column ml-4">
                            <div>
                                <span>
                                    {{
                                        profile !== undefined
                                            ? profile.last_name
                                            : ""
                                    }}
                                </span>
                                <span>
                                    {{
                                        profile !== undefined
                                            ? profile.first_mame
                                            : ""
                                    }}
                                </span>
                                <span>
                                    {{
                                        profile !== undefined
                                            ? profile.middle_mame
                                            : ""
                                    }}
                                </span>
                            </div>

                            <div>
                                <span class="font-bold">Email:</span>
                                <span>{{
                                    profile !== undefined ? profile.email : ""
                                }}</span>
                            </div>
                            <div>
                                <span class="font-bold">Телефон:</span>
                                <span>{{
                                    profile !== undefined ? profile.phone : ""
                                }}</span>
                            </div>
                        </div>
                    </div>
                </template>
                <!-- items and elements within the menu or custom dropdown -->
                <a-avatar
                  
                    class="m-0"
                    :src="avatar"
                 
                    icon="user"/>
            </a-popover>
        </div>
        <div class="leading-tight">
            <p class="font-medium" v-if="title">{{ title }}</p>
            <p class="font-medium" v-else-if="profile">{{ profile['last_name'] }}  {{ profile['first_name'] }}  {{ profile['middle_name'] }} </p>
            <span class="text-xs" v-if="subtitle">{{ subtitle }} </span>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        avatar: [String],
        title: [String],
        subtitle: [String],
        profile: [Object],
    },
};
</script>

<style>
</style>
