import os
import time
import asyncio
import aiohttp
import uuid
import subprocess
import logging
from flask import Flask, jsonify
from threading import Thread
import yt_dlp
from shazamio import Shazam
from pyrogram import Client, filters
from pyrogram.types import InputMediaPhoto

# --- ١. ڕێکخستنی سێرڤەری Keep-Alive ---
flask_app = Flask('')

@flask_app.route('/')
def home():
    return jsonify({"status": "ok", "bot": "Ultra Fast Bot by Aryas Dev"}), 200

def run_flask():
    flask_app.run(host='0.0.0.0', port=5000, threaded=True)

def keep_alive():
    t = Thread(target=run_flask, daemon=True)
    t.start()

# --- ٢. ڕێکخستنی زانیارییەکانی بۆت و API ---
logging.basicConfig(level=logging.ERROR)

# 👈 لە شوێنی تۆکنە ئەسڵییەکان ئەمە بنووسە:
API_ID = int(os.getenv("API_ID", "30998734"))                          
API_HASH = os.getenv("API_HASH", "c5a99d91c4050805fd73a699fac7a952")            
BOT_TOKEN = os.getenv("BOT_TOKEN") # 🚨 تۆکنەکە بە ئاشکرا لێرە مەنووسە!

GROQ_KEY = os.getenv("GROQ_KEY")   # 🚨 کلیدی Groq بە ئاشکرا مەنووسە!


app = Client(
    "fast_downloader_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=20
)

http_session = None

async def get_http_session():
    global http_session
    if http_session is None or http_session.closed:
        http_session = aiohttp.ClientSession()
    return http_session

# --- ٣. بەشی زیرەکی دەستکرد (AI) بە فلتەری Aryas Dev و کوردیی دروست ---
async def ask_ai(prompt):
    user_prompt_lower = prompt.lower().strip()
    
    identity_keywords = [
        "کێی", "کێت", "ناوی", "دروست", "گەشەپێدەر", "خاوەن", "دروستکراوی", 
        "کێ دروستی", "کێ تۆی", "کێ گەشەی", "ناوی تۆ", "تۆ کێیت"
    ]
    
    if any(keyword in user_prompt_lower for keyword in identity_keywords):
        return (
            "🤖 **سڵاو! من یاریدەدەرێکی زیرەکی دەستکردم.**\n\n"
            "👨‍💻 **دروستکەر و گەشەپێدەری من:**\n"
            "من لەلایەن **Aryas Dev** دروستکراوم و پەرەم پێدراوە؛ کە گەشەپێدەرێکی زۆر شارەزایە لە بواری تەکنەلۆژیا، "
            "پرۆگرامسازی، و دروستکردنی سیستەم و بۆتەکانی زیرەکی دەستکرد (AI).\n\n"
            "✨ ئامانجم ئەوەیە لە هەموو بواری داگرتنی میدیا و وەڵامدانەوەی پرسیارەکانت بە باشترین شێوە هاوکاریت بکەم!"
        )

    if not GROQ_KEY or not GROQ_KEY.startswith("gsk_"):
        return "🤖 سیستەمی زیرەکی دەستکرد چالاک نەکراوە."
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    system_prompt = (
        "تۆ یاریدەدەرێکی زیرەکی زۆر لێهاتووی تەلیگرامیت. "
        "مەرجی بنەڕەتی: پێویستە هەمیشە بە زمانی کوردیی سۆرانیی بنووسیت. "
        "نابێت وشەی نامۆ یان وەرگێڕانی وشەبەوشەی عەرەبی و ئینگلیزی بەکاربهێنیت. "
        "ڕێزمانی کوردی بپارێزە: بەکارهێنانی پیتی (ڵ، ڕ، ێ، ۆ، ێک) بە دروستی. "
        "وەڵامەکانت با هاوڕێیانە، کورت، سادە و ڕەوان بن.\n\n"
        "نموونەی وەڵامدانەوە بە کوردیی زۆر ڕاست:\n"
        "پرسیا‌ر: چۆن دەتوانی یاررمەتیم بدەیت؟\n"
        "وەڵام: سڵاو! من دەتوانم لەم بوارانەدا هاوکاریت بکەم:\n"
        "• وەڵامدانەوەی پرسیارەکانت بە کوردیی ڕەوان\n"
        "• داگرتنی ڤیدیۆ و وێنەی تیکتۆک و یوتوب\n"
        "• دۆزینەوەی ناوی گۆرانییەکان\n"
        "هەر پرسیارێکیت هەیە بپرسە، بە خۆشحاڵییەوە وەڵام دەدمەوە!"
    )
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }
    
    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        session = await get_http_session()
        async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as resp:
            if resp.status == 200:
                res_json = await resp.json()
                try:
                    return res_json['choices'][0]['message']['content']
                except KeyError:
                    return "❌ نەمتوانی وەڵام لە سیستەمەوە دەربهێنم."
            else:
                return f"❌ کێشەیەک لە API هەیە (کۆد: {resp.status})."
    except Exception as e:
        print(f"AI Error: {e}")
        return "❌ ببوورە، کێشەیەک لە پەیوەندی بە زیرەکی دەستکرددا ڕوویدا."

# --- ٤. دروستکردنی هێڵی پێشکەوتن (Progress Bar) ---
def create_progress_bar(current, total):
    if total == 0:
        return "%0", "[░░░░░░░░░░]"
    percentage = min(100, max(0, int((current / total) * 100)))
    filled = int(percentage / 10)
    bar = "▓" * filled + "░" * (10 - filled)
    return f"%{percentage}", f"[{bar}]"

last_update_tracker = {}

async def pyrogram_progress(current, total, message, action_title):
    msg_id = message.id
    now = time.time()
    
    if msg_id in last_update_tracker and (now - last_update_tracker[msg_id]) < 3 and current < total:
        return
        
    last_update_tracker[msg_id] = now
    pct_str, bar_str = create_progress_bar(current, total)
    
    text = f"📤 **{action_title}**\n\n**{bar_str} {pct_str}**"
    try:
        await message.edit_text(text)
    except Exception:
        pass

# --- ٥. دەرهێنانی دەنگی خێرا بە FFmpeg ---
async def extract_audio_fast(input_file_or_url, output_mp3):
    try:
        cmd = [
            'ffmpeg', '-y',
            '-threads', '0',
            '-i', input_file_or_url,
            '-vn',
            '-c:a', 'libmp3lame',
            '-q:a', '4',
            output_mp3
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        await proc.wait()
        return os.path.exists(output_mp3) and os.path.getsize(output_mp3) > 5000
    except Exception:
        return False

# --- ٦. بڕینی sample بۆ Shazam ---
async def extract_shazam_sample(input_file, output_sample):
    try:
        cmd = [
            'ffmpeg', '-y',
            '-threads', '0',
            '-ss', '00:00:03',
            '-i', input_file,
            '-t', '10',
            '-vn', '-ac', '1', '-ar', '22050',
            output_sample
        ]
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        await proc.wait()
        return os.path.exists(output_sample)
    except Exception:
        return False

# --- ٧. نیشانەی Shazam ---
async def recognize_song(filepath):
    sample_path = f"sample_{uuid.uuid4()}.wav"
    try:
        shazam = Shazam()
        has_sample = await extract_shazam_sample(filepath, sample_path)
        target_file = sample_path if has_sample else filepath

        if hasattr(shazam, 'recognize'):
            out = await shazam.recognize(target_file)
        else:
            out = await shazam.recognize_song(target_file)

        track = out.get('track', {})
        if track:
            title = track.get('title', '')
            artist = track.get('subtitle', '')
            if title and artist:
                return f"{title} - {artist}"
            elif title:
                return title
        return None
    except Exception:
        return None
    finally:
        if os.path.exists(sample_path):
            try: os.remove(sample_path)
            except: pass

# --- ٨. داگرتنی تیکتۆک (کۆدەکە بە زانیاری تەواوی کوردی) ---
async def download_tiktok(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    api_url = f"https://www.tikwm.com/api/?url={url}"
    try:
        session = await get_http_session()
        async with session.get(api_url, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as resp:
            if resp.status == 200:
                res = await resp.json()
                if res.get("code") == 0:
                    data = res["data"]
                    is_photo = "images" in data
                    audio_link = data.get("music")
                    info = {
                        "username": data["author"].get("unique_id") or data["author"].get("nickname"),
                        "region": data.get("region", "دیاری نەکراو"),
                        "views": data.get("play_count", 0),
                        "comments": data.get("comment_count", 0),
                        "shares": data.get("share_count", 0),
                        "duration": data.get("duration", 0),
                        "is_photo": is_photo
                    }
                    media_links = data["images"] if is_photo else (data.get("hdplay") or data.get("play"))
                    return media_links, audio_link, info
        return None, None, None
    except Exception:
        return None, None, None

# --- ٩. داگرتنی یوتوب ---
async def download_youtube(url, message, loop):
    file_id = str(uuid.uuid4())
    out_video_path = f"yt_vid_{file_id}.mp4"

    def yt_progress_hook(d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            current = d.get('downloaded_bytes', 0)
            now = time.time()
            
            msg_id = message.id
            if msg_id in last_update_tracker and (now - last_update_tracker[msg_id]) < 3 and current < total:
                return
                
            last_update_tracker[msg_id] = now
            pct_str, bar_str = create_progress_bar(current, total)
            text = f"⚡ **خەریکی داونلۆدکردنی ڤیدیۆی یوتوبم...**\n\n**{bar_str} {pct_str}**"
            
            async def _update_msg():
                try:
                    await message.edit_text(text)
                except Exception:
                    pass

            asyncio.run_coroutine_threadsafe(_update_msg(), loop)

    ydl_opts = {
        'format': '18/b[ext=mp4]/best',
        'outtmpl': out_video_path,
        'quiet': True,
        'no_warnings': True,
        'noprogress': True,
        'concurrent_fragment_downloads': 16,
        'buffersize': 2097152,
        'progress_hooks': [yt_progress_hook],
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web']
            }
        }
    }

    def _download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'YouTube Video')
            uploader = info.get('uploader', 'YouTube')
            return out_video_path, title, uploader

    try:
        return await loop.run_in_executor(None, _download)
    except Exception as e:
        print(f"YouTube Download Error: {e}")
        return None, None, None

# --- ١٠. دەستکاریکردنی فەرمانەکان ---
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    await message.reply_text(
        "👋🏼 سڵاو! بەخێربێیت بۆ بۆتی خێرا.\n\n"
        "✨ دەتوانیت هەر پرسیارێک داری لێم بپرسیت تا بە AI وەڵامت بدمەوە.\n"
        "📥 یان لینکی TikTok و YouTube بنێرە تا بۆت دابەزێنم بەبەرزترین خێرایی."
    )

@app.on_message(filters.text & filters.private & ~filters.command("start"))
async def handle_messages(client, message):
    text = message.text.strip()
    loop = asyncio.get_event_loop()

    # ---- بەشی تیکتۆک ----
    if "tiktok.com" in text:
        wait_msg = await message.reply_text("⏳ **خەریکی دابەزاندنم...**")
        media_data, audio_url, info = await download_tiktok(text)

        if media_data:
            temp_raw = None
            temp_clean = None

            try:
                await wait_msg.edit_text("🔍 **خەریکی دۆزینەوەی ناوی گۆرانیەکەم...**")

                temp_clean = f"clean_{uuid.uuid4()}.mp3"
                audio_ready = False

                if audio_url:
                    temp_raw = f"raw_{uuid.uuid4()}.tmp"
                    try:
                        session = await get_http_session()
                        async with session.get(audio_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=aiohttp.ClientTimeout(total=8)) as r:
                            if r.status == 200:
                                content = await r.read()
                                if len(content) > 5000:
                                    with open(temp_raw, 'wb') as f:
                                        f.write(content)
                                    audio_ready = await extract_audio_fast(temp_raw, temp_clean)
                    except Exception:
                        pass

                if not audio_ready and not info["is_photo"] and media_data:
                    audio_ready = await extract_audio_fast(media_data, temp_clean)

                song_name = None
                if audio_ready and os.path.exists(temp_clean):
                    song_name = await recognize_song(temp_clean)

                caption = (
                    f" - ناوی ئەکاونت : {info['username']}\n\n"
                    f" - وڵاتی ئەکاونت : {info['region']}\n\n"
                    f" - ژمارەی بینەران : {info['views']}\n"
                    f" - ژمارەی کۆمێنتەکان : {info['comments']}\n"
                    f" - ژمارەی هاوبەشکردن : {info['shares']}\n"
                    f" - کاتی ڤیدیۆ : {info['duration']} چڕکە"
                )
                if song_name:
                    caption += f"\n\n🎵 ناوی گۆرانی : **{song_name}**"
                caption += "\n\n⚙️ @bu404"

                if info["is_photo"]:
                    images = media_data
                    for i in range(0, len(images), 10):
                        chunk = images[i:i+10]
                        media_group = [InputMediaPhoto(chunk[0], caption=caption if i==0 else "")] + [InputMediaPhoto(img) for img in chunk[1:]]
                        await client.send_media_group(message.chat.id, media_group)
                else:
                    await client.send_video(
                        message.chat.id, 
                        media_data, 
                        caption=caption,
                        progress=pyrogram_progress,
                        progress_args=(wait_msg, "خەریکی ئاپلۆدکردنی ڤیدیۆکەم...")
                    )

                await wait_msg.delete()

            except Exception as e:
                print(f"Error in TikTok flow: {e}")
            finally:
                for path in [temp_raw, temp_clean]:
                    if path and os.path.exists(path):
                        try: os.remove(path)
                        except: pass
        else:
            await wait_msg.edit_text("❌ نەمتوانی دابیەزێنم.")

    # ---- بەشی یوتوب (چاککراو: ناردنی ڤیدیۆ پاشان دەنگ بە بەش بەش) ----
    elif "youtube.com" in text or "youtu.be" in text:
        wait_msg = await message.reply_text("📥 **خەریکی داونلۆدکردنی ڤیدیۆ و دەنگی یوتوبەکەم...**")
        video_path, yt_title, uploader = await download_youtube(text, wait_msg, loop)

        if video_path and os.path.exists(video_path):
            temp_clean = f"clean_{uuid.uuid4()}.mp3"
            try:
                caption = f"🎬 : {yt_title}\n👤 : {uploader}\n\n⚙️ @bu404"

                # ١. ئاپلۆدکردنی ڤیدیۆ
                await client.send_video(
                    chat_id=message.chat.id, 
                    video=video_path, 
                    caption=caption,
                    progress=pyrogram_progress,
                    progress_args=(wait_msg, "خەریکی ئاپلۆدکردنی ڤیدیۆی یوتوبەکەم...")
                )

                # ٢. نوێکردنەوەی پەیامەکە بۆ ناردنی دەنگەکە
                await wait_msg.edit_text("⏳ **خەریکی دەرهێنان و ئاپلۆدکردنی دەنگی ڤیدیۆکەم...**")

                # ٣. ئاپلۆدکردنی دەنگەکە
                audio_ready = await extract_audio_fast(video_path, temp_clean)
                if audio_ready and os.path.exists(temp_clean):
                    song_name = await recognize_song(temp_clean)
                    final_song_name = song_name if song_name else yt_title
                    audio_caption = f"🎵 ناوی گۆرانی :\n**{final_song_name}**\n\n🔊 دەنگی سەر پۆستەکە"

                    clean_filename = "".join([c for c in final_song_name if c.isalnum() or c in (' ', '-', '_')]).strip()
                    if not clean_filename:
                        clean_filename = "YouTube_Audio"

                    await client.send_audio(
                        chat_id=message.chat.id,
                        audio=temp_clean,
                        caption=audio_caption,
                        title=final_song_name,
                        performer=uploader,
                        file_name=f"{clean_filename}.mp3"
                    )

                # ٤. سڕینەوەی نامەی وەستان دوای ئەوەی هەردووکی گەیشت
                await wait_msg.delete()

            except Exception as e:
                print(f"YouTube Error: {e}")
                try: await wait_msg.delete()
                except: pass
            finally:
                for path in [video_path, temp_clean]:
                    if path and os.path.exists(path):
                        try: os.remove(path)
                        except: pass
        else:
            await wait_msg.edit_text("❌ نەمتوانی ڤیدیۆی یوتوبەکە دابیەزێنم.")

    # ---- بەشی AI ----
    else:
        status_msg = await message.reply_text("🤔 خەریکم بیر دەکەمەوە...")
        ai_response = await ask_ai(text)
        await status_msg.edit_text(ai_response)

if __name__ == '__main__':
    keep_alive()
    print("🤖 بۆتەکە بە تەواوی پرۆسێسە چاککراوەکانەوە دەستی پێکرد...")
    app.run()
