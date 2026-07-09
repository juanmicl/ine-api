# tests/test_paginator.py
import pytest

from ine._paginator import aiter_pages, iter_pages


def test_stops_on_short_page():
    pages = {1: list(range(500)), 2: list(range(100))}
    result = list(iter_pages(lambda p: pages[p]))
    assert len(result) == 2
    assert len(result[1]) == 100


def test_stops_on_empty():
    pages = {1: list(range(500)), 2: []}
    result = list(iter_pages(lambda p: pages.get(p, [])))
    assert len(result) == 1  # la página vacía no se yields


def test_stops_on_first_page_short():
    result = list(iter_pages(lambda p: list(range(10))))
    assert len(result) == 1
    assert len(result[0]) == 10


def test_stops_on_first_page_empty():
    result = list(iter_pages(lambda p: []))
    assert result == []


@pytest.mark.anyio
async def test_aiter_stops_on_short_page():
    pages = {1: list(range(500)), 2: list(range(100))}

    async def fetch_page(p: int) -> list:
        return pages[p]

    result = [chunk async for chunk in aiter_pages(fetch_page)]
    assert len(result) == 2
    assert len(result[1]) == 100


@pytest.mark.anyio
async def test_aiter_stops_on_empty():
    pages = {1: list(range(500)), 2: []}

    async def fetch_page(p: int) -> list:
        return pages.get(p, [])

    result = [chunk async for chunk in aiter_pages(fetch_page)]
    assert len(result) == 1  # la página vacía no se yields
