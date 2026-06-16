"""Outbound message catalogs (en / sn / nd) with safe formatting.

Add new languages by extending ``CATALOG`` — the structure is language -> key ->
template string. Missing keys/languages fall back to English then the raw key.
"""

from __future__ import annotations

from app.core.config import settings
from app.shared.enums import Language

CATALOG: dict[str, dict[str, str]] = {
    "en": {
        "greeting": "Hello! I'm Murimi, your farm assistant. How can I help today?",
        "planting_recorded": "Planting recorded: {area} ha of {crop}.",
        "vaccination_recorded": "Vaccination recorded for {count} animal(s).",
        "ask_vaccine": "Which vaccine was used?",
        "harvest_recorded": "Harvest recorded: {quantity} {unit}.",
        "expense_recorded": "Expense recorded: {amount}.",
        "disease_recorded": "Disease event recorded: {disease}. Please consult your vet.",
        "not_understood": "Sorry, I didn't quite get that. Can you rephrase?",
        "need_registration": "Please ask your farm admin to register you first.",
        "weather_alert": "Weather alert: {message}",
        "vaccination_reminder": "Reminder: vaccination due on {date}.",
        "irrigation_reminder": "Reminder: it may be time to irrigate your {crop}.",
    },
    "sn": {
        "greeting": "Mhoro! Ndini Murimi, mubatsiri wepurazi. Ndingakubatsira sei nhasi?",
        "planting_recorded": "Kudyara kwanyorwa: mahekita {area} e{crop}.",
        "vaccination_recorded": "Kubaiwa kwemhuka kwanyorwa kwemhuka {count}.",
        "ask_vaccine": "Ndeupi mushonga wamashandisa?",
        "harvest_recorded": "Goho ranyorwa: {quantity} {unit}.",
        "expense_recorded": "Mari yashandiswa yanyorwa: {amount}.",
        "disease_recorded": "Chirwere chanyorwa: {disease}. Tapota onana nachiremba wemhuka.",
        "not_understood": "Ndineurombo, handina kunzwisisa. Mungadzokorora here?",
        "need_registration": "Kumbirai mutariri wepurazi akunyoreshei kutanga.",
        "weather_alert": "Yambiro yemamiriro ekunze: {message}",
        "vaccination_reminder": "Yeuchidzo: kubaiwa kwemhuka panozosvika {date}.",
        "irrigation_reminder": "Yeuchidzo: inogona kunge yava nguva yekudiridza {crop}.",
    },
    "nd": {
        "greeting": "Sawubona! NginguMurimi, umsizi wepulazi. Ngingakusiza njani lamuhla?",
        "planting_recorded": "Ukutshala kubhaliwe: amahektare {area} e-{crop}.",
        "vaccination_recorded": "Ukugonyelwa kwezifuyo kubhaliwe kwezifuyo {count}.",
        "ask_vaccine": "Yiwuphi umuthi owusebenzisileyo?",
        "harvest_recorded": "Isivuno sibhaliwe: {quantity} {unit}.",
        "expense_recorded": "Imali esetshenzisiwe ibhaliwe: {amount}.",
        "disease_recorded": "Umkhuhlane ubhaliwe: {disease}. Sicela uxhumane lodokotela wezifuyo.",
        "not_understood": "Uxolo, angizwisisanga kuhle. Ungaphinda yini?",
        "need_registration": "Cela umphathi wepulazi akubhalise kuqala.",
        "weather_alert": "Isexwayiso sesimo sezulu: {message}",
        "vaccination_reminder": "Isikhumbuzo: ukugonyelwa kwezifuyo ngo-{date}.",
        "irrigation_reminder": "Isikhumbuzo: kungaba yisikhathi sokunisela {crop}.",
    },
}


def translate(key: str, lang: Language | str = Language.EN, **kwargs) -> str:
    code = lang.value if isinstance(lang, Language) else str(lang)
    template = (
        CATALOG.get(code, {}).get(key)
        or CATALOG[settings.DEFAULT_LANGUAGE].get(key)
        or CATALOG["en"].get(key)
        or key
    )
    try:
        return template.format(**kwargs)
    except (KeyError, IndexError):
        return template
