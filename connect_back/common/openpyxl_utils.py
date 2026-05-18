from math import ceil


factor_of_font_size_to_width = {
    8: {
        "factor": 0.6,
        "height": 14
    },
    12: {
        "factor": 0.8,  # width / count of symbols at row
        "height": 16
    },
    13: {
        "factor": 1.2,
        "height": 18,
    },
    14: {
        "factor": 1.6,
        "height": 20
    },
    16: {
        "factor": 2.4,
        "height": 24,
    }
}


def get_height_for_row(sheet, row_number, font_size=14):
    """
    Возвращает высоту строки в зависимости от размера содержимого ячеек строки.
    """
    font_params = factor_of_font_size_to_width[font_size]
    row = list(sheet.rows)[row_number]
    height = font_params["height"]

    for cell in row:
        words_count_at_one_row = sheet.column_dimensions[cell.column_letter].width / font_params["factor"]
        cell_value = cell.value
        if isinstance(cell_value, str):
            extra_cells = cell_value.split('\n')
            extra_cells_len = len(extra_cells)
            if extra_cells_len > 1:
                extra_lines = extra_cells_len
                for extra_cell in extra_cells:
                    extra_lines = extra_lines + ceil(len(extra_cell) / words_count_at_one_row) - 1
                height = max(height, extra_lines * font_params['height'])
                continue
        lines = ceil(len(str(cell_value)) / words_count_at_one_row)
        height = max(height, lines * font_params['height'])
    return height


def get_height_for_cell(sheet, cell, font_size=14):
    """
    Возвращает высоту строки в зависимости от размера содержимого по одной ячейки.
    Использовать, если есть заведомо самая большая ячейка по содержимому.
    """
    cell_value = cell.value
    font_params = factor_of_font_size_to_width[font_size]
    height = font_params["height"]
    words_count_at_one_row = sheet.column_dimensions[cell.column_letter].width / font_params["factor"]

    if isinstance(cell_value, str):
        extra_cells = cell_value.split('\n')
        extra_cells_len = len(extra_cells)
        if extra_cells_len > 1:
            extra_lines = extra_cells_len
            for extra_cell in extra_cells:
                extra_lines = extra_lines + ceil(len(extra_cell) / words_count_at_one_row) - 1
            height = max(height, extra_lines * font_params['height'])
    lines = ceil(len(str(cell_value)) / words_count_at_one_row)
    return max(height, lines * font_params['height'])
