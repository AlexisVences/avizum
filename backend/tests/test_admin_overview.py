from app.core.config import Settings


def test_los_precios_tienen_un_valor_por_defecto_positivo():
    settings = Settings()
    assert settings.llm_price_input_per_million > 0
    assert settings.llm_price_output_per_million > 0
