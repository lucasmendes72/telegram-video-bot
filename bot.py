import os
import sys
import re
import logging
import aiohttp
import asyncio
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Token do bot - LEITURA SEGURA DA VARIÁVEL DE AMBIENTE
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# Verificação de segurança
if not BOT_TOKEN:
    logger.error("❌ ERRO CRÍTICO: BOT_TOKEN não encontrado!")
    logger.error("Configure a variável de ambiente BOT_TOKEN no Railway:")
    logger.error("1. Vá em 'Variables'")
    logger.error("2. Adicione: BOT_TOKEN = seu_token_do_botfather")
    sys.exit(1)

logger.info("✅ Token carregado com sucesso!")

# URLs das APIs
TIKWM_API = 'https://www.tikwm.com/api/'

class VideoDownloader:
    """Classe para gerenciar downloads de vídeos do TikTok e Shopee"""
    
    def __init__(self):
        self.session = None
    
    async def get_session(self):
        """Retorna uma sessão aiohttp reutilizável"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=60)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def close(self):
        """Fecha a sessão"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def extract_tiktok_url(self, text):
        """Extrai URL do TikTok do texto"""
        patterns = [
            r'https?://(?:www\.)?tiktok\.com/@[\w.-]+/video/\d+',
            r'https?://(?:vm|vt)\.tiktok\.com/[\w]+',
            r'https?://(?:www\.)?tiktok\.com/t/[\w]+',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None
    
    def extract_shopee_url(self, text):
        """Extrai URL do Shopee do texto"""
        patterns = [
            r'https?://(?:www\.)?(?:br|mx|cl|co|id|ph|sg|my|th|tw|vn)\.shp\.ee/[\w?=&./-]+',
            r'https?://(?:shopee\.com\.br|shopee\.com\.mx|shopee\.cl|shopee\.co)/[\w.?=&/-]+',
            r'https?://shp\.ee/[\w?=&./-]+',
            r'https?://(?:video|vod)\.shopee\.com\.br/[\w.?=&/-]+',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None
    
    async def download_tiktok(self, url):
        """Baixa vídeo do TikTok sem marca d'água"""
        try:
            session = await self.get_session()
            
            # Faz requisição para a API do TikWM
            params = {'url': url, 'hd': 1}
            async with session.post(TIKWM_API, data=params) as response:
                if response.status != 200:
                    return None, "Erro ao acessar API do TikTok"
                
                data = await response.json()
                
                if data.get('code') != 0:
                    return None, "Não foi possível processar o vídeo do TikTok"
                
                video_data = data.get('data', {})
                
                # Tenta pegar o vídeo em HD primeiro, depois SD
                video_url = video_data.get('hdplay') or video_data.get('play')
                
                if not video_url:
                    return None, "URL do vídeo não encontrada"
                
                # Baixa o vídeo
                async with session.get(video_url) as video_response:
                    if video_response.status == 200:
                        video_bytes = await video_response.read()
                        
                        # Informações adicionais
                        info = {
                            'title': video_data.get('title', ''),
                            'author': video_data.get('author', {}).get('unique_id', ''),
                            'duration': video_data.get('duration', 0),
                            'size': len(video_bytes)
                        }
                        
                        return video_bytes, info
                    else:
                        return None, "Erro ao baixar o vídeo"
        
        except Exception as e:
            logger.error(f"Erro ao baixar TikTok: {e}")
            return None, f"Erro: {str(e)}"
    
    async def resolve_short_url(self, url):
        """Resolve URLs curtas da Shopee (shp.ee, br.shp.ee)"""
        try:
            session = await self.get_session()
            async with session.get(url, allow_redirects=True) as response:
                return str(response.url)
        except:
            return url
    
    async def download_shopee(self, url):
        """Baixa vídeo do Shopee tentando obter versão sem marca d'água"""
        try:
            session = await self.get_session()
            
            # Resolve URLs curtas primeiro
            if 'shp.ee' in url:
                url = await self.resolve_short_url(url)
                logger.info(f"URL resolvida: {url}")
            
            # Extrai item_id e shop_id da URL
            item_match = re.search(r'[.-]i\.(\d+)\.(\d+)', url)
            if not item_match:
                return None, "Não foi possível extrair ID do produto da URL"
            
            shop_id = item_match.group(1)
            item_id = item_match.group(2)
            
            logger.info(f"Shop ID: {shop_id}, Item ID: {item_id}")
            
            # Tenta API pública da Shopee (sem autenticação)
            # Este endpoint é usado internamente pela Shopee
            api_url = f"https://shopee.com.br/api/v4/item/get"
            
            params = {
                'itemid': item_id,
                'shopid': shop_id
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': url,
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            async with session.get(api_url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    item_data = data.get('data', {}).get('item', {})
                    if not item_data:
                        item_data = data.get('item', {})
                    
                    # Procura por vídeo nos dados
                    video_info = item_data.get('video_info_list', [])
                    if video_info and len(video_info) > 0:
                        video_data = video_info[0]
                        
                        # Tenta diferentes campos de URL
                        video_url = (
                            video_data.get('default_format', {}).get('url') or
                            video_data.get('url') or
                            video_data.get('video_url')
                        )
                        
                        if video_url:
                            # Algumas vezes a URL vem sem protocolo
                            if video_url.startswith('//'):
                                video_url = 'https:' + video_url
                            elif not video_url.startswith('http'):
                                video_url = 'https://' + video_url
                            
                            logger.info(f"URL do vídeo encontrada: {video_url[:100]}...")
                            
                            # Baixa o vídeo
                            async with session.get(video_url, headers=headers) as video_response:
                                if video_response.status == 200:
                                    video_bytes = await video_response.read()
                                    
                                    info = {
                                        'title': item_data.get('name', 'Vídeo Shopee'),
                                        'size': len(video_bytes)
                                    }
                                    
                                    return video_bytes, info
            
            # Se a API oficial não funcionou, tenta scraping do HTML
            logger.info("Tentando método alternativo via HTML...")
            
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Procura por dados JSON embutidos no HTML
                    json_match = re.search(r'<script>window\.__INITIAL_STATE__=({.+?})</script>', html)
                    if json_match:
                        try:
                            json_data = json.loads(json_match.group(1))
                            
                            # Navega pela estrutura para encontrar o vídeo
                            item_data = json_data.get('item', {}).get('item', {})
                            video_info = item_data.get('video_info_list', [])
                            
                            if video_info and len(video_info) > 0:
                                video_url = video_info[0].get('default_format', {}).get('url')
                                
                                if video_url:
                                    if video_url.startswith('//'):
                                        video_url = 'https:' + video_url
                                    
                                    async with session.get(video_url, headers=headers) as video_response:
                                        if video_response.status == 200:
                                            video_bytes = await video_response.read()
                                            
                                            info = {
                                                'title': item_data.get('name', 'Vídeo Shopee'),
                                                'size': len(video_bytes)
                                            }
                                            
                                            return video_bytes, info
                        except json.JSONDecodeError:
                            pass
                    
                    # Última tentativa: procura por URLs de vídeo diretamente no HTML
                    video_patterns = [
                        r'"video_url"\s*:\s*"([^"]+)"',
                        r'"url"\s*:\s*"(https?://[^"]*\.mp4[^"]*)"',
                    ]
                    
                    for pattern in video_patterns:
                        matches = re.findall(pattern, html)
                        if matches:
                            video_url = matches[0]
                            
                            if video_url.startswith('//'):
                                video_url = 'https:' + video_url
                            
                            async with session.get(video_url, headers=headers) as video_response:
                                if video_response.status == 200:
                                    video_bytes = await video_response.read()
                                    
                                    info = {
                                        'title': 'Vídeo Shopee',
                                        'size': len(video_bytes)
                                    }
                                    
                                    return video_bytes, info
            
            return None, ("⚠️ Não foi possível baixar o vídeo sem marca d'água.\n\n"
                         "💡 A Shopee protege seus vídeos e pode ter marca d'água embutida.\n"
                         "✅ Para vídeos 100% limpos, use TikTok!")
        
        except Exception as e:
            logger.error(f"Erro ao baixar Shopee: {e}")
            return None, f"Erro ao processar: {str(e)}"

# Instância global do downloader
downloader = VideoDownloader()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    welcome_message = """
🎥 *Bot de Download de Vídeos*

Bem-vindo! Eu posso baixar vídeos do *TikTok* e *Shopee*!

📝 *Como usar:*
1️⃣ Envie o link do vídeo do TikTok ou Shopee
2️⃣ Aguarde o processamento
3️⃣ Receba o vídeo!

🔗 *Plataformas suportadas:*
✅ *TikTok* - Remove 100% das marcas d'água
⚠️ *Shopee* - Melhor esforço (pode conter watermark)

⚡ *Sobre a Shopee:*
A Shopee protege seus vídeos e alguns podem ter marca d'água incorporada. Faremos o melhor para obter a versão limpa, mas não é sempre possível.

💡 *Dica para afiliados:*
Para vídeos 100% sem marca d'água, use TikTok! É perfeito para repostar.

📌 *Comandos:*
/start - Esta mensagem
/help - Ajuda detalhada

Envie um link para começar! 🚀
"""
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help"""
    help_message = """
❓ *Ajuda - Como Usar*

*Para TikTok:*
1. Abra o vídeo no TikTok
2. Toque em "Compartilhar"
3. Selecione "Copiar link"
4. Cole o link aqui no chat

✅ *TikTok = 100% sem marca d'água!*

*Para Shopee:*
1. Abra o produto com vídeo
2. Toque em "Compartilhar"
3. Copie o link
4. Cole o link aqui no chat

⚠️ *Atenção Shopee:*
A Shopee protege seus vídeos. Faremos o melhor para obter sem marca d'água, mas alguns podem ainda ter.

*Formatos aceitos:*
• TikTok: todos os links
• Shopee: br.shp.ee, shp.ee, shopee.com.br

*Suporte:* Entre em contato com o desenvolvedor.
"""
    await update.message.reply_text(help_message, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa mensagens com links"""
    text = update.message.text
    
    # Verifica se tem link do TikTok
    tiktok_url = downloader.extract_tiktok_url(text)
    if tiktok_url:
        await process_tiktok(update, tiktok_url)
        return
    
    # Verifica se tem link do Shopee
    shopee_url = downloader.extract_shopee_url(text)
    if shopee_url:
        await process_shopee(update, shopee_url)
        return
    
    # Nenhum link encontrado
    await update.message.reply_text(
        "❌ Nenhum link válido encontrado.\n\n"
        "Por favor, envie um link do TikTok ou Shopee.\n"
        "Use /help para ver exemplos."
    )

async def process_tiktok(update: Update, url: str):
    """Processa download do TikTok"""
    status_msg = await update.message.reply_text("⏳ Processando vídeo do TikTok...")
    
    try:
        # Baixa o vídeo
        video_bytes, result = await downloader.download_tiktok(url)
        
        if video_bytes is None:
            await status_msg.edit_text(f"❌ {result}")
            return
        
        # Prepara informações
        info = result
        size_mb = info['size'] / (1024 * 1024)
        duration = info['duration']
        
        caption = f"✅ *Vídeo do TikTok baixado!*\n\n"
        if info['author']:
            caption += f"👤 Autor: @{info['author']}\n"
        if duration:
            caption += f"⏱ Duração: {duration}s\n"
        caption += f"📦 Tamanho: {size_mb:.2f} MB\n\n"
        caption += "🎬 Vídeo sem marca d'água, pronto para usar!"
        
        await status_msg.edit_text("📤 Enviando vídeo...")
        
        # Envia o vídeo
        await update.message.reply_video(
            video=video_bytes,
            caption=caption,
            parse_mode='Markdown',
            supports_streaming=True
        )
        
        await status_msg.delete()
        
    except Exception as e:
        logger.error(f"Erro ao processar TikTok: {e}")
        await status_msg.edit_text(
            f"❌ Erro ao processar vídeo: {str(e)}\n\n"
            "Tente novamente ou use outro link."
        )

async def process_shopee(update: Update, url: str):
    """Processa download do Shopee"""
    status_msg = await update.message.reply_text(
        "⏳ Processando vídeo do Shopee...\n\n"
        "⚠️ *Nota:* A Shopee protege seus vídeos.\n"
        "Tentando obter a melhor qualidade possível...",
        parse_mode='Markdown'
    )
    
    try:
        # Baixa o vídeo
        video_bytes, result = await downloader.download_shopee(url)
        
        if video_bytes is None:
            await status_msg.edit_text(f"❌ {result}", parse_mode='Markdown')
            return
        
        # Prepara informações
        info = result
        size_mb = info['size'] / (1024 * 1024)
        
        caption = f"✅ *Vídeo do Shopee baixado!*\n\n"
        caption += f"📦 Tamanho: {size_mb:.2f} MB\n\n"
        caption += "🛍 Vídeo processado!"
        
        await status_msg.edit_text("📤 Enviando vídeo...")
        
        # Envia o vídeo
        await update.message.reply_video(
            video=video_bytes,
            caption=caption,
            parse_mode='Markdown',
            supports_streaming=True
        )
        
        await status_msg.delete()
        
    except Exception as e:
        logger.error(f"Erro ao processar Shopee: {e}")
        await status_msg.edit_text(
            f"❌ Erro ao processar vídeo: {str(e)}\n\n"
            "💡 *Dica:* Para vídeos 100% limpos, use TikTok!",
            parse_mode='Markdown'
        )

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa vídeos enviados diretamente"""
    await update.message.reply_text(
        "📹 Você enviou um vídeo!\n\n"
        "Para processar, eu preciso do *link* do vídeo do TikTok ou Shopee.\n\n"
        "Por favor, envie o link ao invés do arquivo.",
        parse_mode='Markdown'
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lida com erros"""
    logger.error(f"Erro: {context.error}")
    
    if update and update.message:
        await update.message.reply_text(
            "❌ Ocorreu um erro inesperado.\n"
            "Por favor, tente novamente."
        )

async def shutdown(application):
    """Fecha recursos ao desligar"""
    await downloader.close()

def main():
    """Função principal"""
    logger.info("🚀 Iniciando bot de download de vídeos...")
    logger.info(f"📍 Rodando no Railway.app")
    
    # Cria a aplicação
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Adiciona handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_error_handler(error_handler)
    
    # Registra função de shutdown
    application.post_shutdown = shutdown
    
    # Inicia o bot
    logger.info("🤖 Bot iniciado! Pressione Ctrl+C para parar.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
