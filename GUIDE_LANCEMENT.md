# 🚀 GUIDE DE LANCEMENT - VINTED MONITOR

## ⚡ **LANCEMENT RAPIDE (Recommandé)**

### 1. **Script Automatique**
```bash
./start_monitor.sh
```
Ce script fait tout automatiquement : vérifications, installation, démarrage.

### 2. **Vérification du Statut**
```bash
python -m app.main status
```

## 🔧 **LANCEMENT MANUEL**

### 1. **Prérequis**
```bash
# Installer les dépendances (si pas déjà fait)
pip install -r requirements.txt
playwright install chromium
```

### 2. **Démarrer le Monitoring**
```bash
python -m app.main run
```

### 3. **Commandes Utiles**
```bash
# Voir les watches configurées
python -m app.main list-watches

# Tester une watch spécifique
python -m app.main test-watch "Nike Air Force 1" --dry-run

# Tester le webhook Discord
python -m app.main test-webhook

# Nettoyer les anciennes données
python -m app.main cleanup --days 30
```

## 📋 **ÉTAT ACTUEL**

Votre système est **PRÊT** avec :
- ✅ **5 watches actives** configurées
- ✅ **1305 listings** déjà vus
- ✅ **278 notifications** envoyées
- ✅ **Discord webhook** configuré
- ✅ **BLACKBOX AI** intégrée
- ✅ **Google Sheets** configuré

## 🎯 **TEST RÉUSSI**

Le dernier test a montré :
- ✅ **156 listings** trouvés en 50 secondes
- ✅ **Prix moyen** : 19.19€ (range: 1-50€)
- ✅ **Scraping fonctionnel** avec anti-détection

## 🔄 **ARRÊTER LE SERVICE**

```bash
# Ctrl+C dans le terminal
# ou
pkill -f "python -m app.main run"
```

## 📊 **MONITORING**

- **Logs** : Consultez les logs en temps réel
- **Discord** : Notifications automatiques sur votre channel
- **Google Sheets** : Données de marché automatiquement trackées

---

**🎉 Votre Vinted Monitor est optimisé et prêt à fonctionner !**
