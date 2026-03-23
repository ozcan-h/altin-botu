import discord
from discord.ext import commands
import aiohttp
import os

TOKEN = os.environ.get("TOKEN")
PREFIX = "!"

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)


async def altin_fiyatlari_cek():
    url = "https://api.genelpara.com/json/?list=altin&sembol=GA,C,Y,T,GAG,XAUUSD"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                return None
            veri = await resp.json(content_type=None)

    hedefler = {
        "Gram Altın":      "GA",
        "Çeyrek Altın":    "C",
        "Yarım Altın":     "Y",
        "Tam Altın":       "T",
        "Has Altın":       "GAG",
        "Altın ONS (USD)": "XAUUSD",
    }

    sonuclar = {}
    for isim, anahtar in hedefler.items():
        if anahtar in veri:
            alis  = veri[anahtar].get("alis", "?")
            satis = veri[anahtar].get("satis", "?")
            sonuclar[isim] = {"alis": alis, "satis": satis}

    return sonuclar if sonuclar else None


def embed_olustur(fiyatlar):
    embed = discord.Embed(
        title="🥇 Güncel Altın Fiyatları",
        color=0xFFD700,
    )

    emojiler = {
        "Gram Altın":      "🔸",
        "Çeyrek Altın":    "🔹",
        "Yarım Altın":     "💛",
        "Tam Altın":       "🏆",
        "Has Altın":       "✨",
        "Altın ONS (USD)": "🌍",
    }

    if not fiyatlar:
        embed.description = "❌ Fiyatlar alınamadı. Lütfen biraz sonra tekrar dene."
        return embed

    for isim, deger in fiyatlar.items():
        emoji = emojiler.get(isim, "•")
        para_birimi = "$" if "USD" in isim else "₺"
        embed.add_field(
            name=f"{emoji} {isim}",
            value=f"Alış: **{deger['alis']} {para_birimi}**\nSatış: **{deger['satis']} {para_birimi}**",
            inline=True,
        )

    embed.set_footer(text="Kaynak: genelpara.com | Fiyatlar bilgi amaçlıdır.")
    return embed


@bot.event
async def on_ready():
    print(f"✅ Bot açıldı: {bot.user}")


@bot.command(name="altin", aliases=["gold", "fiyat"])
async def altin_komutu(ctx):
    yukle = await ctx.send("⏳ Fiyatlar alınıyor...")
    fiyatlar = await altin_fiyatlari_cek()
    embed = embed_olustur(fiyatlar)
    await yukle.edit(content=None, embed=embed)


bot.run(TOKEN)
