# 🔵 GUIA COMPLETO: DEPLOY NO RENDER.COM

## ✅ Você já tem:
- ✅ Conta no Render (logado com Google)
- ✅ Token do BotFather guardado

Agora vamos fazer o deploy!

---

## 📁 PASSO 1: COLOCAR CÓDIGO NO GITHUB (10 minutos)

### 1.1. Acessar GitHub
1. Abra: **https://github.com**
2. Se não tiver conta, clique em **"Sign up"**
   - Use o mesmo email do Google para facilitar
3. Faça login

### 1.2. Criar Repositório
1. No canto superior direito, clique no **símbolo +**
2. Clique em **"New repository"**

### 1.3. Configurar Repositório
Preencha assim:

**Repository name:** `telegram-video-bot`

**Description:** `Bot para download de vídeos sem marca d'água`

**Visibilidade:** Deixe marcado **"Public"** (público)

**NÃO marque nenhuma outra opção** (Add a README, etc.)

Clique em **"Create repository"** (botão verde)

### 1.4. Fazer Upload dos Arquivos

Você vai ver uma página com várias opções. Procure o texto:
**"uploading an existing file"** (está no meio da página, em azul)

1. Clique nesse link azul
2. Você verá uma área escrita "Drag files here or choose your files"
3. Arraste os 4 arquivos que vou te fornecer:
   - `bot.py`
   - `requirements.txt`
   - `runtime.txt`
   - `README.md`
4. Ou clique em **"choose your files"** e selecione os 4 arquivos
5. Aguarde o upload completar (barra verde)
6. No final da página, clique no botão verde **"Commit changes"**

✅ **Código está no GitHub!**

**Copie a URL** da página (será algo como: `https://github.com/seu-usuario/telegram-video-bot`)

---

## 🔵 PASSO 2: CRIAR SERVIÇO NO RENDER (5 minutos)

### 2.1. Acessar Render
1. Abra: **https://render.com**
2. Você já está logado (usou Google)
3. Você verá o **Dashboard**

### 2.2. Criar Novo Serviço
1. No topo da página, clique no botão **"New +"** (azul)
2. No menu que abrir, clique em **"Background Worker"**

### 2.3. Conectar GitHub
1. Se é primeira vez, clique em **"Connect GitHub"**
2. Autorize o Render a acessar sua conta GitHub
3. Selecione **"Only select repositories"**
4. Escolha `telegram-video-bot`
5. Clique em **"Install"**

### 2.4. Configurar o Worker

Agora você verá um formulário. Preencha assim:

**Name:** `telegram-video-bot`
(pode ser qualquer nome que você quiser)

**Region:** Deixe como está (provavelmente Oregon ou Frankfurt)

**Branch:** `main` (já vem preenchido)

**Root Directory:** deixe em branco

**Runtime:** `Python 3`

**Build Command:**
```
pip install -r requirements.txt
```
(copie e cole exatamente isso)

**Start Command:**
```
python bot.py
```
(copie e cole exatamente isso)

**Plan:** Deixe em **"Free"** (grátis)

### 2.5. IMPORTANTE: Adicionar o Token

Antes de clicar em "Create", você precisa adicionar o token!

1. Role a página um pouco para baixo
2. Procure a seção **"Environment Variables"**
3. Clique em **"Add Environment Variable"**
4. Preencha:
   - **Key:** `BOT_TOKEN` (exatamente assim, em maiúsculas)
   - **Value:** Cole aqui o token que você copiou do BotFather
     - Exemplo: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`
5. Clique em **"Add"**

### 2.6. Criar o Worker

Agora sim, role até o final da página e clique no botão azul:
**"Create Background Worker"**

✅ **Serviço criado!**

---

## ⏳ PASSO 3: AGUARDAR O DEPLOY (2-3 minutos)

### 3.1. Acompanhar o Deploy
1. Você será redirecionado para a página do seu serviço
2. Verá a aba **"Logs"** aberta
3. Muitas mensagens vão passar na tela
4. Aguarde aparecer:
   - ✅ `Build successful`
   - ✅ `Deploy successful`
   - ✅ `🚀 Iniciando bot no Render.com...`
   - ✅ `✅ Bot iniciado com sucesso!`

### 3.2. Se aparecer erro:
- Clique na aba **"Settings"**
- Verifique se o `BOT_TOKEN` está correto
- Clique em **"Manual Deploy"** > **"Deploy latest commit"**

✅ **Bot está rodando!**

---

## 📱 PASSO 4: TESTAR O BOT (1 minuto)

### 4.1. Abrir o Telegram
1. Abra o app do Telegram no celular
2. Clique na lupa de busca
3. Digite o **username do seu bot** (aquele que você criou no BotFather)
   - Exemplo: `@meu_video_bot`
4. Clique no bot
5. Clique em **"INICIAR"** ou **"START"**

### 4.2. Testar
1. Você deve ver a mensagem de boas-vindas do bot! 🎉
2. Teste enviando um link do TikTok:
   - Abra o TikTok
   - Escolha um vídeo
   - Compartilhar > Copiar link
   - Cole no chat do bot
3. Aguarde alguns segundos
4. O bot vai enviar o vídeo sem marca d'água!

✅ **BOT FUNCIONANDO PERFEITAMENTE!**

---

## 🎯 RESUMO DO QUE VOCÊ FEZ

1. ✅ Subiu o código no GitHub
2. ✅ Criou Background Worker no Render
3. ✅ Configurou o token como variável de ambiente
4. ✅ Fez o deploy
5. ✅ Bot está online 24/7!

---

## 📊 INFORMAÇÕES IMPORTANTES

### 🆓 Plano Gratuito Render:
- **750 horas grátis por mês**
- Bot fica online ~31 dias (se não ultrapassar 750h)
- Sem restrições de rede
- Perfeito para uso pessoal

### 🔍 Como ver os logs:
1. Acesse render.com
2. Entre no seu serviço
3. Aba "Logs"
4. Veja tudo que está acontecendo

### 🔄 Como atualizar o bot:
1. Faça alterações nos arquivos no GitHub
2. Faça commit das mudanças
3. O Render faz deploy automático!

### 🛑 Como parar o bot:
1. Acesse o serviço no Render
2. Clique em "Suspend Service"

### ▶️ Como reiniciar:
1. Clique em "Resume Service"
2. Ou faça "Manual Deploy"

---

## ❓ PROBLEMAS COMUNS

### Bot não responde no Telegram:
1. ✅ Verifique se o serviço está "Live" no Render (bolinha verde)
2. ✅ Veja os logs - deve ter "Bot iniciado com sucesso"
3. ✅ Verifique se o token está correto nas Environment Variables
4. ✅ Tente fazer um Manual Deploy

### Erro "Token inválido":
1. ✅ Vá em Settings > Environment Variables
2. ✅ Clique em BOT_TOKEN
3. ✅ Verifique se o token está completo e correto
4. ✅ Não deve ter espaços antes ou depois
5. ✅ Salve e faça Manual Deploy

### Build failed:
1. ✅ Verifique se todos os arquivos estão no GitHub
2. ✅ Verifique se o `requirements.txt` está correto
3. ✅ Tente fazer deploy novamente

### Vídeo não baixa:
1. ✅ Verifique se o link é válido
2. ✅ Teste com outro vídeo
3. ✅ Veja os logs no Render para mais detalhes

---

## 🎉 PARABÉNS!

Seu bot está no ar! Ele vai:
- ✅ Baixar vídeos do TikTok sem marca d'água
- ✅ Baixar vídeos do Shopee sem marca d'água
- ✅ Funcionar 24 horas por dia
- ✅ Não precisa do seu computador ligado

---

## 💡 PRÓXIMOS PASSOS (Opcional)

### Personalizar o bot:
- Edite o arquivo `bot.py` no GitHub
- Mude as mensagens
- Adicione mais funcionalidades

### Monitorar uso:
- Acesse o Dashboard do Render
- Veja quanto das 750h você usou
- Acompanhe os logs

### Compartilhar:
- Compartilhe o username do bot
- Seus amigos podem usar também!

---

## 🆘 PRECISA DE AJUDA?

Se algo não funcionou, me diga:
1. Em qual passo você está
2. Qual mensagem de erro apareceu
3. Screenshot da tela (se possível)

Estou aqui para ajudar! 🚀
