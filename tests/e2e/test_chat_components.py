"""
Tests E2E para los componentes del chat.

Ejecutar con:
    uv run pytest tests/e2e/test_chat_components.py -v

Requiere:
    - Servidor corriendo: uv run uvicorn autocode.interfaces.api:app --reload
    - Playwright instalado: uv add --dev playwright && playwright install chromium
"""

import pytest
import re

# Importar solo si playwright está disponible
try:
    from playwright.sync_api import Page, expect
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


pytestmark = pytest.mark.skipif(
    not PLAYWRIGHT_AVAILABLE,
    reason="Playwright no está instalado"
)


class TestChatWindow:
    """Tests para el componente chat-window."""

    def test_toggle_button_visible(self, chat_page: Page):
        """El botón de toggle debe ser visible al cargar la página."""
        toggle_btn = chat_page.locator('chat-window [data-ref="toggleBtn"]')
        expect(toggle_btn).to_be_visible()

    def test_chat_opens_on_toggle_click(self, chat_page: Page):
        """El chat debe abrirse al hacer click en el botón de toggle."""
        toggle_btn = chat_page.locator('chat-window [data-ref="toggleBtn"]')
        panel = chat_page.locator('chat-window [data-ref="panel"]')
        
        # Inicialmente oculto
        expect(panel).to_have_class(re.compile(r"hidden"))
        
        # Click para abrir
        toggle_btn.click()
        expect(panel).not_to_have_class(re.compile(r"hidden"))

    def test_chat_closes_on_close_button(self, chat_page: Page):
        """El chat debe cerrarse al hacer click en el botón de cerrar."""
        toggle_btn = chat_page.locator('chat-window [data-ref="toggleBtn"]')
        close_btn = chat_page.locator('chat-window [data-ref="closeBtn"]')
        panel = chat_page.locator('chat-window [data-ref="panel"]')
        
        # Abrir primero
        toggle_btn.click()
        expect(panel).not_to_have_class(re.compile(r"hidden"))
        
        # Cerrar
        close_btn.click()
        expect(panel).to_have_class(re.compile(r"hidden"))

    def test_drag_window(self, chat_page: Page):
        """La ventana debe poder arrastrarse."""
        toggle_btn = chat_page.locator('chat-window [data-ref="toggleBtn"]')
        toggle_btn.click()
        
        window = chat_page.locator('chat-window [data-ref="window"]')
        drag_handle = chat_page.locator('chat-window [data-ref="dragHandle"]')
        
        # Obtener posición inicial
        initial_box = window.bounding_box()
        
        # Arrastrar
        drag_handle.drag_to(chat_page.locator('body'), 
                          source_position={"x": 50, "y": 20},
                          target_position={"x": 200, "y": 200})
        
        # Verificar que se movió
        final_box = window.bounding_box()
        assert final_box["x"] != initial_box["x"] or final_box["y"] != initial_box["y"]


class TestChatInput:
    """Tests para el componente chat-input."""

    def test_input_visible_when_chat_open(self, chat_page: Page):
        """El input debe ser visible cuando el chat está abierto."""
        toggle_btn = chat_page.locator('chat-window [data-ref="toggleBtn"]')
        toggle_btn.click()
        
        chat_input = chat_page.locator('chat-input input')
        expect(chat_input).to_be_visible()

    def test_send_button_visible(self, chat_page: Page):
        """El botón de enviar debe ser visible."""
        toggle_btn = chat_page.locator('chat-window [data-ref="toggleBtn"]')
        toggle_btn.click()
        
        send_btn = chat_page.locator('chat-input button')
        expect(send_btn).to_be_visible()
        expect(send_btn).to_contain_text('Enviar')


class TestChatMessages:
    """Tests para el componente chat-messages."""

    def test_empty_state_visible_initially(self, chat_page: Page):
        """El estado vacío debe mostrarse inicialmente."""
        toggle_btn = chat_page.locator('chat-window [data-ref="toggleBtn"]')
        toggle_btn.click()
        
        empty_state = chat_page.locator('chat-messages [data-ref="emptyState"]')
        expect(empty_state).to_be_visible()
        expect(empty_state).to_contain_text('Inicia una conversación')


class TestContextBar:
    """Tests para el componente context-bar."""

    def test_context_bar_visible(self, chat_page: Page):
        """La barra de contexto debe ser visible."""
        toggle_btn = chat_page.locator('chat-window [data-ref="toggleBtn"]')
        toggle_btn.click()
        
        context_bar = chat_page.locator('context-bar')
        expect(context_bar).to_be_visible()

    def test_context_bar_shows_stats(self, chat_page: Page):
        """La barra de contexto debe mostrar estadísticas."""
        toggle_btn = chat_page.locator('chat-window [data-ref="toggleBtn"]')
        toggle_btn.click()
        
        stats = chat_page.locator('context-bar [data-ref="stats"]')
        expect(stats).to_be_visible()
        expect(stats).to_contain_text('/')


class TestChatIntegration:
    """Tests de integración del chat completo."""

    def test_new_chat_button_clears_messages(self, chat_page: Page):
        """El botón 'Nueva' debe limpiar los mensajes."""
        toggle_btn = chat_page.locator('chat-window [data-ref="toggleBtn"]')
        toggle_btn.click()
        
        new_btn = chat_page.locator('[data-ref="newChatBtn"]')
        expect(new_btn).to_be_visible()
        
        # Click en nueva conversación
        new_btn.click()
        
        # Verificar que aparece el empty state
        empty_state = chat_page.locator('chat-messages [data-ref="emptyState"]')
        expect(empty_state).to_be_visible()

    def test_full_chat_flow(self, chat_page: Page):
        """Test del flujo completo de envío de mensaje."""
        # Abrir chat
        toggle_btn = chat_page.locator('chat-window [data-ref="toggleBtn"]')
        toggle_btn.click()
        
        # Escribir mensaje
        chat_input = chat_page.locator('chat-input input')
        chat_input.fill('Hola, esto es un test')
        
        # El empty state debería desaparecer después de enviar
        send_btn = chat_page.locator('chat-input button')
        send_btn.click()
        
        # Esperar a que aparezca el mensaje del usuario
        user_message = chat_page.locator('chat-messages [data-role="user"]')
        expect(user_message).to_be_visible(timeout=5000)
        expect(user_message).to_contain_text('Hola, esto es un test')
        
        # El input debería estar vacío después de enviar
        expect(chat_input).to_have_value('')


class TestUnitTestsPage:
    """Tests que verifican que los tests unitarios en tests.html pasan."""

    def test_unit_tests_page_loads(self, test_page: Page):
        """La página de tests debe cargar correctamente."""
        title = test_page.locator('h1')
        expect(title).to_contain_text('Chat Components')

    def test_unit_tests_summary_exists(self, test_page: Page):
        """Debe existir un resumen de tests."""
        summary = test_page.locator('#summary')
        # Esperar a que los tests terminen
        test_page.wait_for_timeout(3000)
        expect(summary).to_be_visible()

    def test_no_failed_tests(self, test_page: Page):
        """No debe haber tests fallidos (solo si los componentes existen)."""
        # Esperar a que los tests terminen
        test_page.wait_for_timeout(5000)
        
        # Contar tests fallidos
        failed = test_page.locator('.bg-red-100')
        failed_count = failed.count()
        
        # Si hay tests fallidos, obtener los mensajes para debug
        if failed_count > 0:
            failed_texts = []
            for i in range(failed_count):
                failed_texts.append(failed.nth(i).text_content())
            pytest.fail(f"Tests fallidos: {failed_texts}")
