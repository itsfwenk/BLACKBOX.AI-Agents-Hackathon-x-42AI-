#!/bin/bash

# =============================================================================
# VINTED MONITOR - LANCEMENT OPTIMISÉ POUR NOTIFICATIONS INSTANTANÉES
# =============================================================================

echo "🚀 DÉMARRAGE VINTED MONITOR - MODE NOTIFICATIONS INSTANTANÉES"
echo "=============================================================="

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages colorés
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Vérifier si le script est exécutable
if [ ! -x "$0" ]; then
    chmod +x "$0"
    log_success "Script rendu exécutable"
fi

# Copier la configuration optimisée
if [ -f ".env.fast" ]; then
    cp .env.fast .env
    log_success "Configuration optimisée appliquée (.env.fast → .env)"
else
    log_error "Fichier .env.fast introuvable !"
    exit 1
fi

# Vérifier l'environnement virtuel
if [ ! -d "venv" ]; then
    log_info "Création de l'environnement virtuel..."
    python3 -m venv venv
    log_success "Environnement virtuel créé"
fi

# Activer l'environnement virtuel
log_info "Activation de l'environnement virtuel..."
source venv/bin/activate

# Installer/mettre à jour les dépendances
log_info "Installation des dépendances..."
pip install -r requirements.txt > /dev/null 2>&1
log_success "Dépendances installées"

# Installer Playwright si nécessaire
if ! playwright --version > /dev/null 2>&1; then
    log_info "Installation de Playwright..."
    playwright install chromium > /dev/null 2>&1
    log_success "Playwright installé"
fi

# Créer les dossiers nécessaires
mkdir -p logs data config
log_success "Dossiers créés"

# Vérifier la configuration
log_info "Vérification de la configuration..."

# Test rapide de l'installation
python -c "
import sys
sys.path.insert(0, '.')
try:
    from app.config import ConfigManager
    from app.models import WatchConfig
    print('✅ Configuration OK')
except Exception as e:
    print(f'❌ Erreur configuration: {e}')
    sys.exit(1)
" || exit 1

# Afficher les paramètres optimisés
echo ""
log_info "PARAMÈTRES OPTIMISÉS POUR NOTIFICATIONS INSTANTANÉES :"
echo "   • Intervalle de polling : 10 secondes (au lieu de 30s)"
echo "   • Concurrence : 5 (au lieu de 2)"
echo "   • Pages par poll : 1 (au lieu de 2)"
echo "   • Délais réduits : 400-800ms (au lieu de 800-2200ms)"
echo "   • IA BLACKBOX activée"
echo ""

# Demander confirmation
read -p "🚀 Démarrer le monitoring avec ces paramètres optimisés ? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_warning "Démarrage annulé"
    exit 0
fi

# Afficher les informations de démarrage
echo ""
log_success "DÉMARRAGE EN COURS..."
echo "📊 Watches configurées : $(python -c "
import yaml
try:
    with open('config/watches.yaml', 'r') as f:
        data = yaml.safe_load(f)
        print(len(data.get('watches', [])))
except:
    print('0')
")"
echo "🔗 Discord webhook : Configuré"
echo "🤖 IA BLACKBOX : Activée"
echo "📈 Google Sheets : Activé"
echo ""

log_info "Pour arrêter le monitoring, appuyez sur Ctrl+C"
echo "=============================================================="

# Démarrer le monitoring
python -m app.main run

# Message de fin
echo ""
log_info "Monitoring arrêté"
log_success "À bientôt ! 👋"
