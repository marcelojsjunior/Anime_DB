# 📊 Projeto: Criação de uma Base de Dados de Animes com MyAnimeList API e BigQuery

Este projeto tem como objetivo a construção de uma base de dados estruturada com informações detalhadas sobre animes, utilizando a **API pública do MyAnimeList (MAL)** como fonte de dados e o **Google BigQuery** como destino para armazenamento e análise.

A solução foi desenvolvida com foco em escalabilidade e controle de dados históricos, possibilitando futuras análises sobre tendências, popularidade, sazonalidade, evolução de notas e outras métricas relevantes do universo dos animes.

---

## 🔧 Tecnologias utilizadas

- **Python** – scripts de extração, transformação e orquestração
- **API do MyAnimeList** – coleta dos dados dos animes
- **Pandas** – tratamento e estruturação dos dados
- **Google BigQuery** – armazenamento em nuvem dos dados estruturados
- **dotenv** – gestão de variáveis de ambiente (tokens, credenciais)
- **TQDM** – barra de progresso para visualização durante a extração
- **Google Cloud SDK** – integração com BigQuery

---

## ⚙️ Etapas do pipeline

### 🔐 1. Autenticação com a API do MyAnimeList

- Autenticação via OAuth 2.0.
- Refresh automático de token com armazenamento em `.env`.

### 📥 2. Extração de dados

- A extração é feita ID por ID (devido a limitações da API).
- Os campos coletados incluem:
  - Título, nota média, sinopse, datas, estúdios, gêneros, número de episódios, etc.
- Requisições possuem tratamento de erro e múltiplas tentativas.

### 💾 3. Armazenamento local

- Dados extraídos são armazenados localmente em um arquivo `animes_info.csv`.

### 🔎 4. Controle de duplicidade com BigQuery

- Consulta ao último ID existente na tabela `animes_info_raw` para evitar redundância.

### 📤 5. Envio ao BigQuery

- Inserção de dados limpos na tabela `Anime_DB.animes_info_raw`.

---

## 📁 Estrutura do projeto

📂 Anime_DB/
├── .env # Variáveis de ambiente (tokens, credenciais)
├── MyAnimeList_extract_data.py # Script principal de extração
├── batch_upload.py # Upload do .csv para o BigQuery
├── requirements.txt # Dependências Python
├── animes_info.csv # Backup local dos dados extraídos
└── README.md # Documentação do projeto

Abaixo, documentação visual dos outputs do projeto

Output do processo de extração realizado pelo script MyAnimeList_extract_data.py:

![image](https://github.com/user-attachments/assets/af84bb5b-405c-47b9-adbb-7cc3f2e2d1b7)

CSV de Output da extração:

![image](https://github.com/user-attachments/assets/f24c73ad-e58b-4337-96d2-dc03123b46ad)

Base da camada Bronze após a carga dos dados:

![image](https://github.com/user-attachments/assets/861e9ccc-1864-4992-8e39-0c46e60e47c9)



