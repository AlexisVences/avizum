from app.services.agent.guards import leaks_system_prompt, strip_external_links
from app.services.agent.prompt import SYSTEM_PROMPT


def test_a_verbatim_copy_of_the_prompt_is_detected():
    lines = SYSTEM_PROMPT.replace("\\\n", "").splitlines()
    long_line = max(lines, key=len)
    assert leaks_system_prompt(f"Claro, aquí está: {long_line}")


def test_a_paraphrase_or_normal_answer_is_not_a_leak():
    assert not leaks_system_prompt("Solo respondo sobre tránsito en la CDMX y cito fuentes oficiales.")
    assert not leaks_system_prompt("La multa es de 5, 7 o 10 veces la UMA [1].\n\nEsta información es orientativa y no sustituye asesoría legal.")


def test_images_links_and_bare_urls_are_removed_but_citations_stay():
    text = "Mira ![x](https://evil.example/p.png?q=1) y [aquí](https://phish.example/login) o www.otro.example/x. Multa [2]."
    cleaned, changed = strip_external_links(text)
    assert changed
    assert "evil" not in cleaned and "phish" not in cleaned and "otro.example" not in cleaned
    assert "aquí" in cleaned and "[2]" in cleaned


def test_text_without_links_is_untouched():
    text = "Son 5 veces la UMA [1]."
    assert strip_external_links(text) == (text, False)
