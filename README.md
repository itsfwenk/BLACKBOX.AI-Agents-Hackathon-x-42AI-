# Vinted Monitor

A comprehensive service that monitors Vinted listings in near real-time for user-defined searches and sends Discord notifications when items are listed at or below target prices.

## Features

- 🔍 **Real-time Monitoring**: Continuously monitors Vinted listings based on your search criteria
- 💰 **Price Filtering**: Get notified only when items are at or below your target price
- 🌍 **Multi-Domain Support**: Works with multiple Vinted domains (FR, COM, DE, IT, ES, PL, LT, CZ)
- 💱 **Currency Conversion**: Optional currency conversion for cross-domain price comparison
- 👤 **Seller Filtering**: Filter by seller rating and feedback count
- 🔔 **Discord Notifications**: Rich Discord webhook notifications with item details and images
- 🗄️ **Deduplication**: Prevents duplicate notifications for the same listing
- 🐳 **Docker Support**: Easy deployment with Docker and docker-compose
- 🧪 **Testing**: Comprehensive test suite for reliability
- 🛡️ **Anti-Detection**: Polite scraping with randomized delays and stealth measures

## 🚀 Quick Launch (TL;DR)

**If dependencies are already installed:**

```bash
# Start monitoring (everything is already set up)
source venv/bin/activate && python -m app.main run
```

**If you get "ModuleNotFoundError" errors:**

```bash
# Install dependencies first
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# Then start monitoring
python -m app.main run
```

**Optional - Test first:**
```bash
# Test your watch before running continuously
source venv/bin/activate && python -m app.main test-watch "ETB aventures ensemble" --dry-run
```

**That's it!** Your monitor will find "ETB aventures ensemble" items under 75 EUR and send Discord notifications.

**⚠️ Note:** Manual installation is more reliable than Docker for this project.

---

## Quick Start

### 1. Installation

#### Using Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd vinted-monitor

# Create configuration files
python -m app.main init

# Configure your settings
cp .env.example .env
cp config/watches.yaml.example config/watches.yaml

# Edit .env with your Discord webhook URL
# Edit config/watches.yaml with your watch configurations

# Start with Docker Compose
docker-compose up -d
```

#### Manual Installation

```bash
# Clone the repository
git clone <repository-url>
cd vinted-monitor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Create configuration files
python -m app.main init

# Configure your settings
cp .env.example .env
cp config/watches.yaml.example config/watches.yaml
```

### 2. Configuration

#### Environment Variables (.env)

```env
# Discord webhook URL (required)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN

# Polling settings
DEFAULT_POLL_INTERVAL_SEC=30
CONCURRENCY=2
MAX_PAGES_PER_POLL=2

# Browser settings
HEADLESS=true
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36

# Delay settings (milliseconds)
MIN_DELAY_MS=800
MAX_DELAY_MS=2200

# Optional: Currency conversion
# CURRENCY_API_URL=https://api.exchangerate-api.com/v4/latest/
# CURRENCY_API_KEY=your_api_key_here

# Database and logging
DATABASE_PATH=vinted_monitor.db
LOG_LEVEL=INFO
LOG_FORMAT=text
```

#### Watch Configuration (config/watches.yaml)

```yaml
watches:
  - name: "Nike Air Force 1"
    vinted_domain: "vinted.fr"
    query: "nike air force 1"
    max_price: 50.0
    currency: "EUR"
    polling_interval_sec: 30
    filters:
      order: "newest_first"
      price_from: 10
      # Optional filters:
      # category_ids: [1234]
      # brand_ids: [5678]
      # size_ids: [42]
      # condition_ids: [1, 2, 3]
    min_seller_feedback_count: 5
    min_seller_rating: 4.0
    notification_webhook: null  # Use global webhook

  - name: "Vintage Denim Jacket"
    vinted_domain: "vinted.com"
    query: "vintage denim jacket"
    max_price: 30.0
    currency: "USD"
    polling_interval_sec: 45
    filters:
      order: "price_low_to_high"
      price_from: 15
    min_seller_feedback_count: 10
    min_seller_rating: 4.5
```

### 3. Usage

#### Command Line Interface

```bash
# Initialize configuration files
python -m app.main init

# Run the monitoring service
python -m app.main run

# List all watches
python -m app.main list-watches

# Test a specific watch
python -m app.main test-watch "Nike Air Force 1" --dry-run

# Clear seen listings for a watch (useful after changing price limits)
python -m app.main clear-seen "Watch Name"

# Test Discord webhook
python -m app.main test-webhook

# Test domain accessibility
python -m app.main test-domain vinted.fr

# Show service status
python -m app.main status

# Clean up old data
python -m app.main cleanup --days 30
```

#### Docker Usage

```bash
# Start the service
docker-compose up -d

# View logs
docker-compose logs -f vinted-monitor

# Stop the service
docker-compose down

# Run CLI commands
docker-compose exec vinted-monitor python -m app.main list-watches

# Clear seen listings for a watch (useful after changing price limits)
docker-compose exec vinted-monitor python -m app.main clear-seen "Watch Name"
```

## Configuration Details

### Watch Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Unique name for the watch |
| `vinted_domain` | string | Yes | Vinted domain (e.g., vinted.fr) |
| `query` | string | Yes | Search query keywords |
| `max_price` | float | Yes | Maximum price threshold |
| `currency` | string | No | Currency code (default: EUR) |
| `polling_interval_sec` | int | No | Polling interval in seconds (default: 30) |
| `filters` | object | No | Additional search filters |
| `min_seller_rating` | float | No | Minimum seller rating (0-5) |
| `min_seller_feedback_count` | int | No | Minimum seller feedback count |
| `notification_webhook` | string | No | Watch-specific Discord webhook |

### Filter Options

| Filter | Type | Description |
|--------|------|-------------|
| `order` | string | Sort order: `newest_first`, `price_low_to_high` |
| `price_from` | float | Minimum price |
| `category_ids` | array | Category IDs to filter by |
| `brand_ids` | array | Brand IDs to filter by |
| `size_ids` | array | Size IDs to filter by |
| `condition_ids` | array | Condition IDs (1=New, 2=Very good, etc.) |

### Supported Domains

- `vinted.fr` (France) - EUR
- `vinted.com` (USA) - USD
- `vinted.de` (Germany) - EUR
- `vinted.it` (Italy) - EUR
- `vinted.es` (Spain) - EUR
- `vinted.pl` (Poland) - PLN
- `vinted.lt` (Lithuania) - EUR
- `vinted.cz` (Czech Republic) - CZK

## 🎯 Optimisation de Recherche

Cette section explique toutes les options disponibles pour affiner vos recherches et éviter le spam de notifications.

### 🔍 Recherches Précises avec `query`

Le paramètre `query` est le plus important pour cibler exactement ce que vous cherchez.

#### **Recherche Exacte avec Guillemets**
```yaml
# ❌ MAUVAIS - trop large, trouve tout
query: ETB aventures ensemble

# ✅ BON - recherche exacte
query: '"ETB aventures ensemble"'
```

#### **Exclusions avec le Signe Moins (-)**
```yaml
# Exclure des mots-clés indésirables
query: '"ETB aventures ensemble" -peluche -figurine -carte -lot -collection'

# Exemples d'exclusions utiles :
query: '"Nike Air Force" -replica -fake -copie -imitation'
query: '"iPhone 13" -coque -protection -accessoire -chargeur'
query: '"Pokémon" -peluche -figurine -poster -autocollant'
```

#### **Recherches Multiples avec OU**
```yaml
# Rechercher plusieurs variantes
query: '"ETB aventures ensemble" OR "Elite Trainer Box aventures"'
query: '"Nike Air Force 1" OR "AF1" OR "Air Force One"'
```

#### **Recherches avec Wildcards**
```yaml
# Utiliser * pour les variantes
query: '"ETB * ensemble"'  # Trouve "ETB aventures ensemble", "ETB pokemon ensemble", etc.
query: '"iPhone 1*"'       # Trouve iPhone 11, 12, 13, 14, etc.
```

### 💰 Filtres de Prix

#### **Prix Minimum et Maximum**
```yaml
# Dans la section principale
max_price: 75.0           # Prix maximum (OBLIGATOIRE)

# Dans la section filters
filters:
  price_from: 50.0        # Prix minimum (optionnel)
```

#### **Stratégies de Prix**
```yaml
# Pour des objets rares - fourchette étroite
max_price: 60.0
filters:
  price_from: 50.0        # Fourchette 50-60€

# Pour des bonnes affaires - prix maximum bas
max_price: 30.0
filters:
  price_from: 1.0         # Jusqu'à 30€ maximum

# Pour des objets de collection - prix élevé acceptable
max_price: 200.0
filters:
  price_from: 100.0       # Fourchette 100-200€
```

### 👤 Filtres de Vendeur (Anti-Spam)

#### **Rating et Feedback Minimum**
```yaml
# Vendeurs fiables uniquement
min_seller_rating: 4.0           # Note minimum 4/5 étoiles
min_seller_feedback_count: 5     # Minimum 5 avis

# Pour des objets moins chers - critères plus souples
min_seller_rating: 3.5           # Note minimum 3.5/5
min_seller_feedback_count: 3     # Minimum 3 avis

# Désactiver les filtres vendeur (ATTENTION: beaucoup de spam)
min_seller_rating: null          # Pas de filtre de note
min_seller_feedback_count: null  # Pas de filtre d'avis
```

#### **Stratégies par Type d'Objet**
```yaml
# Objets de valeur (>50€) - vendeurs très fiables
min_seller_rating: 4.5
min_seller_feedback_count: 10

# Objets moyens (10-50€) - vendeurs modérément fiables  
min_seller_rating: 4.0
min_seller_feedback_count: 5

# Objets pas chers (<10€) - critères souples
min_seller_rating: 3.5
min_seller_feedback_count: 3
```

### 📊 Filtres de Tri et Ordre

#### **Options de Tri**
```yaml
filters:
  order: "newest_first"        # ✅ RECOMMANDÉ - nouveautés en premier
  # order: "price_low_to_high" # Prix croissant
  # order: "price_high_to_low" # Prix décroissant
  # order: "relevance"         # Pertinence (par défaut Vinted)
```

#### **Pourquoi `newest_first` est Recommandé**
- ✅ Trouve les nouvelles annonces rapidement
- ✅ Évite de revoir les mêmes anciennes annonces
- ✅ Meilleur pour les notifications en temps réel

### 🏷️ Filtres Avancés Vinted

#### **Catégories (`category_ids`)**
```yaml
filters:
  category_ids: [1234, 5678]     # IDs des catégories spécifiques
  
# Exemples de catégories courantes :
# - Vêtements femmes: [1]
# - Vêtements hommes: [2] 
# - Chaussures: [16]
# - Accessoires: [3]
# - Électronique: [1234] (exemple)
```

#### **Marques (`brand_ids`)**
```yaml
filters:
  brand_ids: [123, 456]          # IDs des marques spécifiques

# Exemples de marques courantes :
# - Nike: [53]
# - Adidas: [14]
# - Zara: [73]
# - H&M: [121]
# Note: Les IDs varient selon le domaine Vinted
```

#### **Tailles (`size_ids`)**
```yaml
filters:
  size_ids: [42, 43, 44]         # IDs des tailles spécifiques

# Exemples de tailles :
# - Chaussures: [39, 40, 41, 42, 43, 44, 45]
# - Vêtements: [S, M, L, XL] (convertis en IDs)
```

#### **État/Condition (`condition_ids`)**
```yaml
filters:
  condition_ids: [1, 2]          # IDs des états acceptés

# États Vinted :
# - 1: Neuf avec étiquettes
# - 2: Très bon état  
# - 3: Bon état
# - 4: État satisfaisant
# - 5: État moyen
```

### ⏱️ Optimisation des Intervalles

#### **Intervalles de Polling**
```yaml
# Surveillance intensive (objets très demandés)
polling_interval_sec: 30         # Toutes les 30 secondes

# Surveillance normale (RECOMMANDÉ)
polling_interval_sec: 45         # Toutes les 45 secondes

# Surveillance détendue (évite le rate-limiting)
polling_interval_sec: 120        # Toutes les 2 minutes

# Surveillance occasionnelle
polling_interval_sec: 300        # Toutes les 5 minutes
```

#### **Stratégies par Type d'Objet**
```yaml
# Objets très demandés (sneakers limitées, etc.)
polling_interval_sec: 30

# Objets normaux
polling_interval_sec: 45

# Objets de niche ou rares
polling_interval_sec: 120
```

### 🌍 Optimisation par Domaine

#### **Domaines et Devises**
```yaml
# France - marché le plus actif
vinted_domain: vinted.fr
currency: EUR

# USA - marché différent, prix en dollars
vinted_domain: vinted.com  
currency: USD

# Allemagne - bon marché européen
vinted_domain: vinted.de
currency: EUR
```

#### **Stratégies Multi-Domaines**
```yaml
# Même recherche sur plusieurs domaines
watches:
  - name: "Nike AF1 France"
    vinted_domain: vinted.fr
    query: '"Nike Air Force 1"'
    max_price: 80.0
    currency: EUR
    
  - name: "Nike AF1 Germany" 
    vinted_domain: vinted.de
    query: '"Nike Air Force 1"'
    max_price: 80.0
    currency: EUR
```

### 🚫 Anti-Spam et Rate-Limiting

#### **Éviter le Spam Discord**
```yaml
# Intervalles plus longs
polling_interval_sec: 120        # Au lieu de 30-45s

# Filtres vendeur stricts
min_seller_rating: 4.0
min_seller_feedback_count: 5

# Recherches très précises
query: '"terme exact" -exclusion1 -exclusion2'

# Prix réalistes (pas trop larges)
max_price: 75.0
filters:
  price_from: 50.0               # Fourchette étroite
```

#### **Configuration Anti-Rate-Limiting**
```yaml
# Dans .env
DEFAULT_POLL_INTERVAL_SEC=45     # Minimum 45s recommandé
CONCURRENCY=1                    # Une seule requête à la fois
MAX_PAGES_PER_POLL=1            # Une seule page par poll
MIN_DELAY_MS=1500               # Délais plus longs
MAX_DELAY_MS=3000
```

### 📝 Exemples de Configurations Optimisées

#### **Exemple 1: Sneakers Limitées (Surveillance Intensive)**
```yaml
- name: "Jordan 1 Retro High"
  vinted_domain: vinted.fr
  query: '"Jordan 1 Retro High" -replica -fake -copie'
  max_price: 200.0
  currency: EUR
  polling_interval_sec: 30
  filters:
    order: newest_first
    price_from: 100.0
    size_ids: [42, 43, 44]
    condition_ids: [1, 2]
  min_seller_rating: 4.5
  min_seller_feedback_count: 10
```

#### **Exemple 2: Vêtements Casual (Surveillance Normale)**
```yaml
- name: "Pull Nike Vintage"
  vinted_domain: vinted.fr  
  query: '"Nike" vintage pull -replica'
  max_price: 40.0
  currency: EUR
  polling_interval_sec: 45
  filters:
    order: newest_first
    price_from: 15.0
    condition_ids: [2, 3]
  min_seller_rating: 4.0
  min_seller_feedback_count: 5
```

#### **Exemple 3: Objets de Collection (Surveillance Détendue)**
```yaml
- name: "Cartes Pokémon Vintage"
  vinted_domain: vinted.fr
  query: '"carte pokémon" vintage -lot -collection -moderne'
  max_price: 150.0
  currency: EUR
  polling_interval_sec: 120
  filters:
    order: newest_first
    price_from: 50.0
    condition_ids: [1, 2, 3]
  min_seller_rating: 4.0
  min_seller_feedback_count: 8
```

#### **Exemple 4: Bonnes Affaires (Large Surveillance)**
```yaml
- name: "Vestes Hiver Bonnes Affaires"
  vinted_domain: vinted.fr
  query: 'veste hiver -abîmé -troué -taché'
  max_price: 25.0
  currency: EUR
  polling_interval_sec: 60
  filters:
    order: price_low_to_high
    price_from: 5.0
    condition_ids: [2, 3]
  min_seller_rating: 3.5
  min_seller_feedback_count: 3
```

### 🔧 Commandes de Test et Debug

#### **Tester une Configuration**
```bash
# Test sans notifications
python -m app.main test-watch "Nom de la Watch" --dry-run

# Test avec notifications
python -m app.main test-watch "Nom de la Watch"

# Vérifier les résultats
python -m app.main status
```

#### **Optimiser Après Test**
```bash
# Si trop de résultats : 
# - Ajouter des exclusions dans query
# - Augmenter min_seller_rating
# - Réduire max_price ou augmenter price_from

# Si pas assez de résultats :
# - Élargir la fourchette de prix  
# - Réduire les critères vendeur
# - Simplifier la query
```

### 💡 Conseils d'Optimisation

#### **Démarche Recommandée**
1. **Commencer large** : Query simple, prix larges
2. **Tester** : `python -m app.main test-watch "Name" --dry-run`
3. **Analyser** : Combien de résultats ? Pertinents ?
4. **Affiner** : Ajouter exclusions, ajuster prix
5. **Re-tester** : Vérifier l'amélioration
6. **Déployer** : Lancer la surveillance continue

#### **Signaux d'Alerte**
- ⚠️ **>50 notifications/heure** : Trop large, affiner
- ⚠️ **Rate-limiting Discord** : Augmenter polling_interval_sec
- ⚠️ **0 résultat pendant 24h** : Trop restrictif, élargir
- ⚠️ **Beaucoup de faux positifs** : Ajouter exclusions

#### **Bonnes Pratiques**
- ✅ Toujours utiliser `newest_first` pour l'ordre
- ✅ Mettre des guillemets pour les recherches exactes
- ✅ Ajouter des exclusions pour éliminer le bruit
- ✅ Tester avant de déployer en continu
- ✅ Surveiller les performances et ajuster

## Discord Webhook Setup

1. Go to your Discord server settings
2. Navigate to Integrations → Webhooks
3. Create a new webhook
4. Copy the webhook URL
5. Add it to your `.env` file as `DISCORD_WEBHOOK_URL`

## Development

### Running Tests

```bash
# Install development dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run specific test file
pytest tests/test_parsers.py

# Run with coverage
pytest --cov=app tests/
```

### Project Structure

```
vinted-monitor/
├── app/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── cli.py               # CLI interface
│   ├── config.py            # Configuration management
│   ├── models.py            # Data models
│   ├── store.py             # Database operations
│   ├── scheduler.py         # Watch scheduling
│   ├── currency.py          # Currency conversion
│   ├── utils.py             # Utilities
│   ├── scraper/
│   │   ├── browser.py       # Browser management
│   │   ├── vinted_scraper.py # Main scraping logic
│   │   └── parsers.py       # DOM parsing
│   └── notifier/
│       └── discord.py       # Discord notifications
├── tests/                   # Test suite
├── config/                  # Configuration files
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose setup
└── requirements.txt        # Python dependencies
```

## Performance and Limits

### Recommended Settings

- **Polling Interval**: 30-60 seconds minimum per watch
- **Concurrency**: 2-3 concurrent requests per domain
- **Max Pages**: 2-3 pages per poll to avoid rate limiting
- **Delays**: 800-2200ms between requests

### Resource Usage

- **Memory**: ~500MB-1GB depending on number of watches
- **CPU**: Low usage, spikes during scraping
- **Network**: Moderate bandwidth usage
- **Storage**: SQLite database grows slowly over time

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError (e.g., 'aiosqlite')**
   ```bash
   # Make sure virtual environment is activated and dependencies installed
   source venv/bin/activate
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Browser Launch Failed**
   ```bash
   # Install browser dependencies
   playwright install-deps chromium
   ```

3. **Permission Denied (Docker)**
   ```bash
   # Fix permissions
   sudo chown -R $USER:$USER ./data ./config ./logs
   ```

4. **Discord Webhook Not Working**
   - Verify webhook URL format
   - Test with: `python -m app.main test-webhook`

5. **No Listings Found (Scraper finds 0 items)**
   - CSS selectors have been updated for current Vinted structure (2024)
   - Test domain accessibility: `python -m app.main test-domain vinted.fr`
   - Verify search query works on Vinted website
   - Check watch configuration

6. **High Memory Usage**
   - Reduce concurrency settings
   - Decrease max pages per poll
   - Increase polling intervals

### Debugging

Enable debug logging:
```env
LOG_LEVEL=DEBUG
LOG_FORMAT=json
```

View detailed logs:
```bash
# Docker
docker-compose logs -f vinted-monitor

# Manual
python -m app.main run --log-level DEBUG
```

## Legal and Ethical Considerations

### Terms of Service Compliance

- **Respect Rate Limits**: Use appropriate delays between requests
- **Polite Scraping**: Don't overload Vinted's servers
- **Personal Use**: Intended for personal monitoring, not commercial use
- **No Automation**: Don't use for automated purchasing

### Best Practices

1. **Reasonable Polling**: Don't poll more frequently than every 30 seconds
2. **Limited Concurrency**: Keep concurrent requests low (2-3 max)
3. **Respectful Usage**: Monitor only items you're genuinely interested in
4. **Data Privacy**: Don't store or share personal data from listings

### Disclaimer

This tool is for educational and personal use only. Users are responsible for complying with Vinted's Terms of Service and applicable laws. The authors are not responsible for any misuse or violations.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## FAQ (Frequently Asked Questions)

### Q: If I update the watches.yaml file, what commands do I have to run to update the app?

**A: Simply restart the monitoring service:**

**Manual Installation:**
```bash
# Stop the current monitor (Ctrl+C if running)
# Then restart:
source venv/bin/activate && python -m app.main run
```

**Docker Installation:**
```bash
# Restart the service to pick up new configuration
docker-compose restart vinted-monitor

# Or stop and start:
docker-compose down
docker-compose up -d
```

**Note:** The monitor automatically loads the watches.yaml file on startup, so you just need to restart the service.

### Q: How do I test a new watch before adding it to continuous monitoring?

**A: Use the test-watch command:**
```bash
# Test without sending notifications
python -m app.main test-watch "Your Watch Name" --dry-run

# Test with notifications (to verify Discord webhook)
python -m app.main test-watch "Your Watch Name"
```

### Q: Why am I not getting notifications even though the monitor is running?

**A: This is normal behavior!** The monitor only notifies about NEW listings that appear AFTER monitoring starts. All existing listings are marked as "seen" to prevent spam. You'll get notifications when someone posts a new item matching your criteria.

**If you're still not getting notifications, run the troubleshooting commands:**
```bash
# Check if Discord webhook works
python -m app.main test-webhook

# Check if Vinted is accessible
python -m app.main test-domain vinted.fr

# Test your specific watch
python -m app.main test-watch "Your Watch Name" --dry-run
```

### Q: How do I clear the "seen" listings to get notifications for existing items?

**A: Use the clear-seen command:**
```bash
# Manual installation
python -m app.main clear-seen "Watch Name"

# Docker installation
docker-compose exec vinted-monitor python -m app.main clear-seen "Watch Name"
```

### Q: I'm getting "ERR_NETWORK_CHANGED" or network connectivity errors. Am I banned?

**A: You're likely NOT banned!** This is usually a network stability issue. Here's how to fix it:

**1. Check if you're actually banned:**
```bash
# Test basic Vinted access (should return HTTP 200 if not banned)
curl -I https://vinted.fr
```

**2. Apply network stability fixes:**
```bash
# Update your .env file with these settings:
MIN_DELAY_MS=1500
MAX_DELAY_MS=3000
DEFAULT_POLL_INTERVAL_SEC=45
CONCURRENCY=1
MAX_PAGES_PER_POLL=1
```

**3. Common causes of network errors:**
- WiFi switching to Ethernet (or vice versa)
- VPN connecting/disconnecting
- Router DHCP lease renewal
- ISP connection instability

**4. Solutions:**
- Restart your router/modem
- Use Docker (better network handling): `docker-compose up -d`
- Use the network-optimized startup script: `./start_monitor.sh`

### Q: How do I run comprehensive troubleshooting?

**A: Use these diagnostic commands:**
```bash
# Full system check (tests webhook, network, scraper)
python troubleshoot_notifications.py

# Check Vinted access and ban status
python check_vinted_access.py

# Apply network fixes automatically
python fix_network_issues.py

# Test individual components
python -m app.main test-webhook
python -m app.main test-domain vinted.fr
python -m app.main status
python -m app.main list-watches
```

### Q: Can I monitor multiple different items at the same time?

**A: Yes!** Add multiple watches to your `config/watches.yaml` file. Each watch monitors different items independently and sends separate Discord notifications.

### Q: How do I change the Discord webhook URL?

**A: Edit your `.env` file:**
1. Open `.env` file
2. Update `DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_NEW_WEBHOOK`
3. Restart the monitor
4. Test: `python -m app.main test-webhook`

### Q: The scraper finds 0 items, what's wrong?

**A: Try these troubleshooting steps:**
```bash
# 1. Test domain accessibility
python -m app.main test-domain vinted.fr

# 2. Test your specific watch
python -m app.main test-watch "Your Watch Name" --dry-run

# 3. Check service status
python -m app.main status

# 4. Verify search manually on Vinted website
# 5. Check price limits aren't too restrictive
```

### Q: How do I add more search filters (category, brand, size)?

**A: Add filters to your watch configuration:**
```yaml
watches:
  - name: "Nike Shoes Size 42"
    query: "nike"
    filters:
      category_ids: [1234]  # Shoes category
      brand_ids: [5678]     # Nike brand
      size_ids: [42]        # Size 42
      condition_ids: [1, 2] # New and Very Good condition
```

### Q: Can I use different Vinted domains (countries)?

**A: Yes!** Supported domains:
- `vinted.fr` (France) - EUR
- `vinted.com` (USA) - USD  
- `vinted.de` (Germany) - EUR
- `vinted.it` (Italy) - EUR
- `vinted.es` (Spain) - EUR
- `vinted.pl` (Poland) - PLN
- `vinted.lt` (Lithuania) - EUR
- `vinted.cz` (Czech Republic) - CZK

Test domain accessibility: `python -m app.main test-domain vinted.de`

### Q: How often does the monitor check for new listings?

**A: Every 30 seconds by default.** You can change this in your watch configuration:
```yaml
polling_interval_sec: 60  # Check every 60 seconds instead
```

**For network stability, consider 45+ seconds:**
```yaml
polling_interval_sec: 45  # More stable, less likely to trigger rate limits
```

### Q: The notification links don't work (404 error)?

**A: If you received a 404 error, it was likely from a test notification.** The real monitor extracts actual working URLs from Vinted listings. Test notifications use fake URLs for demonstration purposes.

### Q: How do I stop the monitor?

**A: Press Ctrl+C in the terminal, or for Docker:**
```bash
docker-compose down
```

### Q: Can I run multiple monitors for different searches?

**A: No need!** One monitor can handle multiple watches simultaneously. Just add all your searches to the same `watches.yaml` file.

### Q: How do I clean up old data from the database?

**A: Use the cleanup command:**
```bash
# Clean up data older than 30 days
python -m app.main cleanup --days 30

# Clean up data older than 7 days
python -m app.main cleanup --days 7
```

### Q: What are all the available CLI commands?

**A: Complete command reference:**
```bash
# Setup and initialization
python -m app.main init                    # Create config files

# Running the monitor
python -m app.main run                     # Start monitoring
./start_monitor.sh                         # Network-optimized startup

# Testing and diagnostics
python -m app.main test-webhook            # Test Discord webhook
python -m app.main test-domain vinted.fr   # Test Vinted access
python -m app.main test-watch "Name"       # Test specific watch
python -m app.main test-watch "Name" --dry-run  # Test without notifications

# Management
python -m app.main list-watches            # List all watches
python -m app.main status                  # Show service status
python -m app.main clear-seen "Name"       # Clear seen listings
python -m app.main cleanup --days 30       # Clean old data

# Troubleshooting scripts
python troubleshoot_notifications.py       # Full system diagnostic
python check_vinted_access.py             # Check ban status
python fix_network_issues.py              # Apply network fixes
```

### Q: I'm getting "ModuleNotFoundError: No module named 'aiosqlite'" or similar dependency errors?

**A: This means Python dependencies aren't installed. Follow these steps:**

**1. Create and activate virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/Mac
# or: venv\Scripts\activate  # On Windows
```

**2. Install all dependencies:**
```bash
pip install -r requirements.txt
playwright install chromium
```

**3. Test the installation:**
```bash
python -m app.main init
python -m app.main status
```

**4. If you still get errors, try:**
```bash
# Force reinstall all dependencies
pip install --force-reinstall -r requirements.txt
playwright install chromium --force
```

**Common dependency errors and solutions:**
- `ModuleNotFoundError: No module named 'aiosqlite'` → Run `pip install aiosqlite`
- `ModuleNotFoundError: No module named 'playwright'` → Run `pip install playwright && playwright install chromium`
- `ModuleNotFoundError: No module named 'click'` → Run `pip install click`

### Q: How do I optimize for better network stability?

**A: Apply these settings in your `.env` file:**
```env
# Network stability settings
MIN_DELAY_MS=1500                 # Longer delays between requests
MAX_DELAY_MS=3000
DEFAULT_POLL_INTERVAL_SEC=45      # Less frequent polling
CONCURRENCY=1                     # Single request at a time
MAX_PAGES_PER_POLL=1             # Limit pages per poll
HEADLESS=true                    # Run browser in background
```

**And in your `watches.yaml`:**
```yaml
watches:
  - name: "Your Watch"
    polling_interval_sec: 45      # 45+ seconds recommended
    # ... other settings
```

### Q: I'm getting Docker errors like "ContainerConfig" or "unable to open database file"?

**A: These are common Docker issues with solutions:**

**1. ContainerConfig error:**
```bash
# Clean up Docker completely and rebuild
docker-compose down --volumes --remove-orphans
docker system prune -f
docker-compose build --no-cache
docker-compose up -d
```

**2. Database permission errors:**
```bash
# Create directories with proper permissions
mkdir -p data logs config
sudo chown -R $USER:$USER data logs config
docker-compose restart
```

**3. If Docker continues to have issues, use manual installation instead:**
```bash
# Stop Docker
docker-compose down

# Use manual installation (more reliable)
source venv/bin/activate
python -m app.main run
```

**4. Docker volume issues:**
```bash
# Remove all volumes and start fresh
docker-compose down --volumes
docker volume prune -f
docker-compose up -d
```

### Q: Docker vs Manual Installation - which should I use?

**A: Based on our testing, Manual Installation is more reliable:**

**Manual installation (RECOMMENDED):**
- ✅ More reliable startup
- ✅ Better error handling
- ✅ Easier debugging
- ✅ Direct access to logs
- ✅ No permission issues

**Docker installation:**
- ⚠️ Can have permission issues
- ⚠️ Database access problems
- ⚠️ More complex troubleshooting
- ✅ Better for production deployment

**Recommended approach:**
```bash
# Use manual installation for reliability
source venv/bin/activate && python -m app.main run
```

**Docker commands (if you prefer Docker):**
```bash
docker-compose up -d              # Start in background
docker-compose logs -f            # View logs
docker-compose restart            # Restart service
docker-compose down               # Stop service
```

## Support

- 📖 Documentation: Check this README and code comments
- 🐛 Issues: Report bugs via GitHub Issues
- 💬 Discussions: Use GitHub Discussions for questions
- 🔧 Development: See the Development section above

## Changelog

### v1.0.0
- Initial release
- Multi-domain Vinted monitoring
- Discord webhook notifications
- Currency conversion support
- Docker deployment
- Comprehensive test suite
- CLI interface
- Anti-detection measures
