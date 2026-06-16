"""Seed knowledge documents for the RAG knowledge base.

In production, replace ``SEED_DOCUMENTS`` with an ingestion pipeline that reads
Agritex / FAO / Tobacco Research Board / livestock manuals (PDF, HTML, etc.).
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.rag.store import VectorStore

SEED_DOCUMENTS: list[dict] = [
    {
        "source": "Agritex",
        "title": "Maize agronomy basics",
        "text": (
            "Maize in Zimbabwe is best planted with the onset of effective rains, "
            "usually mid-November to mid-December. Recommended plant population is "
            "44,000-53,000 plants per hectare. Apply basal compound D at planting "
            "(about 300 kg/ha) and top-dress with ammonium nitrate (200-250 kg/ha) "
            "at knee height. Practise crop rotation with legumes to manage fall "
            "armyworm and improve soil fertility."
        ),
    },
    {
        "source": "Tobacco Research Board",
        "title": "Flue-cured tobacco curing",
        "text": (
            "Flue-cured tobacco is reaped leaf by leaf as it ripens from the bottom "
            "of the plant upwards. During curing, yellowing occurs at 32-35C with high "
            "humidity, leaf drying at 38-46C, and midrib drying up to 60-74C. Avoid "
            "scorching by raising temperatures gradually. Properly cured leaf is lemon "
            "to orange in colour and grades higher at the auction floors."
        ),
    },
    {
        "source": "FAO",
        "title": "Cattle vaccination schedule",
        "text": (
            "Core cattle vaccinations in Southern Africa include blackleg (clostridial), "
            "anthrax, and lumpy skin disease. Calves should receive their first "
            "clostridial vaccine at 2-3 months with a booster 4-6 weeks later, then "
            "annual boosters. Tick-borne diseases such as heartwater and theileriosis "
            "require strategic dipping every 1-2 weeks in the wet season."
        ),
    },
    {
        "source": "Livestock Manual",
        "title": "Goat health and nutrition",
        "text": (
            "Goats thrive on browse and supplementary legume hay during the dry season. "
            "Deworm at the start and end of the rainy season. Watch for pulpy kidney and "
            "vaccinate accordingly. Provide clean water and mineral licks. Kids should be "
            "weaned at about three months."
        ),
    },
    {
        "source": "Agronomy",
        "title": "Soybean inoculation and fertility",
        "text": (
            "Soybeans fix nitrogen when seed is inoculated with the correct rhizobium "
            "strain before planting. Apply phosphorus at planting; nitrogen top-dressing "
            "is usually unnecessary. Plant in rows 45 cm apart at the onset of the rains. "
            "Soybeans are an excellent rotation crop before maize."
        ),
    },
]


async def ingest_seed_knowledge(session: AsyncSession) -> int:
    store = VectorStore(session)
    count = 0
    for doc in SEED_DOCUMENTS:
        await store.add_document(
            source=doc["source"], title=doc["title"], text=doc["text"], language="en"
        )
        count += 1
    return count
