# ine/_paginator.py
"""Paginador perezoso para los endpoints de lista del INE.

Los endpoints de lista del INE se paginan con el query param ``page`` y entregan
hasta ``PAGE_SIZE`` (500) elementos por página. La respuesta NO incluye un campo
con el total de elementos, por lo que la única forma de saber que se llegó al
final es detectar una página *corta* (menos de 500 elementos) o vacía.

Este módulo es una utilidad pura: no realiza HTTP. Recibe un callable que, dado
un número de página (1-based), devuelve la lista de elementos de esa página.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable, Iterator

#: Tamaño de página del INE: si una página trae menos elementos, es la última.
PAGE_SIZE = 500


def iter_pages[T](fetch_page: Callable[[int], list[T]]) -> Iterator[list[T]]:
    """Itera perezosamente las páginas que devuelve ``fetch_page``.

    ``fetch_page`` recibe un número de página (1-based) y devuelve la lista de
    elementos de esa página. Se detiene al recibir una página vacía o con menos
    de :data:`PAGE_SIZE` elementos.
    """
    page = 1
    while True:
        chunk = fetch_page(page)
        if not chunk:
            return
        yield chunk
        if len(chunk) < PAGE_SIZE:
            return
        page += 1


async def aiter_pages[T](
    fetch_page: Callable[[int], Awaitable[list[T]]],
) -> AsyncIterator[list[T]]:
    """Versión asíncrona de :func:`iter_pages`.

    ``fetch_page`` es un callable asíncrono que recibe el número de página
    (1-based) y devuelve un awaitable con la lista de elementos de esa página.
    Se detiene al recibir una página vacía o con menos de :data:`PAGE_SIZE`.
    """
    page = 1
    while True:
        chunk = await fetch_page(page)
        if not chunk:
            return
        yield chunk
        if len(chunk) < PAGE_SIZE:
            return
        page += 1
