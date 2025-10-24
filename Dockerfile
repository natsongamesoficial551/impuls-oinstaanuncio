FROM python:3.11-slim

WORKDIR /app

# Copiar requirements primeiro (cache)
COPY requirements.txt .

# Instalar dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o código
COPY . .

# Criar diretório de comprovantes
RUN mkdir -p comprovantes

# Expor porta do Flask
EXPOSE 10000

# Comando para iniciar o bot
CMD ["python", "main.py"]