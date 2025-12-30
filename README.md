🚀 Assistant IA : Ingestion & Vectorisation Automatisée
Ce projet implémente un pipeline RAG (Retrieval-Augmented Generation) hautement scalable sur AWS, entièrement piloté par Terraform (Infrastructure as Code). Il permet de transformer des documents textuels bruts en une base de connaissances vectorielle exploitable par une IA.

🏗️ Architecture du Système :    

**Le système repose sur une architecture sans serveur (Serverless) pour une efficacité maximale :**

- Stockage Source 📥 : Les documents `.txt` sont déposés dans un bucket Amazon S3
- Trigger ⚡ : Chaque nouvel upload déclenche automatiquement une fonction `AWS Lambda`
- Traitement & IA 🧠 : La Lambda (exécutée via un conteneur Docker sur `ECR`) lit le fichier, découpe le texte (chunking) et génère des embeddings grâce à l'API `Google Gemini Pro`.
- Base de Données Vectorielle 🔍 : Les vecteurs sont stockés dans une collection `OpenSearch Serverless`, permettant des recherches sémantiques ultra-rapides

🛠️ Stack Technique

- Infrastructure : **Terraform**
- Cloud Provider : AWS (S3, Lambda, OpenSearch Serverless, IAM, ECR) 
- IA: gemini-2.5-flash (embeddings and retriever)
- Conteneurisation : **Docker** & Amazon `ECR`


🔐 Sécurité & Gouvernance (IAM)

**L'ensemble des accès est verrouillé selon le principe du moindre privilège**

- Trust Policy : Permet à AWS Lambda d'assumer son rôle de service
- Inline Policies : Droits granulaires pour l'accès à OpenSearch (AOSS) et au registre d'images ECR
- Managed Policies : Utilisation des politiques standards AWS pour S3 Full Access et les logs CloudWatch
- Data Access Policy : Contrôle d'accès précis au niveau de la collection OpenSearch pour les principaux autorisés

📋 La Force de Vericity

- Zéro Maintenance : Entièrement Serverless, aucune instance EC2 à gérer
- Automatisation Totale : De l'infrastructure (Terraform) au traitement des données (S3 Trigger)
- Scalabilité : Capable de traiter des milliers de documents simultanément grâce à la parallélisation de Lambda