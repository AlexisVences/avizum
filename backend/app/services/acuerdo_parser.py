"""Parse the SSC 'nombre completo y número de placa' acuerdo published in the Gaceta Oficial.

Extracted PDF text lists each officer as three lines (row number, plate, name) with page headers
interleaved. Rows are accepted only in strict sequence, so stray page numbers are skipped, and the
caller validates the totals against the counts the acuerdo declares.
"""
import re
from dataclasses import dataclass

from app.models.domain import AuthorizationType

SECTION_PATTERN = re.compile(r"(PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO)\.\s+Se da a conocer", re.IGNORECASE)
END_PATTERN = re.compile(r"\bTRANSITORIOS\b")
PLATE_PATTERN = re.compile(r"\d{3,8}")
NAME_PATTERN = re.compile(r"[A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ.'\- ]*\s[A-ZÁÉÍÓÚÜÑ.'\- ]+")
CONTINUATION_PATTERN = re.compile(r"[A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ.'\- ]*")


class AcuerdoParseError(ValueError):
    pass


@dataclass(frozen=True)
class AgentRow:
    number: int
    plate: str
    full_name: str


@dataclass(frozen=True)
class ParsedSection:
    authorization_type: AuthorizationType
    heading: str
    rows: list[AgentRow]


def _classify(heading: str) -> AuthorizationType:
    text = heading.lower()
    portable = "portátiles" in text or "portatiles" in text
    technological = "sistemas tecnológicos" in text or "sistemas tecnologicos" in text
    if portable == technological:
        raise AcuerdoParseError(f"Sección no reconocida: {heading[:200]}")
    return AuthorizationType.VIA_PUBLICA if portable else AuthorizationType.SISTEMAS_TECNOLOGICOS


def _is_continuation(line: str) -> bool:
    return bool(CONTINUATION_PATTERN.fullmatch(line)) and "GACETA OFICIAL" not in line


def _parse_rows(chunk: str) -> list[AgentRow]:
    lines = [line.strip() for line in chunk.splitlines() if line.strip()]
    rows: list[AgentRow] = []
    expected, i = 1, 0
    while i + 2 < len(lines):
        number, plate, name = lines[i], lines[i + 1], lines[i + 2]
        if number == str(expected) and PLATE_PATTERN.fullmatch(plate) and NAME_PATTERN.fullmatch(name):
            parts = [name]
            i += 3
            while i < len(lines) and lines[i] != str(expected + 1) and _is_continuation(lines[i]):
                parts.append(lines[i])
                i += 1
            rows.append(AgentRow(expected, plate, " ".join(" ".join(parts).split())))
            expected += 1
        else:
            i += 1
    return rows


def parse_acuerdo(text: str) -> list[ParsedSection]:
    end = END_PATTERN.search(text)
    if end is None:
        raise AcuerdoParseError("No se encontró la sección TRANSITORIOS")
    body = text[: end.start()]
    starts = list(SECTION_PATTERN.finditer(body))
    if not starts:
        raise AcuerdoParseError("No se encontraron listas ('PRIMERO. Se da a conocer…')")
    sections = []
    for index, match in enumerate(starts):
        stop = starts[index + 1].start() if index + 1 < len(starts) else len(body)
        chunk = body[match.start():stop]
        heading = " ".join(chunk[:700].split())
        rows = _parse_rows(chunk)
        if not rows:
            raise AcuerdoParseError(f"Sección sin registros: {heading[:120]}")
        sections.append(ParsedSection(_classify(heading), heading[:300], rows))
    return sections


def validate_counts(sections: list[ParsedSection], expected: dict[str, int]) -> None:
    got: dict[str, int] = {}
    for section in sections:
        key = section.authorization_type.value
        if key in got:
            raise AcuerdoParseError(f"Tipo de autorización repetido: {key}")
        got[key] = len(section.rows)
        plates = [row.plate for row in section.rows]
        duplicated = {plate for plate in plates if plates.count(plate) > 1}
        if duplicated:
            raise AcuerdoParseError(f"Placa duplicada en {key}: {sorted(duplicated)}")
    if got != expected:
        raise AcuerdoParseError(f"Conteos no coinciden: esperado {expected}, obtenido {got}")
