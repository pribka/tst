# Action `select_list`

Эндпоинт для получения списка объектов с поддержкой поиска, фильтрации по id/code и пагинации.

## URL

```
POST /api/v1/reports/<model>/select_list/
GET  /api/v1/reports/<model>/select_list/
```

## Методы
- `GET`: стандартный select_list с поиском и пагинацией
- `POST`: поддерживает фильтрацию по списку id или code

## Параметры запроса

### POST
- `id` (list of str, optional): список UUID объектов для фильтрации. Если передан, фильтрация только по этим id.
- `code` (list of str, optional): список code объектов для фильтрации.
- `search` (str, optional): строка поиска (делегируется в get_filtered_select_queryset)

#### Примеры

##### Фильтрация по id
```json
POST /api/v1/reports/<model>/select_list/
{
  "id": ["00e9c7ac-3ce8-11ee-af9e-4216f3de51df", "01b090b0-2bba-11ee-9060-4216f3de51df"]
}
```

##### Фильтрация по code
```json
POST /api/v1/reports/<model>/select_list/
{
  "code": ["03e0ea10-6b78-11f0-b6a9-a1767f0851ef", "06177b88-9a72-11ee-bade-4216f3de51df"]
}
```

### GET
- `search` (str, optional): строка поиска
- стандартные параметры пагинации

## Ошибки
- Если `id` или `code` не список — 400 с сообщением об ошибке

## Примечания
- Для поиска используется логика get_select_queryset/get_filtered_select_queryset модели
- Если у модели есть поле `ct`, используется select_related('ct') 