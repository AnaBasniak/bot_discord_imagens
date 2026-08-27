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

# Cria a pasta caso ela não exista
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
# BOT CONECTADO
# ==========================================

@bot.event
async def on_ready():
    print("=" * 40)
    print(f"Bot conectado como {bot.user}")
    print("=" * 40)


# ==========================================
# FUNÇÃO PARA LIMPAR NOME
# ==========================================

def limpar_nome(nome):
    return nome.lower().strip()


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

    nome_limpo = limpar_nome(nome)

    extensao = os.path.splitext(
        imagem.filename
    )[1].lower()

    # Verifica se é imagem
    if extensao not in EXTENSOES_PERMITIDAS:

        await interaction.response.send_message(
            "❌ A imagem precisa ser PNG, JPG, JPEG ou WEBP.",
            ephemeral=True
        )

        return

    # Verifica se o NPC já existe
    for arquivo in os.listdir(PASTA_NPCS):

        nome_existente, extensao_existente = os.path.splitext(
            arquivo
        )

        if (
            nome_existente.lower() == nome_limpo
            and extensao_existente.lower() in EXTENSOES_PERMITIDAS
        ):

            await interaction.response.send_message(
                f"❌ O NPC **{nome}** já está registrado.\n"
                f"Use `/editar` para trocar a imagem.",
                ephemeral=True
            )

            return

    # Salva a imagem
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
    description="Atualiza a imagem de um NPC"
)
@app_commands.describe(
    nome="Nome do NPC",
    imagem="Nova imagem do NPC"
)
async def editar(
    interaction: discord.Interaction,
    nome: str,
    imagem: discord.Attachment
):

    nome_limpo = limpar_nome(nome)

    nova_extensao = os.path.splitext(
        imagem.filename
    )[1].lower()

    # Verifica se é imagem
    if nova_extensao not in EXTENSOES_PERMITIDAS:

        await interaction.response.send_message(
            "❌ A imagem precisa ser PNG, JPG, JPEG ou WEBP.",
            ephemeral=True
        )

        return

    arquivo_antigo = None

    # Procura o NPC
    for arquivo in os.listdir(PASTA_NPCS):

        nome_arquivo, extensao = os.path.splitext(
            arquivo
        )

        if (
            nome_arquivo.lower() == nome_limpo
            and extensao.lower() in EXTENSOES_PERMITIDAS
        ):

            arquivo_antigo = arquivo
            break

    # NPC não existe
    if arquivo_antigo is None:

        await interaction.response.send_message(
            f"❌ O NPC **{nome}** não está registrado.",
            ephemeral=True
        )

        return

    # Apaga imagem antiga
    caminho_antigo = os.path.join(
        PASTA_NPCS,
        arquivo_antigo
    )

    os.remove(caminho_antigo)

    # Salva imagem nova
    novo_caminho = os.path.join(
        PASTA_NPCS,
        nome_limpo + nova_extensao
    )

    await imagem.save(novo_caminho)

    await interaction.response.send_message(
        f"✏️ Imagem do NPC **{nome}** atualizada com sucesso!"
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

    nome_limpo = limpar_nome(nome)

    # Procura o NPC
    for arquivo in os.listdir(PASTA_NPCS):

        nome_arquivo, extensao = os.path.splitext(
            arquivo
        )

        if (
            nome_arquivo.lower() == nome_limpo
            and extensao.lower() in EXTENSOES_PERMITIDAS
        ):

            caminho = os.path.join(
                PASTA_NPCS,
                arquivo
            )

            os.remove(caminho)

            await interaction.response.send_message(
                f"🗑️ NPC **{nome}** apagado com sucesso!"
            )

            return

    await interaction.response.send_message(
        f"❌ Não encontrei o NPC **{nome}**.",
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

    lista = []

    # Procura todos os NPCs
    for arquivo in os.listdir(PASTA_NPCS):

        nome, extensao = os.path.splitext(
            arquivo
        )

        if extensao.lower() in EXTENSOES_PERMITIDAS:

            lista.append(
                nome.title()
            )

    # Nenhum NPC
    if not lista:

        await interaction.response.send_message(
            "📭 Nenhum NPC registrado."
        )

        return

    # Organiza alfabeticamente
    lista.sort()

    texto = "\n".join(
        f"• {npc}"
        for npc in lista
    )

    await interaction.response.send_message(
        f"📜 **NPCs registrados:**\n\n{texto}"
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

    # Procura os NPCs registrados
    for arquivo in os.listdir(PASTA_NPCS):

        nome_npc, extensao = os.path.splitext(
            arquivo
        )

        if extensao.lower() not in EXTENSOES_PERMITIDAS:
            continue

        # Procura o nome como palavra inteira
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

            # Manda somente uma imagem por mensagem
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