import json
import os
import sys

import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import utils.file_operations as file_operations


def test_atomic_json_write_replaces_target_file(tmp_path: Path):
    target = tmp_path / "data.json"
    target.write_text('{"old": true}', encoding="utf-8")

    with file_operations.atomic_json_write(target) as f:
        json.dump({"new": True}, f)

    assert json.loads(target.read_text(encoding="utf-8")) == {"new": True}
    assert not list(tmp_path.glob('.tmp_*.json'))


def test_atomic_json_write_calls_fsync(tmp_path: Path, monkeypatch):
    target = tmp_path / "durable.json"
    called = []

    def fake_fsync(fd: int):
        called.append(fd)

    monkeypatch.setattr(file_operations.os, "fsync", fake_fsync)

    with file_operations.atomic_json_write(target) as f:
        json.dump({"durable": True}, f)

    assert called
    assert json.loads(target.read_text(encoding="utf-8")) == {"durable": True}


# ── testes para atomic_write ──────────────────────────────────────────────

def test_atomic_write_creates_file_with_correct_content(tmp_path: Path):
    """atomic_write deve criar o arquivo de destino com o conteúdo escrito."""
    target = tmp_path / "output.txt"
    content = "Hello, Wing Mate!\nLinha dois."

    with file_operations.atomic_write(target) as f:
        f.write(content)

    assert target.exists()
    assert target.read_text(encoding="utf-8") == content


def test_atomic_write_replaces_existing_file(tmp_path: Path):
    """atomic_write deve sobrescrever arquivo de destino pré-existente."""
    target = tmp_path / "output.txt"
    target.write_text("conteúdo antigo", encoding="utf-8")

    with file_operations.atomic_write(target) as f:
        f.write("conteúdo novo")

    assert target.read_text(encoding="utf-8") == "conteúdo novo"


def test_atomic_write_leaves_no_temp_files_on_success(tmp_path: Path):
    """Após escrita bem-sucedida, nenhum arquivo .tmp_ deve permanecer."""
    target = tmp_path / "output.txt"

    with file_operations.atomic_write(target) as f:
        f.write("dados")

    temp_files = list(tmp_path.glob(".tmp_*"))
    assert temp_files == [], f"Arquivos temporários encontrados: {temp_files}"


def test_atomic_write_leaves_no_temp_files_on_error(tmp_path: Path):
    """Se ocorrer exceção durante escrita, o arquivo temporário deve ser limpo."""
    target = tmp_path / "output.txt"

    with pytest.raises(ValueError):
        with file_operations.atomic_write(target) as f:
            f.write("início...")
            raise ValueError("erro simulado")

    temp_files = list(tmp_path.glob(".tmp_*"))
    assert temp_files == [], f"Arquivos temporários encontrados: {temp_files}"
    assert not target.exists(), "Arquivo de destino não deveria ter sido criado"


def test_atomic_write_calls_fsync(tmp_path: Path, monkeypatch):
    """atomic_write deve chamar os.fsync para garantir durabilidade."""
    target = tmp_path / "durable.txt"
    fsync_called = []

    def fake_fsync(fd: int):
        fsync_called.append(fd)

    monkeypatch.setattr(file_operations.os, "fsync", fake_fsync)

    with file_operations.atomic_write(target) as f:
        f.write("dados duráveis")

    assert fsync_called, "os.fsync não foi chamado"
    assert target.read_text(encoding="utf-8") == "dados duráveis"




def test_atomic_write_calls_fsync_before_replace(tmp_path: Path, monkeypatch):
    """os.fsync deve ser chamado ANTES de tmp_file.replace() — não depois."""
    target = tmp_path / "order_check.txt"
    call_order = []

    original_fsync = file_operations.os.fsync

    def tracking_fsync(fd: int):
        call_order.append("fsync")
        original_fsync(fd)

    original_replace = file_operations.Path.replace

    def tracking_replace(self_path, dst):
        call_order.append("replace")
        return original_replace(self_path, dst)

    monkeypatch.setattr(file_operations.os, "fsync", tracking_fsync)
    monkeypatch.setattr(file_operations.Path, "replace", tracking_replace)

    with file_operations.atomic_write(target) as f:
        f.write("ordem importa")

    assert "fsync" in call_order, "os.fsync não foi chamado"
    assert "replace" in call_order, "replace não foi chamado"
    fsync_idx = call_order.index("fsync")
    replace_idx = call_order.index("replace")
    assert fsync_idx < replace_idx, (
        f"os.fsync deve ocorrer ANTES do replace — ordem encontrada: {call_order}"
    )


def test_atomic_write_fsync_parity_with_atomic_json_write(tmp_path: Path, monkeypatch):
    """atomic_write e atomic_json_write devem ter comportamento de fsync equivalente.

    Ambas devem chamar os.fsync exatamente uma vez por operação de escrita.
    """
    json_target = tmp_path / "data.json"
    txt_target = tmp_path / "data.txt"

    json_fsync_calls = []
    txt_fsync_calls = []

    original_fsync = file_operations.os.fsync
    call_context = {"active": None}

    def routing_fsync(fd: int):
        if call_context["active"] == "json":
            json_fsync_calls.append(fd)
        elif call_context["active"] == "txt":
            txt_fsync_calls.append(fd)
        original_fsync(fd)

    monkeypatch.setattr(file_operations.os, "fsync", routing_fsync)

    call_context["active"] = "json"
    with file_operations.atomic_json_write(json_target) as f:
        json.dump({"ok": True}, f)

    call_context["active"] = "txt"
    with file_operations.atomic_write(txt_target) as f:
        f.write("ok")

    assert len(json_fsync_calls) == 1, (
        f"atomic_json_write deveria chamar fsync 1x, chamou {len(json_fsync_calls)}x"
    )
    assert len(txt_fsync_calls) == 1, (
        f"atomic_write deveria chamar fsync 1x, chamou {len(txt_fsync_calls)}x"
    )

def test_atomic_write_no_double_close(tmp_path: Path, monkeypatch):
    """atomic_write não deve tentar fechar o file descriptor duas vezes.

    Se os.close() for chamado sobre um fd já fechado por os.fdopen(),
    o sistema operacional retorna EBADF (errno 9). Este teste garante
    que isso não ocorre — o fd é fechado exatamente uma vez.
    """
    target = tmp_path / "output.txt"
    close_calls: list[int] = []
    original_close = os.close

    def tracking_close(fd: int) -> None:
        close_calls.append(fd)
        original_close(fd)

    monkeypatch.setattr(file_operations.os, "close", tracking_close)

    with file_operations.atomic_write(target) as f:
        f.write("teste de fechamento único")

    assert close_calls == [], (
        f"os.close() foi chamado {len(close_calls)} vez(es) com fd(s) {close_calls}. "
        "Esperado: 0 chamadas diretas (fd deve ser fechado pelo os.fdopen)."
    )
