<template>
    <div class="filter_buttons">
        <a-button type="primary" size="large" class="filter_button">Сотрудники</a-button>
        <a-button type="default" size="large" class="filter_button" disabled>Клиенты</a-button>
        <a-button type="default" size="large" class="filter_button" disabled>Дилер</a-button>
        <a-button type="default" size="large" class="filter_button" disabled>Дистрибьютор</a-button>
        <a-button type="default" size="large" class="filter_button" disabled>Партнер</a-button>
        <a-button type="default" size="large" class="filter_button" disabled>Подрядчик</a-button>
    </div>
</template>


<style scoped lang="scss">

.filter_buttons {
  margin-left: -5px;
  margin-right: -5px;
  margin-bottom: -10px;
}

.filter_button {
  margin-left: 5px;
  margin-right: 5px;
  margin-bottom: 10px;
}
</style>