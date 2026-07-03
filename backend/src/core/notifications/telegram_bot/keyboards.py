from __future__ import annotations


def confirm_keyboard(action: str, id: str) -> dict:
    return {
        "inline_keyboard": [
            [
                {
                    "text": "Sí Confirmar",
                    "callback_data": f"{action}:confirm:{id}",
                },
                {
                    "text": "No Cancelar",
                    "callback_data": f"{action}:cancel:{id}",
                },
            ]
        ]
    }


def pagination_keyboard(page: int, total_pages: int) -> dict:
    buttons = []
    row = []
    if page > 0:
        row.append(
            {
                "text": "‹ Anterior",
                "callback_data": f"list:page:{page - 1}",
            }
        )
    if page < total_pages - 1:
        row.append(
            {
                "text": "Siguiente ›",
                "callback_data": f"list:page:{page + 1}",
            }
        )
    if row:
        buttons.append(row)
    return {"inline_keyboard": buttons}
