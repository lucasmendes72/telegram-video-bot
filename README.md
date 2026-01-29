# 🤖 Bot Telegram - Configurado para Render.com

Bot para download de vídeos do TikTok e Shopee sem marca d'água.

## 🚀 Deploy no Render.com

Este bot está otimizado para rodar no Render.com!

### Arquivos Incluídos:
- `bot.py` - Código principal otimizado para Render
- `requirements.txt` - Dependências
- `runtime.txt` - Versão do Python (3.11.7)

### Como fazer deploy:

1. **Suba este código no GitHub**
2. **Acesse render.com e faça login**
3. **Crie novo Background Worker**
4. **Configure conforme instruções abaixo**

---

## 📋 Configurações no Render

Quando criar o Background Worker, use:

### Build Command:
```
pip install -r requirements.txt
```

### Start Command:
```
python bot.py
```

### Environment Variables:
Adicione uma variável:
- **Key**: `BOT_TOKEN`
- **Value**: (seu token do BotFather)

---

## ✅ Pronto!

Após o deploy, seu bot estará online 24/7!

### Recursos do Bot:
- ✅ Download TikTok sem marca d'água
- ✅ Download Shopee sem marca d'água
- ✅ Vídeos em HD quando disponível
- ✅ Remove metadados e legendas
- ✅ Pronto para repostar

### Comandos:
- `/start` - Mensagem de boas-vindas
- `/help` - Ajuda e instruções

---

## 🔧 Suporte

O bot foi testado e funciona perfeitamente no Render.com!

Se tiver problemas:
1. Verifique se o token está correto
2. Veja os logs no Render
3. Teste com /start no Telegram
