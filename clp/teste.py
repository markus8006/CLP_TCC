import os

# Caminho da pasta onde os arquivos .py estão localizados
diretorio = "C:\\Users\\senai\\Desktop\\projeto"

# Arquivo de saída
arquivo_saida = "nomes_e_conteudo_arquivos.txt"

# Abrir o arquivo de saída para escrever os nomes e conteúdos
with open(arquivo_saida, "w") as f:
    # Percorrer todos os arquivos no diretório
    for nome_arquivo in os.listdir(diretorio):
        # Verificar se o arquivo termina com '.py'
        if nome_arquivo.endswith(".py"):
            # Caminho completo do arquivo
            caminho_arquivo = os.path.join(diretorio, nome_arquivo)
            
            # Escrever o nome do arquivo no arquivo de saída
            f.write(f"Nome do arquivo: {nome_arquivo}\n")
            
            # Abrir o arquivo .py e ler seu conteúdo
            with open(caminho_arquivo, "r") as arquivo:
                conteudo = arquivo.read()
                # Escrever o conteúdo no arquivo de saída
                f.write(f"Conteúdo:\n{conteudo}\n")
                
            # Adicionar uma linha em branco entre os arquivos
            f.write("\n" + "="*40 + "\n\n")

print(f"Lista de arquivos .py e seus conteúdos salva em {arquivo_saida}")
