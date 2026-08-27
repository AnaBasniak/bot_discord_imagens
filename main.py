import discord
from discord import app_commands
import os
import re
from dotenv import load_dotenv


# ==========================================
# CONFIGURAÇÕES
# ==========================================

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

PASTA_NPCS = "npcs"

# SEU ID DO DISCORD
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
# BOT CONECTADO
# ==========================================

@bot.event
async def on_ready():

    print("=" * 40)
    print(f"Bot conectado como {bot.user}")
    print("=" * 40)


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

    nome_limpo = limpar_nome(nome)

    extensao = os.path.splitext(
        imagem.filename
    )[1].lower()

    if extensao not in EXTENSOES_PERMITIDAS:

        await interaction.response.send_message(
            "❌ A imagem precisa ser PNG, JPG, JPEG ou WEBP.",
            ephemeral=True
        )

        return

    if procurar_npc(nome) is not None:

        await interaction.response.send_message(
            f"❌ O NPC **{nome}** já está registrado.\n"
            f"Use `/editar` para fazer alterações.",
            ephemeral=True
        )

        return

    caminho = os.path.join(
        PASTA_NPCS,
        nome_limpo + extensao
    )

    await imagem.save(caminho)

    await interaction.response.send_message(
        f"✅ NPC **{nome}** registrado com sucesso!"
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
    novo_nome="Novo nome do NPC (opcional)",
    nova_imagem="Nova imagem do NPC (opcional)"
)
async def editar(
    interaction: discord.Interaction,
    nome_atual: str,
    novo_nome: str = None,
    nova_imagem: discord.Attachment = None
):

    if not await verificar_permissao(interaction):
        return

    # Procura NPC atual
    arquivo_antigo = procurar_npc(nome_atual)

    if arquivo_antigo is None:

        await interaction.response.send_message(
            f"❌ O NPC **{nome_atual}** não está registrado.",
            ephemeral=True
        )

        return

    # Precisa alterar alguma coisa
    if novo_nome is None and nova_imagem is None:

        await interaction.response.send_message(
            "❌ Você precisa informar um novo nome, "
            "uma nova imagem ou os dois.",
            ephemeral=True
        )

        return

    nome_antigo_arquivo, extensao_antiga = os.path.splitext(
        arquivo_antigo
    )

    # ======================================
    # NOVO NOME
    # ======================================

    if novo_nome is not None:

        nome_final = limpar_nome(novo_nome)

        # Verifica se já existe outro NPC com esse nome
        npc_com_novo_nome = procurar_npc(novo_nome)

        if (
            npc_com_novo_nome is not None
            and limpar_nome(novo_nome) != limpar_nome(nome_atual)
        ):

            await interaction.response.send_message(
                f"❌ Já existe um NPC chamado **{novo_nome}**.",
                ephemeral=True
            )

            return

    else:

        nome_final = limpar_nome(nome_atual)

    # ======================================
    # NOVA IMAGEM
    # ======================================

    if nova_imagem is not None:

        extensao_final = os.path.splitext(
            nova_imagem.filename
        )[1].lower()

        if extensao_final not in EXTENSOES_PERMITIDAS:

            await interaction.response.send_message(
                "❌ A imagem precisa ser PNG, JPG, JPEG ou WEBP.",
                ephemeral=True
            )

            return

    else:

        extensao_final = extensao_antiga

    # ======================================
    # CAMINHOS
    # ======================================

    caminho_antigo = os.path.join(
        PASTA_NPCS,
        arquivo_antigo
    )

    caminho_novo = os.path.join(
        PASTA_NPCS,
        nome_final + extensao_final
    )

    # ======================================
    # SE TEM NOVA IMAGEM
    # ======================================

    if nova_imagem is not None:

        # Apaga imagem antiga
        os.remove(caminho_antigo)

        # Salva nova imagem
        await nova_imagem.save(caminho_novo)

    # ======================================
    # SE MUDOU APENAS O NOME
    # ======================================

    elif caminho_antigo != caminho_novo:

        os.rename(
            caminho_antigo,
            caminho_novo
        )

    # ======================================
    # RESPOSTA
    # ======================================

    alteracoes = []

    if novo_nome is not None:

        alteracoes.append(
            f"📝 Nome: **{nome_atual}** → **{novo_nome}**"
        )

    if nova_imagem is not None:

        alteracoes.append(
            "🖼️ Imagem atualizada"
        )

    texto_alteracoes = "\n".join(alteracoes)

    await interaction.response.send_message(
        f"✏️ **NPC atualizado com sucesso!**\n\n"
        f"{texto_alteracoes}"
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

    arquivo = procurar_npc(nome)

    if arquivo is None:

        await interaction.response.send_message(
            f"❌ Não encontrei o NPC **{nome}**.",
            ephemeral=True
        )

        return

    caminho = os.path.join(
        PASTA_NPCS,
        arquivo
    )

    os.remove(caminho)

    await interaction.response.send_message(
        f"🗑️ NPC **{nome}** apagado com sucesso!"
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

    for arquivo in os.listdir(PASTA_NPCS):

        nome, extensao = os.path.splitext(arquivo)

        if extensao.lower() in EXTENSOES_PERMITIDAS:
            lista.append(nome.title())

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

    # Ignora mensagens de bots
    if message.author.bot:
        return

    texto = message.content.lower()

    for arquivo in os.listdir(PASTA_NPCS):

        nome_npc, extensao = os.path.splitext(
            arquivo
        )

        if extensao.lower() not in EXTENSOES_PERMITIDAS:
            continue

        # Reconhece o nome como palavra inteira
        padrao = rf"\b{re.escape(nome_npc.lower())}\b"

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

if TOKEN is None:

    print(
        "ERRO: Token não encontrado no arquivo .env"
    )

else:

    bot.run(TOKEN)