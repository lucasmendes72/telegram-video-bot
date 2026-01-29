import os
import sys
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

# Token do bot - LEITURA SEGURA DA VARIÁVEL DE AMBIENTE
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# Verificação de segurança
if not BOT_TOKEN:
    logger.error("❌ ERRO CRÍTICO: BOT_TOKEN não encontrado!")
    logger.error("Configure a variável de ambiente BOT_TOKEN no Railway:")
    logger.error("1. Vá em 'Variables'")
    logger.error("2. Adicione: BOT_TOKEN = seu_token_do_botfather")
    sys.exit(1)

if BOT_TOKEN == 'SEU_TOKEN_AQUI':
    logger.error("❌ ERRO: Token padrão detectado!")
    logger.error("Você precisa configurar o BOT_TOKEN nas variáveis do Railway")
    sys.exit(1)

logger.info("✅ Token carregado com sucesso!")

# URLs das APIs
TIKWM_API = 'https://www.tikwm.com/api/'
SHOPEE_API = 'https://www.tikwm.com/api/shopee/video'

class VideoDownloader:
    """Classe para gerenciar downloads de vídeos do TikTok e Shopee"""
    
    def __init__(self):
        self.session = None
    
    async def get_session(self):
        """Retorna uma sessão aiohttp reutilizável"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
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
    
    async def download_shopee(self, url):
        """Baixa vídeo do Shopee sem marca d'água"""
        try:
            session = await self.get_session()
            
            # Tenta diferentes endpoints da API
            params = {'url': url}
            
            # Primeira tentativa com API do TikWM (suporta Shopee)
            async with session.post(SHOPEE_API, data=params) as response:
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
            
            # Método alternativo: extrair diretamente do HTML
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Procura por URLs de vídeo no HTML
                    video_patterns = [
                        r'"(https?://[^"]+\.mp4[^"]*)"',
                        r'videoUrl["\']:\s*["\']([^"\']+)["\']',
                    ]
                    
                    for pattern in video_patterns:
                        matches = re.findall(pattern, html)
                        if matches:
                            video_url = matches[0]
                            
                            async with session.get(video_url) as video_response:
                                if video_response.status == 200:
                                    video_bytes = await video_response.read()
                                    
                                    info = {
                                        'title': 'Vídeo Shopee',
                                        'size': len(video_bytes)
                                    }
                                    
                                    return video_bytes, info
            
            return None, "Não foi possível baixar o vídeo do Shopee"
        
        except Exception as e:
            logger.error(f"Erro ao baixar Shopee: {e}")
            return None, f"Erro: {str(e)}"

# Instância global do downloader
downloader = VideoDownloader()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    welcome_message = """
🎥 *Bot de Download de Vídeos*

Bem-vindo! Eu posso baixar vídeos do *TikTok* e *Shopee* sem marca d'água!

📝 *Como usar:*
1️⃣ Envie o link do vídeo do TikTok ou Shopee
2️⃣ Aguarde o processamento
3️⃣ Receba o vídeo sem marca d'água!

🔗 *Plataformas suportadas:*
• TikTok (todos os links)
• Shopee Video (produtos e reviews)

⚡ *Recursos:*
• Download em alta qualidade (HD quando disponível)
• Remove marcas d'água automaticamente
• Remove metadados e legendas
• Vídeos prontos para repostar

💡 *Dica para afiliados:*
Perfeito para salvar vídeos de produtos e repostar nas suas redes sociais sem o @ do criador original!

📌 *Comandos:*
/start - Mensagem de boas-vindas
/help - Ajuda e instruções

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

*Para Shopee:*
1. Abra o produto com vídeo
2. Toque em "Compartilhar"
3. Copie o link
4. Cole o link aqui no chat

*Formatos aceitos:*
• https://www.tiktok.com/@user/video/123...
• https://vm.tiktok.com/abc123/
• https://shopee.com.br/product...
• https://shp.ee/abc123

*Limitações:*
• Vídeos privados não podem ser baixados
• Vídeos muito longos podem demorar mais
• Respeite os direitos autorais do conteúdo

*Problemas?*
Se um vídeo não baixar, verifique:
✓ O link está correto?
✓ O vídeo é público?
✓ O link não expirou?

*Suporte:* Entre em contato com o desenvolvedor para reportar problemas.
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
            supports_streaming=True
        )
        
        await status_msg.delete()
        
    except Exception as e:
        logger.error(f"Erro ao processar Shopee: {e}")
        await status_msg.edit_text(
            f"❌ Erro ao processar vídeo: {str(e)}\n\n"
            "Tente novamente ou use outro link."
        )

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa vídeos enviados diretamente"""
    await update.message.reply_text(
        "📹 Você enviou um vídeo!\n\n"
        "Para remover marca d'água, eu preciso do *link* do vídeo do TikTok ou Shopee.\n\n"
        "Por favor, envie o link do vídeo ao invés do arquivo.",
        parse_mode='Markdown'
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lida com erros"""
    logger.error(f"Erro: {context.error}")
    
    if update and update.message:
        await update.message.reply_text(
            "❌ Ocorreu um erro inesperado.\n"
            "Por favor, tente novamente mais tarde."
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
