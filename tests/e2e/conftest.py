"""
Fixtures para tests E2E con Playwright.

Para ejecutar estos tests necesitas:
1. Instalar playwright: uv add --dev playwright
2. Instalar browsers: playwright install chromium
3. Tener el servidor corriendo: uv run uvicorn autocode.interfaces.api:app --reload

Ejecutar tests:
    uv run pytest tests/e2e/ -v
"""

import pytest
from typing import Generator
import subprocess
import time
import os

# Intentar importar playwright, si no está disponible los tests se saltarán
try:
    from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


# Skip si playwright no está instalado
pytestmark = pytest.mark.skipif(
    not PLAYWRIGHT_AVAILABLE,
    reason="Playwright no está instalado. Ejecuta: uv add --dev playwright && playwright install chromium"
)


@pytest.fixture(scope="session")
def browser() -> Generator[Browser, None, None]:
    """Fixture que proporciona un browser de Playwright para toda la sesión."""
    if not PLAYWRIGHT_AVAILABLE:
        pytest.skip("Playwright no disponible")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def context(browser: Browser) -> Generator[BrowserContext, None, None]:
    """Fixture que proporciona un contexto de browser limpio por test."""
    context = browser.new_context(
        viewport={"width": 1280, "height": 720}
    )
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext) -> Generator[Page, None, None]:
    """Fixture que proporciona una página limpia por test."""
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture(scope="session")
def base_url() -> str:
    """URL base del servidor de desarrollo."""
    return os.environ.get("TEST_BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="function")
def chat_page(page: Page, base_url: str) -> Page:
    """Fixture que navega a la página principal con el chat."""
    page.goto(f"{base_url}/")
    # Esperar a que los custom elements estén definidos
    page.wait_for_function("""
        () => customElements.get('autocode-chat') !== undefined
    """, timeout=10000)
    return page


@pytest.fixture(scope="function")
def demo_page(page: Page, base_url: str) -> Page:
    """Fixture que navega a la página de demo."""
    page.goto(f"{base_url}/demo")
    page.wait_for_load_state("networkidle")
    return page


@pytest.fixture(scope="function")
def test_page(page: Page, base_url: str) -> Page:
    """Fixture que navega a la página de tests de componentes."""
    page.goto(f"{base_url}/elements/chat/tests.html")
    page.wait_for_load_state("networkidle")
    return page
