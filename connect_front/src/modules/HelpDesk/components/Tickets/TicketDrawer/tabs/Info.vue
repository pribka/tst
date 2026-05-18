<template>
    <a-row
        ref="ticketBodyWrap"
        :gutter="{xs: 15, md: 20, lg: 30, xxl: 30}"
        class="h-full ticket_drawer"
        :class="`layout-${layoutMode}`">
        <template>
            <a-col
                v-if="!isMobile"
                class="description-block"
                :xs="24"
                :md="24"
                :xl="desc3Xl"
                :xxl="desc3Xl">
                <ListViewItem >
                    <div>
                        <a-form-model-item v-if="edit" ref="description" label="" prop="description">
                            <div class="w-full description_editor relative z-10">
                                <component
                                    :is="ckEditor"
                                    :taskId="form.id || null"
                                    :placeholder="$t('helpdesk.description')"
                                    :key="form.id"
                                    v-model="form.description"
                                    @change="dataChange({field: 'description', useTimer: true})" />
                            </div>
                        </a-form-model-item>
                        <TextViewer
                            v-else
                            class="body_text"
                            :body="ticket.description" />
                    </div>
                </ListViewItem>
                <ListViewItem v-if="tab === 'info'" class="mt-5">
                    <div class="mb-1 font-semibold">
                        {{ $t('task.comments') }}
                    </div>
                    <vue2CommentsComponent
                        bodySelector=".ticket_drawer"
                        :related_object="ticket.id"
                        :suffix_socket_name="isClientView?'public_':''"
                        commentDateTimeFormat="DD.MM.YYYY HH:mm"
                        model="help_desk_tickets"
                        injectContainer
                        :injectContainerSelector="getCommentsContainer"
                        initScroll
                        :useVisibility="isClientView?false:true"
                        :defaultPublic="false" />
                </ListViewItem>
            </a-col>

            <a-col
                class="right-sidebar"
                style="padding-right: 0px;"
                :xs="24"
                :md="24"
                :xl="sidebar3Xl"
                :xxl="sidebar3Xl">
                <!-- ЧАТ УБРАН ИЗ ПОТОКА САЙДБАРА (теперь он всплывающий ниже) -->

                <div class="info-block">
                    <a-button
                        v-if="canTakeTicketInInfo"
                        block
                        class="mb-4"
                        icon="fi-rr-user-add"
                        flaticon
                        type="flat_primary"
                        @click="takeItem()">
                        {{ $t('helpdesk.take_ticket') }}
                    </a-button>
                    <div
                        v-if="['completed', 'rejected'].includes(ticket.status.code)"
                        class="mb-4">
                        <CompletedBanner
                            ref="completedBanner"
                            :ticket="ticket"
                            :actions="actions"
                            :edit="edit"
                            :getTicket="getTicket" />
                    </div>
                    <a-form-model
                        ref="ruleForm"
                        :model="form"
                        class="mini_form pb-5"
                        :rules="rules">
                        <DrawerAside>
                            <ListView inline labelDark class="aside-grid">
                                <ListViewItem
                                    v-if="!['completed', 'rejected'].includes(ticket.status.code)"
                                    class="meeting_list_item"
                                    bottomBorder>
                                    <div class="meeting_section">
                                        <div class="meeting_section__label mb-1">
                                            {{ $t('helpdesk.task_meeting') }}
                                        </div>
                                        <template v-if="ticket.meeting">
                                            <div
                                                v-if="ticket.meeting.status"
                                                class="mb-2 flex items-center">
                                                <span class="mr-2">{{ $t('helpdesk.status') }}:</span>
                                                <component :is="meetingStatus" :status="ticket.meeting.status" />
                                            </div>
                                            <div
                                                v-if="ticket.meeting.id"
                                                class="mb-2 cursor-pointer blue_color flex items-center"
                                                @click="openMeeting()">
                                                <i class="fi fi-rr-redo mr-1" />
                                                {{ $t('helpdesk.open_meeting') }}
                                            </div>
                                            <div class="flex items-center gap-2">
                                                <a-button
                                                    v-if="ticket.meeting.url"
                                                    block
                                                    icon="fi-rr-video-camera-alt"
                                                    flaticon
                                                    :loading="meetingLoading"
                                                    type="flat_primary"
                                                    @click="openMeetingInviteModal()">
                                                    {{ ticket.meeting.status === 'online' ? $t('helpdesk.join_meeting') : (ticket.meeting.status === 'ended' ? $t('helpdesk.start_new_session') : $t('helpdesk.start_meeting')) }}
                                                </a-button>
                                                <a-button
                                                    v-if="ticket.meeting.url_external"
                                                    icon="fi-rr-link-alt"
                                                    flaticon
                                                    v-tippy
                                                    :content="$t('copy_link')"
                                                    type="flat_primary"
                                                    @click="copyMeeting()" />
                                            </div>
                                        </template>
                                        <div v-else class="mt-1">
                                            <a-button
                                                block
                                                icon="fi-rr-video-camera-alt"
                                                flaticon
                                                :loading="meetingLoading"
                                                type="flat_primary"
                                                @click="openMeetingInviteModal()">
                                                {{ $t('helpdesk.create_meeting') }}
                                            </a-button>
                                        </div>
                                        <a-button
                                            v-if="canStartTicketCallInInfo"
                                            block
                                            class="mt-2"
                                            type="flat_primary"
                                            icon="fi-rr-phone-flip"
                                            flaticon
                                            :loading="callLoading"
                                            @click="startTicketCall()">
                                            {{ $t('chat.call') }}
                                        </a-button>
                                        <div
                                            v-if="showContactPersonNotRegisteredAlert"
                                            class="mt-2">
                                            <a-alert
                                                type="warning"
                                                show-icon
                                                :message="$t('helpdesk.meeting_contact_not_registered')" />
                                        </div>
                                    </div>
                                </ListViewItem>
                                <ListViewItem v-if="ticket.customer_card && ticket.customer_card.tags.length" bottomBorder>
                                    <TagsList :tags="ticket.customer_card.tags" />
                                </ListViewItem>
                                <ListViewItem v-if="(edit && isInternalChatChannel) || ticket.customer_card" :title="$t('table.contractor_member')">
                                    <template v-if="edit && isInternalChatChannel">
                                        <ListViewModal
                                            endpoint="help_desk/customer_cards/"
                                            tableType="clients"
                                            pageName="helpdesk_clients_all"
                                            :title="$t('helpdesk.contractor_name')"
                                            model="help_desk.CustomerCardModel"
                                            @select="selectClient"
                                            ref="listViewModalClientsRef"/>
                                        <a-form-model-item class="mb-0">
                                            <DSelect
                                                v-model="form.customer_card"
                                                apiUrl="/app_info/filtered_select_list/?model=help_desk.CustomerCardModel"
                                                class="w-full"
                                                :showAllHandler="openAllClients"
                                                infinity
                                                size="default"
                                                resultsKey="filteredSelectList"
                                                inputType="ghost"
                                                showSearch
                                                initList
                                                :initOptionList="initListClient"
                                                :useOptionFlex="false"
                                                useSearchApi
                                                :selectUID="clientUUID"
                                                :placeholder="$t('helpdesk.assign_contractor_placeholder')"
                                                searchKey="search"
                                                labelKey="string_view"
                                                :listObject="false"
                                                :default-active-first-option="false"
                                                :filter-option="false"
                                                :not-found-content="null"
                                                @select="selectClientId"
                                                @change="handleCustomerCardChange">
                                                <template #suffixSlot>
                                                    <a-spin v-if="getClientLoading" size="small" />
                                                    <a-button
                                                        v-else
                                                        type="ui"
                                                        ghost
                                                        shape="circle"
                                                        size="small"
                                                        flaticon
                                                        v-tippy
                                                        :content="$t('helpdesk.add_contractor')"
                                                        icon="fi-rr-user-add"
                                                        @click="addClient()"/>
                                                </template>
                                            </DSelect>
                                        </a-form-model-item>
                                    </template>
                                    <div v-else class="row-inline">
                                        <span>
                                            {{ ticket.customer_card.name }}
                                        </span>
                                        <i
                                            @click="openClient()"
                                            style="color: blue; cursor: pointer;"
                                            class="fi fi-rr-share-square"/>
                                    </div>
                                </ListViewItem>
                                <ListViewItem v-if="isClientView && ticket.org_admin" :title="$t('helpdesk.organization')">
                                    {{ ticket.org_admin.name }}
                                </ListViewItem>
                                <ListViewItem v-if="isClientView && ticket.created_at"  :title="$t('helpdesk.creation_date')">
                                    {{ $moment(ticket.created_at).format('DD.MM.YYYY') }}
                                </ListViewItem>
                                <ListViewItem v-if="(edit && isInternalChatChannel) || ticket.analytics_key" :title="$t('helpdesk.work_contour')">
                                    <template v-if="edit && isInternalChatChannel">
                                        <a-form-model-item class="mb-0" ref="analytics_key" label="" prop="analytics_key">
                                            <ContractSelect
                                                :key="`ticket_analytics_key_${form.customer_card || 'empty'}_${contractSelectKey}`"
                                                v-model="form.analytics_key"
                                                class="w-full"
                                                :apiUrl="contractSelectApiUrl"
                                                :params="contractSelectParams"
                                                listObject="filteredSelectList"
                                                inputType="ghost"
                                                size="default"
                                                :title="$t('helpdesk.work_contour')"
                                                valueKey="id"
                                                labelKey="string_view"
                                                searchKey="search"
                                                :showIcon="false"
                                                :showSearch="true"
                                                :showRecent="false"
                                                :showClear="true"
                                                :showArrow="true"
                                                :initList="Boolean(form.customer_card)"
                                                :useSearchApi="false"
                                                :disabled="!form.customer_card"
                                                :placeholder="$t('helpdesk.select_work_contour')"
                                                @change="handleAnalyticsKeyChange" />
                                        </a-form-model-item>
                                    </template>
                                    <span v-else :title="ticket.analytics_key.string_view">
                                        {{ ticket.analytics_key.string_view }}
                                    </span>
                                </ListViewItem>
                                <!-- CONTACT PERSON: VIEW/EDIT -->
                                <ListViewItem v-if="(edit && isInternalChatChannel) || ticket.contact_person" :title="$t('helpdesk.contact_person')">
                                    <template v-if="edit && isInternalChatChannel">
                                        <ListViewModal
                                            :endpoint="contactPersonEndpoint"
                                            tableType="contact_person"
                                            :title="$t('helpdesk.contact_persons')"
                                            pageName="helpdesk_contact_person_all"
                                            model="help_desk.ContactPersonModel"
                                            @select="selectContactPerson"
                                            :add="addContact"
                                            @close="getSLA"
                                            ref="listViewModalConctactPersonRef">
                                            <template v-slot:headerLeft="{ rowSelected }">
                                                <SLASelect
                                                    v-if="rowSelected"
                                                    :selectItem="rowSelected"
                                                    :params="{ contractor: orgAdminClient }"
                                                    pageName="helpdesk_contact_person_all"
                                                    model="help_desk.ContactPersonModel" />
                                            </template>
                                        </ListViewModal>
                                        <a-form-model-item ref="contact_person" label="" prop="contact_person">
                                            <DSelect
                                                :key="`${form.customer_card || 'empty'}_${personKey}`"
                                                v-model="form.contact_person"
                                                :apiUrl="contactPersonEndpoint"
                                                class="w-full"
                                                :selectUID="contactUUID"
                                                infinity
                                                :useOptionFlex="false"
                                                :disabled="!form.customer_card"
                                                size="default"
                                                inputType="ghost"
                                                :showAllHandler="openAllConctactPersons"
                                                :initOptionList="initListContactPerson"
                                                showSearch
                                                useSearchApi
                                                showPlaceholder
                                                :placeholder="$t('helpdesk.assign_contractor')"
                                                searchKey="search"
                                                labelKey="name"
                                                :listObject="false"
                                                :default-active-first-option="false"
                                                :filter-option="false"
                                                :not-found-content="null"
                                                @change="handleContactPersonChange"
                                                @changeFull="changeFullPerson">
                                                <template #suffixSlot>
                                                    <div class="flex items-center gap-2">
                                                        <a-button
                                                            v-if="form.contact_person && fullPerson"
                                                            type="ui"
                                                            ghost
                                                            shape="circle"
                                                            size="small"
                                                            flaticon
                                                            v-tippy
                                                            :content="$t('helpdesk.edit_contact_person')"
                                                            icon="fi-rr-user-pen"
                                                            @click="editContact()"/>
                                                        <a-button
                                                            type="ui"
                                                            ghost
                                                            shape="circle"
                                                            size="small"
                                                            flaticon
                                                            :disabled="!form.customer_card"
                                                            v-tippy
                                                            :content="$t('helpdesk.add_contact_person')"
                                                            icon="fi-rr-user-add"
                                                            @click="addContact()"/>
                                                    </div>
                                                </template>
                                            </DSelect>
                                            <ContactModal
                                                v-if="edit"
                                                slaSelect
                                                :contractor="orgAdminClient"
                                                @change="getSLA()" />
                                        </a-form-model-item>
                                    </template>
                                    <ContactPerson
                                        v-else
                                        :contact_person="ticket.contact_person"
                                        showIcon
                                        placement="left" />
                                </ListViewItem>
                                <ListViewItem v-if="ticket.contact_person && ticket.contact_person.unknown">
                                    <template>
                                        <div class="flex gap-1">
                                            <CreateClientModal ref="clientClientModalRef" />
                                            <a-button type="primary" ghost @click="openCreateClientModal">
                                                {{ $t('helpdesk.create_contractor') }}
                                            </a-button>
                                            <a-button
                                                type="danger"
                                                ghost
                                                :loading="spamLoading"
                                                @click="maskAsSpam(ticket.contact_person)">
                                                {{ $t('helpdesk.to_spam') }}
                                            </a-button>
                                        </div>
                                    </template>
                                </ListViewItem>
                                <ListViewItem v-if="slaInfo">
                                    <a-spin :spinning="slaLoading" size="small" class="w-full">
                                        <component
                                            :is="slaComponent"
                                            :showRelated="false"
                                            :sla="slaInfo" />
                                    </a-spin>
                                </ListViewItem>
                                <ListViewItem vertical v-if="ticket.receipt_date" :title="$t('helpdesk.receipt_date')">
                                    <a-date-picker
                                        v-if="edit"
                                        v-model="form.receipt_date"
                                        inputType="ghost"
                                        format="DD.MM.YYYY HH:mm"
                                        size="small"
                                        :showTime="{format: 'HH:mm'}"
                                        :allowClear="false"
                                        showToday
                                        :getCalendarContainer="getCalendarContainer"
                                        class="w-full"
                                        :placeholder="$t('helpdesk.receipt_date')"
                                        @change="dataChange({field: 'receipt_date'})" />
                                    <span v-else class="truncate-text">
                                        {{ $moment(ticket.receipt_date).format('DD.MM.YYYY HH:mm') }}
                                    </span>
                                </ListViewItem>
                                <ListViewItem vertical v-if="ticket.start_date && !ticket.end_date" :title="$t('helpdesk.start_date')">
                                    <span>
                                        {{ $moment(ticket.start_date).format('DD.MM.YYYY') }}
                                    </span>
                                </ListViewItem>
                                <ListViewItem vertical v-if="ticket.status" :title="$t('helpdesk.status')">
                                    <template v-if="!isClientView && canChangeStatus" ref="status" label="" prop="status">
                                        <StatusSelect
                                            :value="ticket.status"
                                            :statusList="availableStatuses"
                                            :loading="statusLoader"
                                            statusListNameKey="name"
                                            optionViewType="bullets_"
                                            @change="actionsOpenFinishModal({ status: $event.code })" />
                                    </template>
                                    <a-tag v-else :color="ticket.status.color" block size="large">
                                        <span>{{ ticket.status.name }}</span>
                                    </a-tag>
                                </ListViewItem>
                                <ListViewItem vertical v-if="checkField({ key: 'category' })" :title="$t('helpdesk.category')">
                                    <a-form-model-item v-if="edit" ref="category" label="" prop="category">
                                        <DSelect
                                            v-model="form.category"
                                            apiUrl="/help_desk/ticket_categories/"
                                            class="w-full"
                                            infinity
                                            size="default"
                                            inputType="ghost"
                                            labelKey="name"
                                            valueKey="id"
                                            :initOptionList="initListCategory"
                                            :placeholder="$t('helpdesk.select_category')"
                                            :listObject="false"
                                            :params="{
                                                ...(currentOrgAdminId
                                                    ? { contractor: currentOrgAdminId }
                                                    : {})
                                            }"
                                            :default-active-first-option="false"
                                            :filter-option="false"
                                            :not-found-content="null"
                                            @change="dataChange({field: 'category'})" />
                                    </a-form-model-item>
                                    <span v-else class="truncate-text">
                                        {{ ticket.category.name }}
                                    </span>
                                </ListViewItem>
                                <ListViewItem :title="$t('helpdesk.priority')" v-if="!isClientView || ticket.priority">
                                    <a-form-model-item v-if="!isClientView && edit" ref="priority" label="" prop="priority">
                                        <a-select v-model="form.priority" inputType="ghost" @change="dataChange({field: 'priority'})">
                                            <a-select-option
                                                v-for="priority in priorityList"
                                                :key="priority.value"
                                                :value="priority.value">
                                                <ProirityCard :priority="priority" />
                                            </a-select-option>
                                        </a-select>
                                    </a-form-model-item>
                                    <ProirityCard v-else-if="curPriority" :priority="curPriority" />
                                    <span v-else class="truncate-text">
                                        {{ ticket.priority && ticket.priority.name ? ticket.priority.name : '-' }}
                                    </span>
                                </ListViewItem>
                                <ListViewItem v-if="checkField({ key: 'dead_line' })" :title="$t('helpdesk.deadline')">
                                    <a-form-model-item v-if="edit" ref="dead_line" prop="dead_line">
                                        <a-date-picker
                                            v-model="form.dead_line"
                                            inputType="ghost"
                                            format="DD.MM.YYYY"
                                            size="small"
                                            :showTime="{format: 'HH:mm'}"
                                            :allowClear="false"
                                            :getCalendarContainer="getCalendarContainer"
                                            class="w-full"
                                            :placeholder="$t('helpdesk.specify_deadline')"
                                            @change="dataChange({field: 'dead_line'})" />
                                    </a-form-model-item>
                                    <template v-else>
                                        <span class="truncate-text">
                                            {{ $moment(ticket.dead_line).format('DD.MM.YYYY') }}
                                        </span>
                                    </template>
                                </ListViewItem>
                                <ListViewItem v-if="isClientView && ticket.contact_person_user" :title="$t('helpdesk.user')">
                                    <Profiler
                                        :avatarSize="22"
                                        nameClass="text-sm"
                                        :user="ticket.contact_person_user" />
                                </ListViewItem>
                                <ListViewItem v-if="isClientView && ticket.specialist" :title="$t('helpdesk.responsible')">
                                    <div>
                                        <Profiler
                                            :avatarSize="22"
                                            nameClass="text-sm"
                                            :user="ticket.specialist" />
                                        <div style="color: #888888;font-size: 13px;">{{ ticket.specialist.is_reserve ? $t('helpdesk.is_reserve') : $t('helpdesk.is_reserve_main') }}</div>
                                    </div>
                                </ListViewItem>
                                <ListViewItem v-if="!isClientView" :title="$t('helpdesk.responsible')">
                                    <a-form-model-item v-if="edit" ref="specialist" label="" prop="specialist">
                                        <UserMiniSelect
                                            v-model="form.specialist"
                                            inputType="input"
                                            :showIcon="false"
                                            :apiUrl="userSelectApi"
                                            :storeName="currentCustomerCardId ? `${currentCustomerCardId}_user_select` : 'users_mini_select_empty'"
                                            placement="bottomLeft"
                                            :placeholder="$t('helpdesk.select_responsible')"
                                            @change="dataChange({field: 'specialist', valueKey: 'id'})">
                                            <template #item="{ work }">
                                                <div>
                                                    <a-avatar :size="20" icon="team" :src="work.avatar ? work.avatar.path : null" />
                                                </div>
                                                <div class="ml-2 truncate">
                                                    <div class="truncate">{{ work.full_name }}</div>
                                                    <div
                                                        class="truncate gray lowercase"
                                                        style="font-size: 10px;line-height: 12px;">
                                                        {{ work.is_reserve ? $t('helpdesk.is_reserve') : $t('helpdesk.is_reserve_main') }}
                                                    </div>
                                                </div>
                                            </template>
                                        </UserMiniSelect>
                                    </a-form-model-item>
                                    <Profiler
                                        v-else-if="ticket.specialist"
                                        :avatarSize="22"
                                        nameClass="text-sm"
                                        :user="ticket.specialist" />
                                </ListViewItem>
                                <ListViewItem  v-if="checkField({ key: 'visors', type: 'array' })" :title="$t('helpdesk.observers')">
                                    <a-form-model-item v-if="edit" ref="visors" label="" prop="visors">
                                        <UserDrawer
                                            v-model="form.visors"
                                            :taskId="ticket ? ticket.id : null"
                                            :id="ticket ? ticket.id : defaultUserSelectId"
                                            inputType="ghost"
                                            :metadata="{ key: 'visors', value: form.metadata }"
                                            :changeMetadata="changeMetadata"
                                            multiple
                                            inputSize="small"
                                            :title="$t('helpdesk.select_observers')"
                                            :inputPlaceholder="$t('helpdesk.assign_observers')"
                                            class="w-full clamp-2"
                                            @allClear="allVisorClear()"
                                            @change="dataChange({field: 'visors', valueKey: 'id', multiple: true, useTimer: true})" />
                                    </a-form-model-item>
                                    <div v-else class="flex gap-2 flex-wrap">
                                        <Profiler
                                            v-for="visor in filteredVisors"
                                            :key="visor.id"
                                            :avatarSize="22"
                                            nameClass="text-sm"
                                            :user="visor" />
                                    </div>
                                </ListViewItem>
                                <ListViewItem  v-if="ticket.channel" :title="$t('helpdesk.communication_channel')">
                                    <div class="row-inline pr-1">
                                        <span class="pr-2">{{ ticket.channel.name }}</span>
                                        <div v-if="ticket.channel.icon">
                                            <img
                                                v-if="isSVG(ticket.channel.icon)"
                                                :src="require(`@/assets/svg/${ticket.channel.icon}`)"
                                                class="lazyload mr-2 channel_icon" />
                                            <i
                                                v-else
                                                class="mr-2 fi"
                                                :class="ticket.channel.icon" />
                                        </div>
                                    </div>
                                </ListViewItem>
                                <ListViewItem v-if="showRelatedChat" :title="$t('helpdesk.created_from_chat')">
                                    <a class="related-chat-link" @click.prevent="openRelatedChat">
                                        {{ ticket.related_chat.name }}
                                    </a>
                                </ListViewItem>
                            </ListView>
                        </DrawerAside>
                        <MeetingInviteModal
                            :visible="inviteModalVisible"
                            :users="meetingInviteUsers"
                            :loading="meetingLoading"
                            @cancel="inviteModalVisible = false"
                            @invite="inviteAndStartMeeting" />

                        <DrawerAside v-if="showMembersBlock">
                            <TicketMembersBlock
                                :members="ticketMembersList"
                                :canEdit="canEdit"
                                :loading="membersLoading"
                                :memberRemovingId="memberRemovingId"
                                :orgAdminId="currentOrgAdminId"
                                @save="updateMembers"
                                @remove="removeMember" />
                        </DrawerAside>

                        <DrawerAside v-if="ticket.status.code === 'completed' && ticket.rating">
                            <ListView inline labelDark>
                                <ListViewItem :bottomBorder="false" :title="$t('helpdesk.rating')">
                                    <ViewRating :rating="ticket.rating.rating" labelView />
                                </ListViewItem>
                                <ListViewItem :bottomBorder="false" v-if="ticket.rating.description">
                                    <div class="clamp-2">
                                        {{ ticket.rating.description }}
                                    </div>
                                </ListViewItem>
                            </ListView>
                        </DrawerAside>
                    </a-form-model>
                </div>
            </a-col>
            <a-col
                v-if="isMobile"
                class="description-block"
                style=""
                :xs="24"
                :md="24"
                :xl="desc3Xl"
                :xxl="desc3Xl">
                <ListViewItem :bottomBorder="false">
                    <div>
                        <a-form-model-item v-if="edit" ref="description" label="" prop="description">
                            <div class="w-full description_editor relative z-10">
                                <component
                                    :is="ckEditor"
                                    :taskId="form.id || null"
                                    :placeholder="$t('helpdesk.description')"
                                    :key="form.id"
                                    v-model="form.description"
                                    @change="dataChange({field: 'description', useTimer: true})" />
                            </div>
                        </a-form-model-item>
                        <TextViewer
                            v-else
                            class="body_text"
                            :body="ticket.description" />
                    </div>
                </ListViewItem>
            </a-col>
            <!-- ✅ MOBILE ONLY: comments at the very bottom -->
            <div v-if="isMobile && tab === 'info'">
                <a-col
                    class="comments-mobile"
                    style="padding-right: 0px;"
                    :xs="24"
                    :md="24">
                    <a-collapse
                        v-model="expanded"
                        :bordered="false">
                        <a-collapse-panel
                            style="margin-top: 10px;"
                            key="comments"
                            :header="$t('task.comments')">
                            <div style="padding-left: 16px;">
                                <vue2CommentsComponent
                                    :suffix_socket_name="isClientView?'public_':''"
                                    class="task_info_collapse m-4"
                                    bodySelector=".ticket_drawer"
                                    :related_object="ticket.id"
                                    commentDateTimeFormat="DD.MM.YYYY HH:mm"
                                    model="help_desk_tickets"
                                    injectContainer
                                    :injectContainerSelector="getCommentsContainer"
                                    initScroll
                                    :useVisibility="true"
                                    :defaultPublic="false" />
                            </div>

                        </a-collapse-panel>
                    </a-collapse>
                </a-col>
            </div>
        </template>
    </a-row>
</template>

<script>
import priorityMixin from '../../../../priorityMixin.js'
import eventBus from '@/utils/eventBus'
import { mapState } from 'vuex'
import { errorHandler } from '@/utils/index.js'
import { formatSeconds } from '../../../../utils/utils.js'
let timer;
let reloadTimer;
export default {
    mixins: [priorityMixin],
    components: {
        DrawerAside: () => import('@apps/UIModules/DrawerAside'),
        DSelect: () => import('@apps/DrawerSelect/Select.vue'),
        ContractSelect: () => import('@apps/DrawerSelect/ContractSelect.vue'),
        UserDrawer: () => import("@apps/DrawerSelect/index.vue"),
        TagsList: () => import('../../../TagsList.vue'),
        ContactPerson: () => import('../../../ContactPerson.vue'),
        ProirityCard: () => import('../../../ProirityCard.vue'),
        ChatList: () => import('../components/ChatList/index.vue'),
        CompletedBanner: () => import('../components/ChatList/CompletedBanner.vue'),
        CreateClientModal: () => import('./CreateClientModal.vue'),
        ContactModal: () => import('../../../ContactModal.vue'),
        ListViewModal: () => import('@/components/ListView/ListViewModal.vue'),
        SLASelect: () => import('../../../SLASelect.vue'),
        UserMiniSelect: () => import('@apps/DrawerSelect/UserMiniSelect.vue'),
        TextViewer: () => import('@apps/CKEditor/TextViewer.vue'),
        ViewRating: () => import('../../../Request/RequestDrawer/components/ViewRating.vue'),
        ListViewItem: () => import('../components/ListItem.vue'),
        StatusSelect: () => import('@apps/DrawerSelect/StatusSelect.vue'),
        MeetingInviteModal: () => import('../components/MeetingInviteModal.vue'),
        TicketMembersBlock: () => import('../components/TicketMembersBlock.vue'),

        // ✅ comments
        vue2CommentsComponent: () => import('@apps/vue2CommentsComponent'),
    },
    props: {
        slaLoading: {
            type: Boolean,
            default: false
        },
        showChat: {
            type: Boolean,
            default: false
        },
        getSLA: {
            type: Function,
            default: () => {}
        },
        ticket: {
            type: Object,
            required: true
        },
        callLoading: {
            type: Boolean,
            default: false
        },
        startTicketCall: {
            type: Function,
            default: () => {}
        },
        takeItem: {
            type: Function,
            default: () => {}
        },
        edit: {
            type: Boolean,
            default: false
        },
        canEdit: {
            type: Boolean,
            default: false
        },
        listPageName: {
            type: String,
            required: true
        },
        listModel: {
            type: String,
            required: true
        },
        actions: {
            type: Object,
            default: () => null
        },
        getTicket: {
            type: Function,
            default: () => {}
        },
        actionsTakeDelete: {
            type: Function,
            default: () => {}
        },
        tab: {
            type: String,
            default: "info"
        },
        getActions: {
            type: Function,
            default: () => {}
        },
        forceReload: {
            type: Function,
            default: () => {}
        },
        ticketType: {
            type: String,
            default: "issue"
        },
        slaInfo: {
            type: Object,
            default: () => null
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        isClientView() {
            const q = this.$route?.query || {}
            if (q.ticketView) return false
            if (q.requestView) return true
            return false
        },
        ...mapState({
            user: state => state.user.user
        }),
        slaComponent() {
            if(this.slaInfo)
                return () => import('../../ModalFormSLA.vue')
            return null
        },
        sources() {
            if (this.slaInfo){
                return this.slaInfo.sources?.length ? this.slaInfo.sources : []
            }
            return []
        },
        currentSla() {
            return this.slaInfo.sla
        },
        canStartTimer() {
            return this.actions?.can_use_timer?.availability
        },
        stopTimerModalTitle() {
            const titles = {
                'on_pause': this.$t('helpdesk.on_pause'),
                'completed': this.$t('helpdesk.complete'),
                'rejected': this.$t('helpdesk.reject'),
            }
            return titles[this.stopTimerReasonStatus] || this.$t('helpdesk.stop_timer')
        },
        showStartButton() {
            if (['new', 'on_pause', 'on_rework', 'in_work'].includes(this.ticket.status.code)) {
                return this.availableStatuses.some(status => status.code === 'in_work')
            }
            return false
        },
        showExecutionButton() {
            if (this.ticket.status.code !== 'in_work') { return }
            return this.availableStatuses.some(status => status.code === 'on_pause')
        },
        showFinishButton() {
            return this.availableStatuses.some(status => status.code === 'completed')
        },
        canChangeStatus() {
            return this.actions?.change_status?.availability && this.availableStatuses.length
        },
        canTakeTicketInInfo() {
            return this.isMobile && Boolean(this.actions?.take)
        },
        canStartTicketCallInInfo() {
            return this.isMobile && Boolean(this.ticket?.id)
        },
        canEditCategory() {
            return this.actions?.edit?.availability
        },
        showRejectbutton() {
            const rejectButtonCode = 'rejected'
            if (this.ticket.status.code === rejectButtonCode) { return }
            if (this.canChangeStatus) {
                return this.availableStatuses.some(status => status.code === rejectButtonCode)
            }
            return false
        },
        availableStatuses() {
            return this.actions?.change_status?.available_statuses || []
        },
        curPriority() {
            if(this.ticket.priority) {
                const find = this.priorityList.find(f => Number(f.value) === Number(this.ticket.priority.code))
                if(find) {
                    return find
                }
            }
            return null
        },
        formattedTimer() {
            if (this.timerStop) {
                const total = Math.max(0, this.stoppedValue)
                const h = Math.floor(total / 3600)
                const m = Math.floor((total % 3600) / 60)
                const s = Math.floor(total % 60)
                const pad = n => String(n).padStart(2, '0')
                return (h > 0 ? `${pad(h)}:` : '') + `${pad(m)}:${pad(s)}`
            }
            const total = Math.max(0, this.elapsedSeconds)
            const h = Math.floor(total / 3600)
            const m = Math.floor((total % 3600) / 60)
            const s = Math.floor(total % 60)
            const pad = n => String(n).padStart(2, '0')
            return (h > 0 ? `${pad(h)}:` : '') + `${pad(m)}:${pad(s)}`
        },
        accountingPageName() {
            return `work_log_${this.ticket?.id || 'new'}`
        },
        ckEditor() {
            return () => import("@apps/CKEditor");
        },
        userSelectApi() {
            if (!this.currentCustomerCardId) return ''
            if(this.ticketType === 'lead')
                return `/contractor_permissions/app_sections/help_desk/members/?contractor=${this.currentOrgAdminId}`
            else
                return `/help_desk/customer_cards/${this.currentCustomerCardId}/specialists/actual/?display=user`
        },
        currentCustomerCardId() {
            return this.form.customer_card || this.ticket?.customer_card?.id || null
        },
        currentOrgAdminId() {
            return this.orgAdminClient || this.ticket?.customer_card?.org_admin?.id || null
        },
        contactPersonEndpoint() {
            if (!this.form.customer_card) return ''
            return `help_desk/customer_cards/${this.form.customer_card}/contact_persons/`
        },
        contractSelectApiUrl() {
            return '/customer_contracts/analytics_keys/'
        },
        contractSelectParams() {
            if (!this.form.customer_card) return {}
            return {
                customer_card: this.form.customer_card
            }
        },
        isInternalChatChannel() {
            const channelCode = this.ticket?.channel?.code
            return channelCode === 'internal_chat' || channelCode === 'internal'
        },
        initialCustomerCardId() {
            return this.ticket?.customer_card?.id || null
        },
        initialContactPersonId() {
            return this.ticket?.contact_person?.id || null
        },
        initialAnalyticsKeyId() {
            return this.ticket?.analytics_key?.id || null
        },
        currentAnalyticsKeyId() {
            if (!this.form.analytics_key) return null
            return typeof this.form.analytics_key === 'object'
                ? this.form.analytics_key.id || null
                : this.form.analytics_key
        },
        hasInternalChatCustomerContactChanges() {
            if (!this.edit || !this.isInternalChatChannel) return false

            return (
                (this.form.customer_card || null) !== this.initialCustomerCardId ||
                (this.form.contact_person || null) !== this.initialContactPersonId ||
                this.currentAnalyticsKeyId !== this.initialAnalyticsKeyId
            )
        },
        showInternalChatCustomerSave() {
            return this.hasInternalChatCustomerContactChanges
        },

        layoutMode() {
            return this.isMobile ? 1 : this.layout
        },
        info2Xl() {
            return 7
        },
        chat2Xl() {
            return this.showChat ? 6 : 2
        },
        desc2Xl() {
            return 24 - this.info2Xl - this.chat2Xl
        },
        desc3Xl() {
            return 16
        },
        sidebar3Xl() {
            return 8
        },
        meetingStatus() {
            if (this.ticket.meeting)
                return () => import('@apps/vue2MeetingComponent/components/Status.vue')
            return null
        },
        filteredVisors() {
            return Array.isArray(this.ticket?.visors) ? this.ticket.visors.filter(Boolean) : []
        },
        meetingInviteUsers() {
            const list = []
            const pushUser = user => {
                if (user && user.id) {
                    list.push(user)
                }
            }

            pushUser(this.ticket?.contact_person?.user)
            pushUser(this.ticket?.specialist)
            const visors = Array.isArray(this.ticket?.visors) ? this.ticket.visors : []
            visors.forEach(visor => {
                pushUser(visor?.user || visor)
            })

            const uniq = new Map()
            list.forEach(user => {
                const key = String(user.id)
                if (!uniq.has(key)) {
                    uniq.set(key, user)
                }
            })

            const authorId = this.ticket?.author?.id
            const currentUserId = this.user?.id

            return Array.from(uniq.values()).filter(user =>
                String(user.id) !== String(authorId) &&
                String(user.id) !== String(currentUserId)
            )
        },
        showContactPersonNotRegisteredAlert() {
            return Boolean(this.ticket?.contact_person) && !this.ticket.contact_person.user
        },
        showRelatedChat() {
            const channelCode = this.ticket?.channel?.code
            const isInternalChat = channelCode === 'internal_chat' || channelCode === 'internal'
            return Boolean(isInternalChat && this.ticket?.related_chat?.name && (this.ticket?.related_chat?.chat_uid || this.ticket?.related_chat?.id))
        },
        showMembersBlock() {
            if (this.isClientView) return false
            if (this.canEdit) return true
            return this.ticketMembersList.length > 0
        },
        ticketMembersList() {
            return Array.isArray(this.ticket?.members)
                ? this.ticket.members
                    .map(member => member?.user || member)
                    .filter(member => member?.id)
                : []
        }
    },
    watch: {
        // ✅ FIX: после take/ приходит новый ticket -> пересобираем form
        'ticket.id': {
            immediate: true,
            handler(newVal, oldVal) {
                if (!newVal) return
                if (!oldVal || newVal !== oldVal) {
                    this.initEdit()
                }
            }
        },

        // ✅ FIX: если specialist поменялся (после take) — синхроним form.specialist
        'ticket.specialist': {
            immediate: true,
            handler(val) {
                this.form.specialist = val || null
            }
        },

        tab(val) {
            if(val === 'info') {
                this.$nextTick(() => {
                    if(this.$refs?.chatList)
                        this.$refs.chatList.scrollToBottom()
                })
            }
        },
        'ticket.status.code'() {
            if (!this.ticket?.status?.code) { return }
            this.getTimer()
        },
        'ticket.started_timer'() {
            if (this.ticket?.status?.code !== 'in_work') { return }
            this.getTimer()
        },
        edit(val) {
            if (val) {
                this.initEdit()
                return
            }
            clearTimeout(timer)
            this.pendingPatch = null
        }
    },
    data() {
        return {
            initListCategory: [],
            initListClient: [],
            initListContactPerson: [],
            clientUUID: null,
            contactUUID: null,
            personKey: Date.now(),
            contractSelectKey: Date.now(),
            fullPerson: null,
            orgAdminClient: null,
            getClientLoading: false,
            customerContactSaving: false,

            accountingModel: 'help_desk.HelpDeskTicketWorkLogModel',
            durationLoading: true,
            duration: 0,
            accountingDate: null,
            editorGate: false,
            elapsedSeconds: 0,
            runTimerId: null,
            statusLoader: false,
            showAside: true,
            spamPageName: 'list_help_desk.SpamContactPersonModel',
            spamPageModel: 'help_desk.ContactPersonModel',
            execution_result: "",
            rejectReasonText: "",
            description: "",
            customDuration: {
                hours: 0,
                minutes: 0,
                seconds: 0
            },

            layout: 3,

            form: {
                metadata: {
                    visors: []
                },
                receipt_date: null,
                author: null,
                visors: [],
                category: null,
                customer_card: null,
                contact_person: null,
                analytics_key: null,
                name: "",
                description: "",
                priority: null,
                dead_line: null,
                specialist: null
            },
            rules: {

            },
            expanded: 'comments',
            stoppedValue: 0,
            spamLoading: false,
            finishModalVisible: false,
            getIncompleteDurationLoading: false,
            stopTimerReasonStatus: null,
            lastSessionDuration: 0,
            totalDuration: 0,
            timerStop: false,
            isCurrentWorkLog: false,
            meetingLoading: false,
            inviteModalVisible: false,
            pendingPatch: null,
            membersLoading: false,
            memberRemovingId: null
        }
    },
    created() {
        this.getTimer()
        this.initEdit()
    },
    beforeDestroy() {
        this.stopLocalTimer()
    },
    methods: {
        // ✅ для комментариев — чтобы модалки/поповеры жили внутри drawer
        getCommentsContainer() {
            const ref = this.$refs.ticketBodyWrap
            return ref?.$el || ref || this.$el
        },
        async updateMembers(newIds) {
            if (!this.ticket?.id) return
            if (!Array.isArray(newIds)) return
            if (this.membersLoading) return

            const oldIds = this.ticketMembersList.map(member => member.id)
            const same = newIds.length === oldIds.length && newIds.every(id => oldIds.includes(id))

            if (same) return

            try {
                this.membersLoading = true
                const { data } = await this.$http.patch(`/help_desk/tickets/${this.ticket.id}/`, {
                    members: newIds,
                    metadata: this.form.metadata
                })

                if (data) {
                    this.$set(this.ticket, 'members', Array.isArray(data.members) ? data.members : this.ticket.members)
                    this.listReload()

                    const kanbanObj = { ...data }
                    if (kanbanObj.sla?.sla)
                        kanbanObj.sla = kanbanObj.sla.sla
                    eventBus.$emit('UPDATE_TICKET_KANBAN', kanbanObj)
                    if (this.$store.hasModule('workplan')) {
                        this.$store.dispatch('workplan/updateItem', {
                            item: { id: this.ticket.id },
                            list: 'ticketList'
                        })
                    }
                }
            } catch (error) {
                errorHandler({ error })
            } finally {
                this.membersLoading = false
                this.memberRemovingId = null
            }
        },
        async removeMember(memberId) {
            if (!this.canEdit) return
            if (!memberId) return
            if (this.membersLoading) return

            const currentIds = this.ticketMembersList.map(member => member.id)
            const newIds = currentIds.filter(id => id !== memberId)
            if (newIds.length === currentIds.length) return

            this.memberRemovingId = memberId
            await this.updateMembers(newIds)
        },

        afterVisibleChange(vis) {
            if(vis) {
                requestAnimationFrame(() => {
                    this.$nextTick(() => {
                        if(this.$refs.execution_result)
                            this.$refs.execution_result.focus()
                    })
                })
            } else {
                this.timerStop = false
                this.execution_result = ""
                this.description = ""
            }
        },

        initEdit() {
            if(this.canEditCategory) {
                if (this.ticket.category){
                    this.initListCategory = [{
                        ...this.ticket.category,
                        string_view: this.ticket.category.name
                    }]
                    this.form.category = this.ticket.category.id
                }
            }
            if(this.edit) {
                const ticketForm = {...this.ticket}

                if(ticketForm.category) {
                    this.initListCategory = [{
                        ...ticketForm.category,
                        string_view: ticketForm.category.name
                    }]
                    ticketForm.category = ticketForm.category.id
                }

                if(ticketForm.customer_card)
                    this.initListClient = [{
                        id: ticketForm.customer_card.id,
                        string_view: ticketForm.customer_card.name
                    }]
                if(ticketForm.customer_card?.org_admin?.id)
                    this.orgAdminClient = ticketForm.customer_card.org_admin.id

                if(ticketForm.customer_card)
                    ticketForm.customer_card = ticketForm.customer_card.id

                if (ticketForm.analytics_key)
                    ticketForm.analytics_key = { ...ticketForm.analytics_key }

                if(ticketForm.contact_person) {
                    this.initListContactPerson = [{
                        id: ticketForm.contact_person.id,
                        name: ticketForm.contact_person.name
                    }]
                    this.fullPerson = ticketForm.contact_person
                    ticketForm.contact_person = ticketForm.contact_person.id
                }

                if(ticketForm.priority)
                    ticketForm.priority = Number(ticketForm.priority.code)
                if(ticketForm.dead_line)
                    ticketForm.dead_line = this.$moment(ticketForm.dead_line)
                if(ticketForm.receipt_date)
                    ticketForm.receipt_date = this.$moment(ticketForm.receipt_date)

                // ✅ FIX: важно не потерять specialist после take
                ticketForm.specialist = this.ticket.specialist || null

                this.form = ticketForm

                if(this.$route.query?.in_complete) {
                    const query = JSON.parse(JSON.stringify(this.$route.query))
                    delete query.in_complete
                    this.$router.replace({query})
                    this.actionsOpenFinishModal({ status: 'completed' })
                }
            }
        },

        closeFinishModal() {
            this.finishModalVisible = false
        },
        stopTimerWithTime() {
            this.changeStatus(this.stopTimerReasonStatus, true)
        },
        stopTimerWithoutTime() {
            this.changeStatus(this.stopTimerReasonStatus, true)
        },
        finishModalAfterClose() {
            this.customDuration = {
                hours: 0,
                minutes: 0,
                seconds: 0
            }
            this.accountingDate = null
            this.execution_result = ""
            this.description = ""
            this.lastSessionDuration = 0
            this.totalDuration = 0
        },
        secondsToHMS(total) {
            const t = Number(total || 0)
            const hours = Math.floor(t / 3600)
            const minutes = Math.floor((t % 3600) / 60)
            const seconds = t % 60
            return {
                hours,
                minutes,
                seconds,
            }
        },
        HMSToSeconds(HMS) {
            const { hours, minutes, seconds } = HMS
            return (hours * 3600) + (minutes * 60) + seconds
        },
        actionsOpenFinishModal({ status=null }){
            eventBus.$emit('ticket_open_finish_modal', {status:status})
        },
        isSVG(icon) {
            return icon.endsWith('.svg')
        },
        openCreateClientModal() {
            this.$refs.clientClientModalRef.openModal(this.ticket.contact_person)
        },
        maskAsSpam(contactPerson) {
            this.spamLoading = true
            this.$http.post(`help_desk/contact_persons/${contactPerson.id}/mark_as_spam/`)
                .then(({ data }) => {
                    if(data) {
                        this.$message.success(this.$t('helpdesk.contact_marked_spam'))
                        eventBus.$emit('ticket_drawer_close')
                    }
                })
                .catch((error) => {
                    errorHandler({error})
                })
                .finally(() => {
                    this.spamLoading = false
                })
        },
        allVisorClear() {
            this.form.metadata.visors = []
            this.form.visors = []
            this.patchField([], 'visors')
        },
        changeMetadata({ key, value }) {
            this.$set(this.form.metadata, key, value);
        },
        selectClient(client) {
            this.initListClient = [{ id: client.id, string_view: client.name }]
            this.handleCustomerCardChange(client.id)
        },
        selectClientId(clientId) {
            this.handleSelectClient(clientId)
        },
        async handleSelectClient(clientId) {
            if (!clientId) return

            this.getClientLoading = true
            try {
                const { data } = await this.$http.get(`help_desk/customer_cards/${clientId}/`)
                this.orgAdminClient = data?.org_admin?.id || null
            } catch (error) {
                errorHandler({ error, show: false })
            } finally {
                this.getClientLoading = false
            }
        },
        async handleCustomerCardChange(clientId) {
            this.form.customer_card = clientId || null
            this.form.analytics_key = null
            this.form.contact_person = null
            this.fullPerson = null
            this.initListContactPerson = []
            this.personKey = Date.now()
            this.contractSelectKey = Date.now()

            await this.handleSelectClient(this.form.customer_card)
            if (this.edit && this.isInternalChatChannel) {
                this.getSLA()
                return
            }

            await this.patchField(this.form.customer_card, 'customer_card')
            await this.patchField(null, 'analytics_key')
            await this.patchField(null, 'contact_person')
            this.getSLA()
        },
        handleAnalyticsKeyChange(value) {
            this.form.analytics_key = value || null
            if (this.edit && this.isInternalChatChannel) {
                return
            }

            this.dataChange({ field: 'analytics_key', valueKey: 'id' })
        },
        selectContactPerson(item) {
            this.changeFullPerson(item)
            this.initListContactPerson = [{ id: item.id, name: item.name }]
            this.handleContactPersonChange(item.id)
        },
        handleContactPersonChange(value) {
            this.form.contact_person = value || null
            if (this.edit && this.isInternalChatChannel) {
                this.getSLA()
                return
            }

            this.dataChange({ field: 'contact_person' })
            this.getSLA()
        },
        changeFullPerson(data) {
            this.fullPerson = data
        },
        addClient() {
            eventBus.$emit("helpdesc_add_client", true, { slaSelect: true })
        },
        addContact() {
            eventBus.$emit("add_ticket_contact", this.form.customer_card)
        },
        editContact() {
            eventBus.$emit("edit_contact_person_modal", {
                client: { id: this.form.customer_card },
                contactPerson: this.fullPerson,
            })
        },
        async openAllClients() {
            let customer_card_data
            try {
                if (this.form.customer_card) {
                    customer_card_data = await this.$http.get(
                        `help_desk/customer_cards/${this.form.customer_card}/customer_card_detail/?page_name=helpdesk_clients_all`
                    )
                }
            } catch (e) {
                console.log(e)
            }

            await this.$refs.listViewModalClientsRef?.open?.()

            if (this.form.customer_card) {
                this.$nextTick(() => {
                    if (this.$refs.listViewModalClientsRef?.$refs?.refListView?.$refs?.tableRef && customer_card_data) {
                        this.$refs.listViewModalClientsRef.$refs.refListView.$refs.tableRef.selectedRows = [
                            customer_card_data.data,
                        ]
                    }
                })
            }
        },
        async openAllConctactPersons() {
            let contact_person_data
            try {
                if (this.form.contact_person) {
                    contact_person_data = await this.$http.get(`help_desk/contact_persons/${this.form.contact_person}/`)
                }
            } catch (e) {
                console.log(e)
            }

            this.$refs.listViewModalConctactPersonRef?.open?.()

            if (this.form.contact_person) {
                this.$nextTick(() => {
                    if (
                        this.$refs.listViewModalConctactPersonRef?.$refs?.refListView?.$refs?.tableRef &&
                        contact_person_data
                    ) {
                        this.$refs.listViewModalConctactPersonRef.$refs.refListView.$refs.tableRef.selectedRows = [
                            contact_person_data.data,
                        ]
                    }
                })
            }
        },
        onTextareaKeydown(e, status='completed') {
            if (e.key === 'Enter' && e.shiftKey) {
                e.preventDefault()
                this.changeStatus(status, true)
            }
        },
        resultVisibleChange(vis) {
            this.$nextTick(() => {
                if(vis && this.$refs?.execution_result) {
                    this.$refs.execution_result.focus()
                }
            })
        },
        async saveEdit() {
            if (this.$refs?.completedBanner?.isEditing) {
                await this.$refs.completedBanner.saveExecutionResult({
                    silent: true,
                    reload: false
                })
            }

            if (this.hasInternalChatCustomerContactChanges) {
                return await this.saveInternalChatCustomerContact()
            }

            if (!this.pendingPatch) return
            const { field, value } = this.pendingPatch
            clearTimeout(timer)
            this.pendingPatch = null
            await this.patchField(value, field)
            return true
        },
        async saveInternalChatCustomerContact() {
            if (!this.showInternalChatCustomerSave || this.customerContactSaving) return true

            if (!this.form.customer_card) {
                this.$message.warning(`${this.$t('table.contractor_member')}: ${this.$t('helpdesk.required_field')}`)
                return false
            }

            if (!this.form.contact_person) {
                this.$message.warning(`${this.$t('helpdesk.contact_person')}: ${this.$t('helpdesk.required_field')}`)
                return false
            }

            try {
                this.customerContactSaving = true
                const payload = {
                    customer_card: this.form.customer_card,
                    contact_person: this.form.contact_person,
                    analytics_key: this.currentAnalyticsKeyId,
                    metadata: this.form.metadata
                }
                const { data } = await this.$http.patch(`/help_desk/tickets/${this.ticket.id}/`, payload)

                if (data) {
                    this.$set(this.ticket, 'customer_card', data.customer_card || null)
                    this.$set(this.ticket, 'contact_person', data.contact_person || null)
                    this.$set(this.ticket, 'contact_person_user', data.contact_person_user || null)
                    this.$set(this.ticket, 'analytics_key', data.analytics_key || null)
                    if (data.org_admin) {
                        this.$set(this.ticket, 'org_admin', data.org_admin)
                    }

                    if (data.customer_card) {
                        this.initListClient = [{
                            id: data.customer_card.id,
                            string_view: data.customer_card.name
                        }]
                        this.orgAdminClient = data.customer_card?.org_admin?.id || this.orgAdminClient
                    }

                    if (data.contact_person) {
                        this.initListContactPerson = [{
                            id: data.contact_person.id,
                            name: data.contact_person.name
                        }]
                        this.fullPerson = data.contact_person
                    } else {
                        this.fullPerson = null
                    }

                    this.listReload()
                    this.getSLA()

                    const kanbanObj = { ...data }
                    if (kanbanObj.sla?.sla)
                        kanbanObj.sla = kanbanObj.sla.sla
                    eventBus.$emit('UPDATE_TICKET_KANBAN', kanbanObj)
                    if (this.$store.hasModule('workplan')) {
                        this.$store.dispatch('workplan/updateItem', {
                            item: { id: this.ticket.id },
                            list: 'ticketList'
                        })
                    }
                }

                return true
            } catch (error) {
                errorHandler({ error })
                return false
            } finally {
                this.customerContactSaving = false
            }
        },
        updateTimer() {
            this.getTimer()
            this.$nextTick(() => {
                if(this.$refs?.completedBanner)
                    this.$refs.completedBanner.getTimer()
            })
        },
        changeShowAside(value) {
            this.showAside = value
        },
        startLocalTimer() {
            if (!this.isCurrentWorkLog) {
                this.stopLocalTimer()
                return
            }
            this.stopLocalTimer()
            this.runTimerId = setInterval(() => {
                this.elapsedSeconds += 1
            }, 1000)
        },
        stopLocalTimer() {
            if (this.runTimerId) {
                clearInterval(this.runTimerId)
                this.runTimerId = null
            }
        },
        async getTimer() {
            if(this.ticket.status.code === 'in_work') {
                try {
                    const { data } = await this.$http.get(`/help_desk/tickets/${this.ticket.id}/work_log/duration/`)
                    if(data) {
                        const duration = Number(data.duration || 0)
                        const incompleteDuration = Number(data.duration_incomplete ?? data.incomplete_duration ?? 0)
                        const isCurrent = Boolean(data.is_current)

                        this.duration = duration
                        this.elapsedSeconds = isCurrent
                            ? Math.max(0, Math.floor(incompleteDuration))
                            : 0
                        this.lastSessionDuration = Math.max(0, Math.floor(incompleteDuration))
                        this.isCurrentWorkLog = isCurrent

                        if (isCurrent) this.startLocalTimer()
                        else this.stopLocalTimer()
                    } else {
                        this.isCurrentWorkLog = false
                        this.stopLocalTimer()
                    }
                } catch(error) {
                    this.isCurrentWorkLog = false
                    this.stopLocalTimer()
                    errorHandler({error, show: false})
                } finally {
                    this.durationLoading = false
                }
            } else {
                this.isCurrentWorkLog = false
                this.elapsedSeconds = 0
                this.stopLocalTimer()
                this.durationLoading = false
            }
        },
        async changeStatus(status, useText = false) {
            try {
                this.statusLoader = true
                const queryData = {
                    status
                }
                if (useText) {
                    queryData.execution_result = this.execution_result
                }

                const { data } = await this.$http.put(`/help_desk/tickets/${this.ticket.id}/status/`, queryData)
                if(data) {
                    await this.getTicket()
                    if (this.$store.hasModule('workplan')) {
                        this.$store.dispatch('workplan/updateItem', {
                            item: { id: this.ticket.id },
                            list: 'ticketList'
                        })
                    }
                    eventBus.$emit(`update_filter_${this.accountingModel}_${this.accountingPageName}`)
                    this.listReload()
                    this.execution_result = ""
                    this.rejectReasonText = ''
                    eventBus.$emit('STATUS_TICKET_KANBAN', {
                        task: data,
                        status
                    })
                    this.closeFinishModal()
                }

                this.getActions({ ticketView: this.ticket.id })
            } catch(error) {
                errorHandler({error})
            } finally {
                this.statusLoader = false
            }
        },
        listReload() {
            clearTimeout(reloadTimer)
            reloadTimer = setTimeout(() => {
                eventBus.$emit(`update_filter_${this.spamPageModel}_${this.spamPageName}`)
                eventBus.$emit(`update_filter_${this.listModel}_${this.listPageName}`)
            }, 1000)
        },
        checkField({key, type = 'object'}) {
            if(this.edit)
                return true
            else {
                if(type === 'array') {
                    if(this.ticket[key]?.length)
                        return true
                } else {
                    if(this.ticket[key])
                        return true
                }
            }
            return false
        },
        dataChange({field, useTimer = false, valueKey = false, multiple = false}) {
            let value = this.form[field]
            if(valueKey) {
                if(multiple) {
                    value = this.form[field].map(fld => fld[valueKey])
                } else {
                    value = this.form[field][valueKey]
                }
            }
            if(useTimer) {
                clearTimeout(timer)
                this.pendingPatch = { field, value }
                timer = setTimeout(() => {
                    this.patchField(value, field)
                    this.pendingPatch = null
                }, 600)
            } else {
                this.pendingPatch = null
                this.patchField(value, field)
            }
        },
        async patchField(value, field) {
            try {
                if(field === 'name' && !value) {
                    this.$message.warning(this.$t('helpdesk.name_required_warning'))
                    return false
                }
                const { data } = await this.$http.patch(`/help_desk/tickets/${this.ticket.id}/`, {
                    [field]: value,
                    metadata: this.form.metadata
                })
                if(data) {
                    if(field === 'specialist')
                        this.actionsTakeDelete()
                    this.listReload()
                    if(field === 'category')
                        this.getSLA()

                    if(field === 'contact_person')
                        this.getSLA()

                    if(field === 'specialist')
                        this.getActions(this.$route.query)

                    const kanbanObj = {...data}
                    if(kanbanObj.sla?.sla)
                        kanbanObj.sla = kanbanObj.sla.sla
                    eventBus.$emit('UPDATE_TICKET_KANBAN', kanbanObj)
                    if (this.$store.hasModule('workplan')) {
                        this.$store.dispatch('workplan/updateItem', {
                            item: { id: this.ticket.id },
                            list: 'ticketList'
                        })
                    }
                }
            } catch(error) {
                if(error?.non_field_errors?.length) {
                    if(error.non_field_errors[0].includes("не является ответственным")) {
                        this.forceReload(false)
                    }
                }
                errorHandler({error})
            }
        },
        getCalendarContainer(trigger) {
            return trigger.parentNode
        },
        openRelatedChat() {
            const chatUid = this.ticket?.related_chat?.chat_uid || this.ticket?.related_chat?.id
            if (!chatUid) return
            this.$router.push({
                name: 'chat',
                query: { chat_id: chatUid }
            })
        },
        openClient() {
            const query = JSON.parse(JSON.stringify(this.$route.query))
            if(!query.client) {
                query.client = this.ticket.customer_card.id
                this.$router.replace({query})
            } else {
                eventBus.$emit('close_client_drawer')
                setTimeout(() => {
                    query.client = this.ticket.customer_card.id
                    this.$router.replace({query})
                }, 500)
            }
        },
        openMeetingInviteModal() {
            if (this.ticket?.meeting?.status === 'online') {
                this.joinMeeting()
                return
            }

            if (!this.meetingInviteUsers.length) {
                this.startMeetingWithNotifyUsers()
                return
            }

            this.inviteModalVisible = true
        },
        joinMeeting() {
            if (this.ticket?.meeting?.url) {
                window.open(this.ticket.meeting.url, '_blank', 'noopener,noreferrer')
            }
        },
        async inviteAndStartMeeting(notifyUserIds = []) {
            this.inviteModalVisible = false
            await this.startMeetingWithNotifyUsers(notifyUserIds)
        },
        async startMeetingWithNotifyUsers(notifyUserIds = []) {
            try {
                this.meetingLoading = true
                const payload = {
                    notify_user_ids: notifyUserIds
                }

                const { data } = await this.$http.post(`meetings/start-related/?related_object=${this.ticket.id}`, payload)

                if (data) {
                    this.$set(this.ticket, 'meeting', data)
                }

                if (data?.url) {
                    window.open(data.url, '_blank', 'noopener,noreferrer')
                }
            } catch(error) {
                errorHandler({error})
            } finally {
                this.meetingLoading = false
            }
        },
        openMeeting() {
            const query = JSON.parse(JSON.stringify(this.$route.query))
            if (!query?.meeting && this.ticket?.meeting?.id) {
                query.meeting = this.ticket.meeting.id
                this.$router.push({query})
            }
        },
        copyMeeting() {
            navigator.clipboard.writeText(this.ticket.meeting.url_external)
                .then(() => {
                    this.$message.success(this.$t('link_succes_copy'))
                })
                .catch(error => {
                    console.error(error)
                    this.$message.error(this.$t('copy_link_error'))
                })
        }
    }
}
</script>
<style lang="scss">
.ticket_drawer{
    .ck-editor__top{
        background: white !important;
    }
}
</style>
<style lang="scss" scoped>
.ticket-slide-down-fade-enter-active,
.ticket-slide-down-fade-leave-active {
    transition: all 0.25s ease;
}
.ticket-slide-down-fade-enter,
.ticket-slide-down-fade-leave-to {
    transform: translateY(-10px);
    opacity: 0;
}
.task_info_collapse {
    margin-left: -15px;
    margin-right: -15px;
    ::v-deep {
        .ant-collapse-header {
            font-weight: 500;
        }
        .ant-collapse-borderless{
            background: #F8F9FD;
        }
    }

}
.badge-fade-slide-enter-active, .badge-fade-slide-leave-active {
    transition: all 0.3s ease
}
.badge-fade-slide-enter, .badge-fade-slide-leave-to {
    transform: translateX(-8px);
    opacity: 0
}
.description_editor{
    &::v-deep{
        .ck-editor__top{
            position: sticky !important;
            top: 0px !important;
            z-index: 999999;
        }
        .ck{
            &.ck-toolbar__items{
                margin-right: 0px!important;
            }
            &.ck-toolbar__separator{
                opacity: 0;
                margin-right: 0px!important;
            }
            &.ck-toolbar{
                border: 0px;
                padding-left: 0px!important;
                padding-right: 0px!important;
                margin-left: -7px;
            }
            &.ck-content{
                border: 0px!important;
                box-shadow: none!important;
                padding-left: 0px!important;
                padding-right: 0px!important;
                background: transparent!important;
            }
        }
    }
}
.execution_result{
    min-width: 0;
    width: 100%;
    max-width: 100%;
}
.channel_icon{
    max-width: 16px;
}
.related-chat-link {
    color: #1677ff;
    cursor: pointer;
    text-decoration: underline;
}
.priority_icon{
    position: relative;
    overflow: hidden;
    width: 28px;
    height: 28px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    &__bg{
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        opacity: 0.1;
    }
    i{
        position: relative;
        z-index: 5;
    }
}
.change-status-header {
    &:not(:empty) {
        border-bottom: 1px solid #DADADA;
        margin-bottom: 16px;
        padding-bottom: 16px;
    }
}

::v-deep {
    .ant-modal .ant-modal-header {
        padding-top: 24px;
    }
    .ant-modal .ant-modal-body {
        padding-top: 0;
        padding-bottom: 24px;
    }
}

.aside-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(180px, 1fr));
    gap: 5px;
    align-items: flex-start;
}

/* layout 2/3: info-block becomes vertical (one column grid) */
.ticket_drawer.layout-2 .aside-grid,
.ticket_drawer.layout-3 .aside-grid {
    grid-template-columns: 1fr;
}

/* fix: keep sidebar content within bounds */
.right-sidebar{
    min-width: 0;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.right-sidebar .info-block{
    flex: 1;
    max-width: 100%;
    overflow-wrap: anywhere;
    word-break: break-word;
}

.right-sidebar .aside-grid,
.right-sidebar .aside-grid > *{
    min-width: 0;
}

.meeting_section__label{
    opacity: 0.6;
}

.meeting_list_item {
    margin-bottom: 12px;
}

/* =========================
   TEXT OVERFLOW FIXES
   ========================= */

/* 1) Universal: long strings won't push layout */
.ticket_drawer,
.ticket_drawer *{
    max-width: 100%;
}

/* 2) If you want in ONE line with ellipsis */
.truncate-text{
    display: block;
    min-width: 0;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* 3) For flex rows: allow shrink + ellipsis */
.row-inline{
    display: flex;
    align-items: center;
    justify-content: space-between;
    min-width: 0;
}
.row-inline > *{
    min-width: 0;
}

/* 4) If you want wrap (instead of ellipsis) for long words/urls */
.wrap-anywhere{
    overflow-wrap: anywhere;
    word-break: break-word;
}

/* 5) clamp for 2 lines (nice on mobile for long descriptions) */
.clamp-2{
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

/* =========================
   MOBILE (layout-1) tweaks
   ========================= */
@media (max-width: 768px) {
    .ticket_drawer.layout-1 .aside-grid {
        grid-template-columns: 1fr;
        gap: 0px;
    }

    .right-sidebar .mini_form {
        padding-bottom: 0 !important;
    }

    .channel_icon {
        max-width: 18px;
    }

    .right-sidebar,
    .right-sidebar .info-block,
    .description-block {
        min-width: 0;
        max-width: 100%;
        margin: 0px !important;
    }

    /* ✅ comments bottom spacing */
    .comments-mobile{
        padding-right: 0;
    }
}
@media (max-width: 768px) {
    .drawer_aside{
        background: transparent !important;
        padding: 0px !important;
    }
}
</style>
