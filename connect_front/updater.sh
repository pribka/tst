#!/bin/bash
ROOT_UID=0
echo "Сливаем основной проект..."
git pull origin master &
wait
cd ./src/modules
echo "Удаляем папки..."
rm -r -f Deals Planner RequestApprovals AccountingReports Directories BusinessProcesses Inquiries GeoViewer Calendar CKEditor Consolidation Dashboard Datepicker Documents DrawerSelect FinancialReports Gallery Groups History InvestProject LogisticMonitor Moderation MyBases Notifications Orders Products Profiler Projects SportsFacilities Support Team UIModules Upload vue2ChatComponent vue2CommentsComponent vue2Files vue2MeetingComponent vue2TaskComponent WorkPlan Reports HelpDesk OKR GOS24 AIAssistant &
wait
echo "Клонируем репозитории..."
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/Deals.git
# git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/AccountingReports.git
# git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/BusinessProcesses.git
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/Planner.git
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/Directories.git
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/RequestApprovals.git
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/Calendar.git
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/CKEditor.git
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/Consolidation.git
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/Dashboard.git
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/Datepicker.git
# git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/Documents.git
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/DrawerSelect.git
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/HelpDesk.git
# git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/FinancialReports.git
# git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/Gallery.git
# git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/GeoViewer.git
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/Groups.git
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/History.git
# git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/Inquiries.git
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/InvestProject.git
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/LogisticMonitor.git
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/Moderation.git
# git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/MyBases.git
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/Notifications.git
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/Orders.git
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/Products.git
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/Profiler.git
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/Projects.git
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/SportsFacilities.git
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/Support.git
# git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/Team.git
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/UIModules.git
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/Upload.git
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/vue2ChatComponent.git
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/vue2CommentsComponent.git
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/vue2Files.git
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/vue2MeetingComponent.git
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/vue2TaskComponent.git
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/WorkPlan.git
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/Reports.git
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/OKR.git
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/GOS24.git
git clone https://gitlab+deploy-token-39:QXQbPsizBDhCzwK6kSiM@gitlab.buhni.kz/bkz/frontend/appcomponents/AIAssistant.git

#############
#git clone https://gitlab+deploy-token-1340290:uK_ooysvQgz46NzGbqU4@gitlab.com/b3889/startercomponents-vue2/CKEditor.git
#git clone https://gitlab+deploy-token-1340320:wbpyaGpe-auUAyFAUWU6@gitlab.com/b3889/startercomponents-vue2/Profiler.git
#git clone https://gitlab+deploy-token-1340323:_Co9brmhS98Esus9vfjW@gitlab.com/b3889/startercomponents-vue2/Upload.git
#git clone https://gitlab+deploy-token-1340405:XsMSfELzRfny1ZzXdW5s@gitlab.com/b3889/startercomponents-vue2/vue2TaskComponent.git
#git clone https://gitlab+deploy-token-1340328:zAks1CsBjP9ABz5b2Eix@gitlab.com/b3889/startercomponents-vue2/vue2ChatComponent.git
#git clone https://gitlab+deploy-token-1340332:Xhg3y3idzZ7zZXg-H2dD@gitlab.com/b3889/startercomponents-vue2/vue2CommentsComponent.git
#git clone https://gitlab+deploy-token-1340384:yLxWyfWdng3KGHwDDoNv@gitlab.com/b3889/startercomponents-vue2/vue2GroupsAndProjectsComponent.git
#git clone https://gitlab+deploy-token-1340404:oMAkwQHxzsXuRu3iXUsz@gitlab.com/b3889/startercomponents-vue2/vue2MeetingComponent.git
#git clone https://gitlab+deploy-token-1340298:Ro2MiWg9cdT4KSWXst3X@gitlab.com/b3889/startercomponents-vue2/Datepicker.git
#git clone https://gitlab+deploy-token-1340309:9QTJPB9VwxJgxhkQptp7@gitlab.com/b3889/startercomponents-vue2/Notifications
#git clone https://gitlab+deploy-token-1340296:DKsiQ2A6Ud8y81g3buVH@gitlab.com/b3889/startercomponents-vue2/Dashboard
#git clone https://gitlab+deploy-token-1340315:zHkmChPTuZ6PdmbrcGYC@gitlab.com/b3889/startercomponents-vue2/Products
#git clone https://gitlab+deploy-token-1340313:DevQcqn-NPSH3pP7WLuS@gitlab.com/b3889/startercomponents-vue2/Orders.git
#git clone https://gitlab+deploy-token-1340307:yuw3RGTccng75of-5sYU@gitlab.com/b3889/startercomponents-vue2/DrawerSelect.git
#git clone https://gitlab+deploy-token-1409580:Ksi2mxoWf2biMXgpGyJk@gitlab.com/b3889/startercomponents-vue2/LogisticMonitor.git
#git clone https://gitlab+deploy-token-1409578:RDz6q2GmbWsCWTCuLaCm@gitlab.com/b3889/startercomponents-vue2/vue2Files.git
#############

echo "Всё готово!"
