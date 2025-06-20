import os

def concatenate_all_code(root_dir="farmtech_final/", output_file="todos_os_codigos.txt"):
    """
    Percorre o diretório root_dir, coleta o conteúdo de arquivos de texto/código
    e os concatena em output_file. Inclui o máximo de arquivos possível,
    excluindo apenas os próprios arquivos de script/saída e binários detectados.
    """
    
    # Nomes de arquivos e diretórios a serem explicitamente excluídos
    # Minimizar ao máximo, apenas o script e o arquivo de saída para evitar recursão
    EXCLUDE_NAMES = (os.path.basename(output_file), os.path.basename(__file__))
    
    # Nomes de diretórios a serem explicitamente excluídos (geralmente metadados, virtualenvs, ou pastas de build)
    # Manter as essenciais para não varrer lixo ou estruturas temporárias.
    EXCLUDE_DIRS = ('.git', '__pycache__', '.pytest_cache', '.venv', 'node_modules', '.vscode', 'build', 'dist')

    print(f"DEBUG: Iniciando concatenação de código de '{os.path.abspath(root_dir)}' para '{output_file}'...")
    
    # Use um set para controlar arquivos já adicionados, caso haja symlinks ou caminhos complexos
    processed_files = set()

    with open(output_file, 'w', encoding='utf-8', errors='replace') as outfile:
        for dirpath, dirnames, filenames in os.walk(root_dir, topdown=True):
            # Excluir diretórios (modificar dirnames in place)
            dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
            
            # Ajustar o dirpath para ser relativo ao root_dir
            display_dirpath = os.path.relpath(dirpath, root_dir)

            for filename in filenames:
                file_path_full = os.path.join(dirpath, filename)
                display_file_path = os.path.relpath(file_path_full, root_dir)

                if display_file_path in processed_files:
                    print(f"DEBUG: Pulando arquivo já processado (duplicata ou symlink): {display_file_path}")
                    continue

                # Ignorar arquivos que devem ser explicitamente excluídos
                if filename in EXCLUDE_NAMES:
                    print(f"DEBUG: Ignorando arquivo por nome na exclusão explícita: {display_file_path}")
                    continue
                
                # Ignorar arquivos muito grandes (provavelmente não são código-fonte simples)
                try:
                    if os.path.getsize(file_path_full) > 2 * 1024 * 1024: # Aumentar limite para 2MB
                        print(f"DEBUG: Ignorando arquivo muito grande (>2MB): {display_file_path}")
                        continue
                except Exception as e:
                    print(f"DEBUG: Não foi possível verificar o tamanho do arquivo {display_file_path}: {e}")
                    continue
                
                # Tentativa de detectar binários pela leitura de um pequeno cabeçalho e erro de decodificação
                is_binary = False
                try:
                    with open(file_path_full, 'rb') as f:
                        header = f.read(256) # Ler os primeiros 256 bytes
                        if b'\x00' in header: # Presença de byte nulo geralmente indica binário
                            is_binary = True
                        elif header.startswith((b'\x89PNG', b'GIF89a', b'JFIF', b'%PDF-', b'PK\x03\x04')): # Algumas assinaturas de binários comuns (PNG, GIF, JPG, PDF, ZIP)
                            is_binary = True
                except Exception as e:
                    print(f"DEBUG: Erro ao ler cabeçalho de {display_file_path} para detecção de binário: {e}")
                    is_binary = True 
                
                if is_binary:
                    print(f"DEBUG: Ignorando possível arquivo binário: {display_file_path}")
                    continue

                try:
                    with open(file_path_full, 'r', encoding='utf-8') as infile:\
                        content = infile.read()
                    
                    outfile.write(f"\n--- Início do Arquivo: {display_file_path} ---\n")
                    outfile.write(content)
                    outfile.write(f"\n--- Fim do Arquivo: {display_file_path} ---\n\n")
                    print(f"DEBUG: Adicionado {display_file_path}")
                    processed_files.add(display_file_path) # Marcar como processado
                except UnicodeDecodeError:
                    print(f"DEBUG: Ignorando arquivo com erro de codificação (provavelmente binário): {display_file_path}")
                    continue
                except Exception as e:
                    print(f"DEBUG: Não foi possível ler ou escrever o arquivo {file_path_full}: {e}")
    
    print(f"DEBUG: Concatenação concluída. Verifique '{output_file}'.")

if __name__ == "__main__":
    concatenate_all_code()
