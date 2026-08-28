import discord
from discord import app_commands
import os
import re
import base64
import requests

from dotenv import load_dotenv


# ==========================================
# CONFIGURAÇÕES
# ==========================================

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")

PASTA_NPCS = "npcs"


SEU_DISCORD_ID = 880067814680064010


os.makedirs(PASTA_NPCS, exist_ok=True)

intents = discord.Intents.default()
intents.message_content = True


# ==========================================
# BOT
# ==========================================

class MeuBot(discord.Client):

    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()


bot = MeuBot()


# ==========================================
# EXTENSÕES PERMITIDAS
# ==========================================

EXTENSOES_PERMITIDAS = [
    ".png",
    ".jpg",
    ".jpeg",
    ".webp"
]


# ==========================================
# FUNÇÕES AUXILIARES
# ==========================================

def limpar_nome(nome):
    return nome.lower().strip()


def eh_dono(interaction: discord.Interaction):
    return interaction.user.id == SEU_DISCORD_ID


async def verificar_permissao(interaction: discord.Interaction):

    if not eh_dono(interaction):

        await interaction.response.send_message(
            "❌ Você não tem permissão para usar este comando.",
            ephemeral=True
        )

        return False

    return True


def procurar_npc(nome):

    nome_limpo = limpar_nome(nome)

    for arquivo in os.listdir(PASTA_NPCS):

        nome_arquivo, extensao = os.path.splitext(arquivo)

        if (
            nome_arquivo.lower() == nome_limpo
            and extensao.lower() in EXTENSOES_PERMITIDAS
        ):
            return arquivo

    return None


# ==========================================
# GITHUB
# ==========================================

def github_headers():

    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }


def github_url(caminho):

    return (
        f"https://api.github.com/repos/"
        f"{GITHUB_REPO}/contents/{caminho}"
    )


def github_buscar_arquivo(caminho):

    resposta = requests.get(
        github_url(caminho),
        headers=github_headers(),
        params={
            "ref": GITHUB_BRANCH
        }
    )

    if resposta.status_code == 200:
        return resposta.json()

    if resposta.status_code == 404:
        return None

    print(
        "Erro ao buscar arquivo no GitHub:",
        resposta.status_code,
        resposta.text
    )

    return None


def github_salvar_arquivo(
    caminho_local,
    caminho_github,
    mensagem_commit
):

    if not GITHUB_TOKEN or not GITHUB_REPO:

        print(
            "GitHub não configurado no .env"
        )

        return False

    with open(
        caminho_local,
        "rb"
    ) as arquivo:

        conteudo = arquivo.read()

    conteudo_base64 = base64.b64encode(
        conteudo
    ).decode("utf-8")

    arquivo_existente = github_buscar_arquivo(
        caminho_github
    )

    dados = {
        "message": mensagem_commit,
        "content": conteudo_base64,
        "branch": GITHUB_BRANCH
    }

    if arquivo_existente is not None:

        dados["sha"] = arquivo_existente["sha"]

    resposta = requests.put(
        github_url(caminho_github),
        headers=github_headers(),
        json=dados
    )

    if resposta.status_code in [
        200,
        201
    ]:

        print(
            f"Arquivo enviado ao GitHub: "
            f"{caminho_github}"
        )

        return True

    print(
        "Erro ao enviar arquivo ao GitHub:",
        resposta.status_code,
        resposta.text
    )

    return False


def github_apagar_arquivo(
    caminho_github,
    mensagem_commit
):

    if not GITHUB_TOKEN or not GITHUB_REPO:

        print(
            "GitHub não configurado no .env"
        )

        return False

    arquivo_existente = github_buscar_arquivo(
        caminho_github
    )

    if arquivo_existente is None:

        print(
            f"Arquivo não existe no GitHub: "
            f"{caminho_github}"
        )

        return True

    dados = {
        "message": mensagem_commit,
        "sha": arquivo_existente["sha"],
        "branch": GITHUB_BRANCH
    }

    resposta = requests.delete(
        github_url(caminho_github),
        headers=github_headers(),
        json=dados
    )

    if resposta.status_code == 200:

        print(
            f"Arquivo apagado do GitHub: "
            f"{caminho_github}"
        )

        return True

    print(
        "Erro ao apagar arquivo do GitHub:",
        resposta.status_code,
        resposta.text
    )

    return False


# ==========================================
# BOT CONECTADO
# ==========================================

@bot.event
async def on_ready():

    print("=" * 50)
    print(f"Bot conectado como {bot.user}")
    print(f"Repositório GitHub: {GITHUB_REPO}")
    print(f"Branch: {GITHUB_BRANCH}")
    print("=" * 50)


# ==========================================
# REGISTRAR NPC
# ==========================================

@bot.tree.command(
    name="registrar",
    description="Registra um novo NPC e sua imagem"
)
@app_commands.describe(
    nome="Nome do NPC",
    imagem="Imagem do NPC"
)
async def registrar(
    interaction: discord.Interaction,
    nome: str,
    imagem: discord.Attachment
):

    if not await verificar_permissao(interaction):
        return

    await interaction.response.defer(
        ephemeral=True
    )

    nome_limpo = limpar_nome(nome)

    extensao = os.path.splitext(
        imagem.filename
    )[1].lower()

    if extensao not in EXTENSOES_PERMITIDAS:

        await interaction.followup.send(
            "❌ A imagem precisa ser PNG, JPG, JPEG ou WEBP.",
            ephemeral=True
        )

        return

    if procurar_npc(nome) is not None:

        await interaction.followup.send(
            f"❌ O NPC **{nome}** já está registrado.\n"
            f"Use `/editar` para fazer alterações.",
            ephemeral=True
        )

        return

    nome_arquivo = nome_limpo + extensao

    caminho_local = os.path.join(
        PASTA_NPCS,
        nome_arquivo
    )

    await imagem.save(
        caminho_local
    )

    caminho_github = (
        f"npcs/{nome_arquivo}"
    )

    sucesso_github = github_salvar_arquivo(
        caminho_local,
        caminho_github,
        f"Registrar NPC {nome}"
    )

    if sucesso_github:

        await interaction.followup.send(
            f"✅ NPC **{nome}** registrado com sucesso!\n"
            f"☁️ Imagem salva no GitHub.",
            ephemeral=True
        )

    else:

        await interaction.followup.send(
            f"⚠️ NPC **{nome}** foi salvo localmente, "
            f"mas houve erro ao enviar para o GitHub.",
            ephemeral=True
        )


# ==========================================
# EDITAR NPC
# ==========================================

@bot.tree.command(
    name="editar",
    description="Edita o nome e/ou a imagem de um NPC"
)
@app_commands.describe(
    nome_atual="Nome atual do NPC",
    novo_nome="Novo nome do NPC",
    nova_imagem="Nova imagem do NPC"
)
async def editar(
    interaction: discord.Interaction,
    nome_atual: str,
    novo_nome: str = None,
    nova_imagem: discord.Attachment = None
):

    if not await verificar_permissao(interaction):
        return

    await interaction.response.defer(
        ephemeral=True
    )

    arquivo_antigo = procurar_npc(
        nome_atual
    )

    if arquivo_antigo is None:

        await interaction.followup.send(
            f"❌ O NPC **{nome_atual}** não está registrado.",
            ephemeral=True
        )

        return

    if novo_nome is None and nova_imagem is None:

        await interaction.followup.send(
            "❌ Informe um novo nome, "
            "uma nova imagem ou os dois.",
            ephemeral=True
        )

        return

    nome_arquivo_antigo, extensao_antiga = os.path.splitext(
        arquivo_antigo
    )

    caminho_local_antigo = os.path.join(
        PASTA_NPCS,
        arquivo_antigo
    )

    caminho_github_antigo = (
        f"npcs/{arquivo_antigo}"
    )

    # ======================================
    # NOME FINAL
    # ======================================

    if novo_nome is not None:

        nome_final = limpar_nome(
            novo_nome
        )

        npc_existente = procurar_npc(
            novo_nome
        )

        if (
            npc_existente is not None
            and limpar_nome(novo_nome)
            != limpar_nome(nome_atual)
        ):

            await interaction.followup.send(
                f"❌ Já existe um NPC chamado "
                f"**{novo_nome}**.",
                ephemeral=True
            )

            return

    else:

        nome_final = limpar_nome(
            nome_atual
        )

    # ======================================
    # EXTENSÃO FINAL
    # ======================================

    if nova_imagem is not None:

        extensao_final = os.path.splitext(
            nova_imagem.filename
        )[1].lower()

        if extensao_final not in EXTENSOES_PERMITIDAS:

            await interaction.followup.send(
                "❌ A imagem precisa ser PNG, JPG, JPEG ou WEBP.",
                ephemeral=True
            )

            return

    else:

        extensao_final = extensao_antiga

    arquivo_final = (
        nome_final + extensao_final
    )

    caminho_local_final = os.path.join(
        PASTA_NPCS,
        arquivo_final
    )

    caminho_github_final = (
        f"npcs/{arquivo_final}"
    )

    # ======================================
    # SALVAR ALTERAÇÃO LOCAL
    # ======================================

    if nova_imagem is not None:

        if os.path.exists(
            caminho_local_antigo
        ):

            os.remove(
                caminho_local_antigo
            )

        await nova_imagem.save(
            caminho_local_final
        )

    elif caminho_local_antigo != caminho_local_final:

        os.rename(
            caminho_local_antigo,
            caminho_local_final
        )

    # ======================================
    # SINCRONIZAR GITHUB
    # ======================================

    # Se mudou o nome ou extensão,
    # apaga o arquivo antigo no GitHub
    if caminho_github_antigo != caminho_github_final:

        github_apagar_arquivo(
            caminho_github_antigo,
            f"Remover arquivo antigo de {nome_atual}"
        )

    sucesso_github = github_salvar_arquivo(
        caminho_local_final,
        caminho_github_final,
        f"Editar NPC {nome_atual}"
    )

    alteracoes = []

    if novo_nome is not None:

        alteracoes.append(
            f"📝 Nome: **{nome_atual}** → **{novo_nome}**"
        )

    if nova_imagem is not None:

        alteracoes.append(
            "🖼️ Imagem atualizada"
        )

    texto_alteracoes = "\n".join(
        alteracoes
    )

    if sucesso_github:

        await interaction.followup.send(
            f"✏️ **NPC atualizado com sucesso!**\n\n"
            f"{texto_alteracoes}\n\n"
            f"☁️ Alteração salva no GitHub.",
            ephemeral=True
        )

    else:

        await interaction.followup.send(
            f"⚠️ NPC atualizado localmente, "
            f"mas houve erro ao sincronizar com o GitHub.",
            ephemeral=True
        )


# ==========================================
# APAGAR NPC
# ==========================================

@bot.tree.command(
    name="apagar",
    description="Apaga um NPC registrado"
)
@app_commands.describe(
    nome="Nome do NPC que deseja apagar"
)
async def apagar(
    interaction: discord.Interaction,
    nome: str
):

    if not await verificar_permissao(interaction):
        return

    await interaction.response.defer(
        ephemeral=True
    )

    arquivo = procurar_npc(
        nome
    )

    if arquivo is None:

        await interaction.followup.send(
            f"❌ Não encontrei o NPC **{nome}**.",
            ephemeral=True
        )

        return

    caminho_local = os.path.join(
        PASTA_NPCS,
        arquivo
    )

    caminho_github = (
        f"npcs/{arquivo}"
    )

    if os.path.exists(
        caminho_local
    ):

        os.remove(
            caminho_local
        )

    sucesso_github = github_apagar_arquivo(
        caminho_github,
        f"Apagar NPC {nome}"
    )

    if sucesso_github:

        await interaction.followup.send(
            f"🗑️ NPC **{nome}** apagado com sucesso!\n"
            f"☁️ Também removido do GitHub.",
            ephemeral=True
        )

    else:

        await interaction.followup.send(
            f"⚠️ NPC **{nome}** foi apagado localmente, "
            f"mas houve erro ao apagar do GitHub.",
            ephemeral=True
        )


# ==========================================
# LISTAR NPCS
# ==========================================

@bot.tree.command(
    name="npcs",
    description="Lista todos os NPCs registrados"
)
async def npcs(
    interaction: discord.Interaction
):

    if not await verificar_permissao(interaction):
        return

    lista = []

    for arquivo in os.listdir(
        PASTA_NPCS
    ):

        nome, extensao = os.path.splitext(
            arquivo
        )

        if extensao.lower() in EXTENSOES_PERMITIDAS:

            lista.append(
                nome.title()
            )

    if not lista:

        await interaction.response.send_message(
            "📭 Nenhum NPC registrado.",
            ephemeral=True
        )

        return

    lista.sort()

    texto = "\n".join(
        f"• {npc}"
        for npc in lista
    )

    await interaction.response.send_message(
        f"📜 **NPCs registrados:**\n\n{texto}",
        ephemeral=True
    )


# ==========================================
# DETECTAR NPC NAS MENSAGENS
# ==========================================

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    texto = message.content.lower()

    for arquivo in os.listdir(
        PASTA_NPCS
    ):

        nome_npc, extensao = os.path.splitext(
            arquivo
        )

        if extensao.lower() not in EXTENSOES_PERMITIDAS:
            continue

        padrao = (
            rf"\b{re.escape(nome_npc.lower())}\b"
        )

        if re.search(
            padrao,
            texto
        ):

            caminho = os.path.join(
                PASTA_NPCS,
                arquivo
            )

            await message.channel.send(
                file=discord.File(caminho)
            )

            break


# ==========================================
# INICIAR BOT
# ==========================================

if DISCORD_TOKEN is None:

    print(
        "ERRO: DISCORD_TOKEN não encontrado no .env"
    )

elif GITHUB_TOKEN is None:

    print(
        "ERRO: GITHUB_TOKEN não encontrado no .env"
    )

elif GITHUB_REPO is None:

    print(
        "ERRO: GITHUB_REPO não encontrado no .env"
    )

else:

    bot.run(
        DISCORD_TOKEN
    )