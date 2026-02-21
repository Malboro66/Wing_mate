# -*- coding: utf-8 -*-
# ===================================================================
# Wing Mate - utils/file_operations.py
# Utilitários para operações de arquivo com escrita atômica
# ===================================================================

import os
import tempfile
from pathlib import Path
from contextlib import contextmanager


@contextmanager
def atomic_json_write(filepath: Path):
    """Context manager para escrita atômica e durável de arquivos JSON.

    O conteúdo é escrito em arquivo temporário no mesmo diretório, com flush +
    ``os.fsync`` antes do ``os.replace`` para reduzir risco de truncamento após
    quedas de energia.
    """
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=filepath.parent,
        prefix='.tmp_',
        suffix='.json'
    )
    tmp_file = Path(tmp_path)

    try:
        with os.fdopen(tmp_fd, 'w', encoding='utf-8') as f:
            yield f
            f.flush()
            os.fsync(f.fileno())

        os.replace(str(tmp_file), str(filepath))

    except Exception:
        if tmp_file.exists():
            try:
                tmp_file.unlink()
            except OSError:
                pass
        raise


@contextmanager
def atomic_write(filepath: Path, mode: str = 'w', encoding: str = 'utf-8'):
    """Context manager genérico para escrita atômica de arquivos de texto.
    
    Versão mais genérica que suporta diferentes modos de escrita.
    
    Args:
        filepath: Caminho do arquivo de destino
        mode: Modo de abertura ('w', 'a', etc)
        encoding: Encoding do arquivo (padrão: utf-8)
        
    Yields:
        File handle para escrita
        
    Raises:
        OSError: Se houver falha na escrita ou renomeação do arquivo
    
    Example:
        >>> with atomic_write(Path("data.txt")) as f:
        ...     f.write("Hello, World!")
    """
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=filepath.parent,
        prefix='.tmp_',
        suffix=filepath.suffix
    )
    tmp_file = Path(tmp_path)
    
    try:
        with open(tmp_fd, mode, encoding=encoding) as f:
            yield f
        tmp_file.replace(filepath)
        
    except Exception:
        if tmp_file.exists():
            try:
                tmp_file.unlink()
            except OSError:
                pass
        raise
        
    finally:
        try:
            os.close(tmp_fd)
        except OSError:
            pass


def safe_read_json(filepath: Path, default=None):
    """Lê arquivo JSON com tratamento de erros e valor padrão.
    
    Args:
        filepath: Caminho do arquivo JSON
        default: Valor padrão a retornar em caso de erro (None por padrão)
        
    Returns:
        Dados JSON parseados ou valor padrão em caso de erro
    
    Example:
        >>> data = safe_read_json(Path("config.json"), default={})
    """
    import json
    
    if not filepath.exists():
        return default
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return default


def ensure_dir(directory: Path) -> bool:
    """Garante que um diretório existe, criando-o se necessário.
    
    Args:
        directory: Caminho do diretório
        
    Returns:
        True se diretório existe ou foi criado com sucesso, False caso contrário
    
    Example:
        >>> ensure_dir(Path("data/cache"))
    """
    try:
        directory.mkdir(parents=True, exist_ok=True)
        return True
    except OSError:
        return False


# Exemplo de uso
if __name__ == "__main__":
    import json
    from pathlib import Path
    
    print("Testando utilitários de arquivo...\n")
    
    # Teste 1: atomic_json_write
    test_file = Path("test_atomic.json")
    test_data = {"name": "Wing Mate", "version": "1.0.0", "medals": 11}
    
    try:
        with atomic_json_write(test_file) as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)
        print(f"✓ Teste 1: atomic_json_write - Arquivo criado: {test_file}")
        
        # Verifica conteúdo
        loaded = safe_read_json(test_file)
        assert loaded == test_data, "Dados não correspondem!"
        print(f"✓ Teste 1: Dados verificados: {loaded}")
        
    except Exception as e:
        print(f"✗ Teste 1 falhou: {e}")
    finally:
        if test_file.exists():
            test_file.unlink()
    
    # Teste 2: atomic_write (texto simples)
    test_txt = Path("test_atomic.txt")
    test_content = "Hello, Wing Mate!\nTeste de escrita atômica."
    
    try:
        with atomic_write(test_txt) as f:
            f.write(test_content)
        print(f"\n✓ Teste 2: atomic_write - Arquivo criado: {test_txt}")
        
        # Verifica conteúdo
        with open(test_txt, 'r', encoding='utf-8') as f:
            loaded_content = f.read()
        assert loaded_content == test_content, "Conteúdo não corresponde!"
        print(f"✓ Teste 2: Conteúdo verificado ({len(loaded_content)} caracteres)")
        
    except Exception as e:
        print(f"✗ Teste 2 falhou: {e}")
    finally:
        if test_txt.exists():
            test_txt.unlink()
    
    # Teste 3: safe_read_json com arquivo inexistente
    result = safe_read_json(Path("arquivo_inexistente.json"), default={"status": "default"})
    print(f"\n✓ Teste 3: safe_read_json - Valor padrão retornado: {result}")
    
    # Teste 4: ensure_dir
    test_dir = Path("test_dir/subdir/nested")
    if ensure_dir(test_dir):
        print(f"\n✓ Teste 4: ensure_dir - Diretório criado: {test_dir}")
        # Limpa
        import shutil
        shutil.rmtree(Path("test_dir"))
    else:
        print(f"\n✗ Teste 4 falhou")
    
    print("\n✓ Todos os testes concluídos!")
