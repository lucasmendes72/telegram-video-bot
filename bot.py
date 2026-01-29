import os
import re
import logging
import aiohttp
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Token do bot - Render vai pegar da variável de ambiente
BOT_TOKEN = os.getenv('BOT_TOKEN', '8421702557:AAG-o6kUbmuxoUoYxq59qP9OrPbGuQCLmPE')

if not BOT_TOKEN:
    logger.error("BOT_TOKEN não configurado! Configure nas variáveis de ambiente do Render.")
    exit(1)

class VideoDownloader:
    """Classe para gerenciar downloads de vídeos"""
    
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
            r'https?://(?:shopee\.com\.br|shopee\.com\.mx|shopee\.cl|shopee\.co|shp\.ee)/[\w./-]+',
            r'https?://(?:video|vod)\.shopee\.com\.br/[\w./-]+',
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
            
            # API do TikWM - gratuita e sem autenticação
            api_url = 'https://www.tikwm.com/api/'
            params = {'url': url, 'hd': 1}
            
            async with session.post(api_url, data=params) as response:
                if response.status != 200:
                    return None, f"Erro na API (status {response.status})"
                
                data = await response.json()
                
                if data.get('code') != 0:
                    msg = data.get('msg', 'Erro desconhecido')
                    return None, f"Erro ao processar: {msg}"
                
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
                            'title': video_data.get('title', '')[:100],
                            'author': video_data.get('author', {}).get('unique_id', ''),
                            'duration': video_data.get('duration', 0),
                            'size': len(video_bytes)
                        }
                        
                        return video_bytes, info
                    else:
                        return None, f"Erro ao baixar vídeo (status {video_response.status})"
        
        except asyncio.TimeoutError:
            logger.error("Timeout ao baixar TikTok")
            return None, "Tempo esgotado. Tente novamente."
        except Exception as e:
            logger.error(f"Erro ao baixar TikTok: {e}")
            return None, f"Erro: {str(e)}"
    
    async def download_shopee(self, url):
        """Baixa vídeo do Shopee sem marca d'água"""
        try:
            session = await self.get_session()
            
            # API do TikWM para Shopee
            api_url = 'https://www.tikwm.com/api/shopee/video'
            params = {'url': url}
            
            async with session.post(api_url, data=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('code') == 0:
                        video_data = data.get('data', {})
                        video_url = video_data.get('video_url') or video_data.get('url')
                        
                        if video_url:
                            # Baixa o vídeo
                            async with session.get(video_url) as video_response:
                                if video_response.status == 200:
                                    video_bytes = await video_response.read()
                                    
                                    info = {
                                        'title': video_data.get('title', 'Vídeo Shopee'),
                                        'size': len(video_bytes)
                                    }
                                    
                                    return video_bytes, info
            
            # Método alternativo se a API falhar
            return None, "Não foi possível baixar o vídeo do Shopee. Verifique se o link está correto."
        
        except asyncio.TimeoutError:
            logger.error("Timeout ao baixar Shopee")
            return None, "Tempo esgotado. Tente novamente."
        except Exception as e:
            logger.error(f"Erro ao baixar Shopee: {e}")
            return None, f"Erro: {str(e)}"

# Instância global do downloader
downloader = VideoDownloader()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    welcome_message = """
🎥 *Bot de Download de Vídeos*

Bem-vindo! Eu baixo vídeos do *TikTok* e *Shopee* sem marca d'água!

📝 *Como usar:*
1️⃣ Envie o link do vídeo
2️⃣ Aguarde o processamento
3️⃣ Receba o vídeo limpo!

🔗 *Plataformas:*
• TikTok (todos os links)
• Shopee Video

⚡ *Recursos:*
✓ Download em HD
✓ Remove marcas d'água
✓ Remove legendas e metadados
✓ Pronto para repostar

💡 *Dica para afiliados:*
Salve vídeos de produtos e reposte sem o @ do criador original!

📌 *Comandos:*
/start - Boas-vindas
/help - Ajuda

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
4. Cole aqui no chat

*Para Shopee:*
1. Abra o produto com vídeo
2. Toque em "Compartilhar"
3. Copie o link
4. Cole aqui no chat

*Formatos aceitos:*
• https://www.tiktok.com/@user/video/123...
• https://vm.tiktok.com/abc...
• https://shopee.com.br/produto...
• https://shp.ee/abc...

*Limitações:*
• Vídeos privados não podem ser baixados
• Vídeos muito longos demoram mais
• Respeite os direitos autorais

*Problemas?*
Verifique se:
✓ O link está correto
✓ O vídeo é público
✓ O link não expirou
"""
    await update.message.reply_text(help_message, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa mensagens com links"""
    text = update.message.text
    
    # Verifica TikTok
    tiktok_url = downloader.extract_tiktok_url(text)
    if tiktok_url:
        await process_tiktok(update, tiktok_url)
        return
    
    # Verifica Shopee
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
            supports_streaming=True,
            read_timeout=60,
            write_timeout=60
        )
        
        await status_msg.delete()
        
    except Exception as e:
        logger.error(f"Erro ao processar TikTok: {e}")
        await status_msg.edit_text(
            f"❌ Erro ao processar vídeo.\n\n"
            "Tente novamente ou use outro link."
        )

async def process_shopee(update: Update, url: str):
    """Processa download do Shopee"""
    status_msg = await update.message.reply_text("⏳ Processando vídeo do Shopee...")
    
    try:
        # Baixa o vídeo
        video_bytes, result = await downloader.download_shopee(url)
        
        if video_bytes is None:
            await status_msg.edit_text(f"❌ {result}")
            return
        
        # Prepara informações
        info = result
        size_mb = info['size'] / (1024 * 1024)
        
        caption = f"✅ *Vídeo do Shopee baixado!*\n\n"
        caption += f"📦 Tamanho: {size_mb:.2f} MB\n\n"
        caption += "🛍 Vídeo sem marca d'água, perfeito para afiliados!"
        
        await status_msg.edit_text("📤 Enviando vídeo...")
        
        # Envia o vídeo
        await update.message.reply_video(
            video=video_bytes,
            caption=caption,
            parse_mode='Markdown',
            supports_streaming=True,
            read_timeout=60,
            write_timeout=60
        )
        
        await status_msg.delete()
        
    except Exception as e:
        logger.error(f"Erro ao processar Shopee: {e}")
        await status_msg.edit_text(
            f"❌ Erro ao processar vídeo.\n\n"
            "Tente novamente ou use outro link."
        )

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa vídeos enviados diretamente"""
    await update.message.reply_text(
        "📹 Você enviou um vídeo!\n\n"
        "Para remover marca d'água, eu preciso do *link* do vídeo.\n\n"
        "Por favor, envie o link do TikTok ou Shopee.",
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
    logger.info("🚀 Iniciando bot no Render.com...")
    logger.info(f"Token configurado: {'Sim' if BOT_TOKEN else 'Não'}")
    
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
    logger.info("✅ Bot iniciado com sucesso!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
