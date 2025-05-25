# ⚙️ Etapas do pipeline (cont.)

## 🔐 1. Autenticação com a API do MyAnimeList
- Autenticação via OAuth 2.0.
- Refresh automático de token com armazenamento em `.env`.

## 📥 2. Extração de dados
- A extração é feita ID por ID (devido a limitações da API).
- Campos coletados: título, nota média, sinopse, datas, estúdios, gêneros, número de episódios, etc.
- Tratamento de erros e múltiplas tentativas nas requisições.

## 💾 3. Armazenamento local
- Dados extraídos são armazenados localmente em um arquivo `animes_info.csv`.

## 🔎 4. Controle de duplicidade com BigQuery
- Consulta ao último ID existente na tabela `animes_info_raw` para evitar redundância.

## 📤 5. Envio ao BigQuery
- Inserção de dados limpos na tabela `Anime_DB.animes_info_raw`.

## 🔄 6. Transformação e modelagem dos dados com dbt
- Após o carregamento dos dados brutos no BigQuery, o **dbt** é utilizado para transformar, limpar e modelar a base de dados.
- Os modelos dbt realizam:
  - Remoção de duplicatas;
  - Conversão de tipos (strings para datas, números, etc.);
  - Criação de camadas estruturadas, como tabelas bronze (raw), silver (limpas) e gold (análise final);
  - Criação de tabelas materializadas para evitar custos excessivos em consultas temporárias.
- O dbt facilita o versionamento, documentação e automação das transformações SQL.

---

## 📁 Estrutura do projeto

```plaintext
📂 Anime_DB/
├── .env                        # Variáveis de ambiente (tokens, credenciais)
├── MyAnimeList_extract_data.py # Script principal de extração
├── batch_upload.py             # Upload do .csv para o BigQuery
├── requirements.txt            # Dependências Python
├── animes_info.csv             # Backup local dos dados extraídos
├── models/                    # Modelos dbt
│   ├── anime_source.sql        # Modelo ephemereal fonte raw
│   └── anime_info_clean.sql    # Modelo table bronze limpo e tipado
└── README.md                  # Documentação do projeto
```

Output do processo de extração realizado pelo script MyAnimeList_extract_data.py:

![image](https://github.com/user-attachments/assets/af84bb5b-405c-47b9-adbb-7cc3f2e2d1b7)

CSV de Output da extração:

![image](https://github.com/user-attachments/assets/f24c73ad-e58b-4337-96d2-dc03123b46ad)

Base da camada Bronze após a carga dos dados:

![image](https://github.com/user-attachments/assets/861e9ccc-1864-4992-8e39-0c46e60e47c9)

Scrips SQL para tratamento da tabela bronze:

![image](https://github.com/user-attachments/assets/98b12112-30ae-43bd-babc-fd57582cc1d1)

