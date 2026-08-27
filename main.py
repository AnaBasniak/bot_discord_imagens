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
# FUNÇÃO PARA NORMALIZAR NOME
# ==========================================

def limpar_nome(nome):
    return nome.lower().strip()


# ==========================================
# REGISTRAR NPC
# ==========================================

@bot.tree.command(
    name="registrar",
    description="Registra um NPC e sua imagem"
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

    extensao = os.path.splitext(imagem.filename)[1].lower()

    extensoes_permitidas = [
        ".png",
        ".jpg",
        ".jpeg",
        ".webp"
    ]

    if extensao not in extensoes_permitidas:

        await interaction.response.send_message(
            "❌ A imagem precisa ser PNG, JPG, JPEG ou WEBP.",
            ephemeral=True
        )

        return

    nome_limpo = limpar_nome(nome)

    # Remove arquivo antigo caso o NPC já exista
    for arquivo in os.listdir(PASTA_NPCS):

        nome_existente, _ = os.path.splitext(arquivo)

        if nome_existente.lower() == nome_limpo:

            caminho_antigo = os.path.join(
                PASTA_NPCS,
                arquivo
            )

            os.remove(caminho_antigo)

    caminho = os.path.join(
        PASTA_NPCS,
        nome_limpo + extensao
    )

    await imagem.save(caminho)

    await interaction.response.send_message(
        f"✅ NPC **{nome}** registrado com sucesso!"
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

    for arquivo in os.listdir(PASTA_NPCS):

        nome_arquivo, _ = os.path.splitext(arquivo)

        if nome_arquivo.lower() == nome_limpo:

            caminho = os.path.join(
                PASTA_NPCS,
                arquivo
            )

            os.remove(caminho)

            await interaction.response.send_message(
                f"🗑️ NPC **{nome}** apagado."
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
async def npcs(interaction: discord.Interaction):

    lista = []

    for arquivo in os.listdir(PASTA_NPCS):

        nome, extensao = os.path.splitext(arquivo)

        if extensao.lower() in [
            ".png",
            ".jpg",
            ".jpeg",
            ".webp"
        ]:
            lista.append(nome.title())

    if not lista:

        await interaction.response.send_message(
            "📭 Nenhum NPC registrado."
        )

        return

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

    if message.author.bot:
        return

    texto = message.content.lower()

    for arquivo in os.listdir(PASTA_NPCS):

        nome_npc, extensao = os.path.splitext(arquivo)

        if extensao.lower() not in [
            ".png",
            ".jpg",
            ".jpeg",
            ".webp"
        ]:
            continue

        # Verifica o nome como palavra inteira
        padrao = rf"\b{re.escape(nome_npc.lower())}\b"

        if re.search(padrao, texto):

            caminho = os.path.join(
                PASTA_NPCS,
                arquivo
            )

            await message.channel.send(
                file=discord.File(caminho)
            )

            # Evita mandar várias imagens na mesma mensagem
            break


# ==========================================
# INICIAR BOT
# ==========================================

if TOKEN is None:
    print("ERRO: Token não encontrado no arquivo .env")
else:
    bot.run(TOKEN)
