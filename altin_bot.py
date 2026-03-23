import discord
from discord.ext import commands
import aiohttp
from bs4 import BeautifulSoup
import asyncio

# ============================================================
#  BOT AYARLARI - Buraya kendi token'ını yaz
# ============================================================
TOKEN = "BURAYA_BOT_TOKENINI_YAZ"
PREFIX = "!"
# ============================================================

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

async def altin_fiyatlari_cek():
    """Altın fiyatlarını bigpara.com'dan çeker."""
    url = "https://bigpara.hurriyet.com.tr/altin/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                return None
            html = await resp.text()

    soup = BeautifulSoup(html, "html.parser")

    hedefler = {
        "Gram Altın":       "ALTIN",
        "Çeyrek Altın":     "CEYREK_ALTIN",
        "Yarım Altın":      "YARIM_ALTIN",
        "Tam Altın":        "TAM_ALTIN",
        "Altın ONS (USD)":  "ALTIN_ONS",
    }

    sonuclar = {}

    satirlar = soup.select("tr")
    for satir in satirlar:
        hucreler = satir.find_all("td")
        if len(hucreler) < 4:
            continue
        ad = hucreler[0].get_text(strip=True)
        for gosterim_adi, anahtar in hedefler.items():
            if anahtar in ad.upper().replace(" ", "_").replace("Ç", "C").replace("Ş", "S").replace("Ğ", "G").replace("İ", "I").replace("Ö", "O").replace("Ü", "U") or gosterim_adi.upper() in ad.upper():
                alis  = hucreler[1].get_text(strip=True)
                satis = hucreler[2].get_text(strip=True)
                sonuclar[gosterim_adi] = {"alis": alis, "satis": satis}

    # Eğer scraping çalışmazsa yedek API dene
    if not sonuclar:
        sonuclar = await altin_yedek_api()

    return sonuclar


async def altin_yedek_api():
    """Yedek: collectapi.com altın endpoint (ücretsiz tier)"""
    url = "https://api.collectapi.com/economy/goldPrice"
    # Ücretsiz ve API key gerektirmeyen alternatif
    url2 = "https://finans.truncgil.com/today.json"
    
    hedef_map = {
        "gram-altin":      "Gram Altın",
        "ceyrek-altin":    "Çeyrek Altın",
        "yarim-altin":     "Yarım Altın",
        "tam-altin":       "Tam Altın",
        "altin-ons":       "Altın ONS (USD)",
    }

    sonuclar = {}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url2) as resp:
                if resp.status == 200:
                    veri = await resp.json(content_type=None)
                    for anahtar, gosterim in hedef_map.items():
                        if anahtar in veri:
                            alis  = veri[anahtar].get("Alış", "?")
                            satis = veri[anahtar].get("Satış", "?")
                            sonuclar[gosterim] = {"alis": alis, "satis": satis}
    except Exception:
        pass

    return sonuclar


def embed_olustur(fiyatlar: dict) -> discord.Embed:
    embed = discord.Embed(
        title="🥇 Güncel Altın Fiyatları",
        color=0xFFD700,
    )

    emojiler = {
        "Gram Altın":      "🔸",
        "Çeyrek Altın":    "🔹",
        "Yarım Altın":     "💛",
        "Tam Altın":       "🏆",
        "Altın ONS (USD)": "🌍",
    }

    if not fiyatlar:
        embed.description = "❌ Fiyatlar alınamadı. Lütfen biraz sonra tekrar dene."
        return embed

    for isim, deger in fiyatlar.items():
        emoji = emojiler.get(isim, "•")
        embed.add_field(
            name=f"{emoji} {isim}",
            value=f"Alış: **{deger['alis']} ₺**\nSatış: **{deger['satis']} ₺**",
            inline=True,
        )

    embed.set_footer(text="Kaynak: bigpara.hurriyet.com.tr | Fiyatlar bilgi amaçlıdır.")
    return embed


@bot.event
async def on_ready():
    print(f"✅ Bot açıldı: {bot.user} (ID: {bot.user.id})")
    print(f"   Komut prefix: {PREFIX}")
    print("   Komutlar: !altin  |  !altin yardim")


@bot.command(name="altin", aliases=["gold", "fiyat"])
async def altin_komutu(ctx, alt: str = None):
    """Altın fiyatlarını gösterir. Kullanım: !altin"""

    if alt == "yardim":
        yardim = discord.Embed(
            title="📖 Yardım",
            description=(
                "**!altin** → Tüm altın fiyatlarını gösterir\n"
                "**!altin yardim** → Bu yardım mesajını gösterir\n\n"
                "Kısayollar: `!gold`, `!fiyat`"
            ),
            color=0xFFD700,
        )
        await ctx.send(embed=yardim)
        return

    # Yükleniyor mesajı
    yukle = await ctx.send("⏳ Fiyatlar alınıyor...")

    try:
        fiyatlar = await asyncio.wait_for(altin_fiyatlari_cek(), timeout=10)
    except asyncio.TimeoutError:
        fiyatlar = None

    embed = embed_olustur(fiyatlar)
    await yukle.edit(content=None, embed=embed)


bot.run(TOKEN)
