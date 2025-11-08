from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class AudioSupportOpportunity:
    slug: str
    title: str
    description_es: str
    target_field: str
    language_code: str = 'es'
    needs_funding: bool = True


AUDIO_SUPPORT_OPPORTUNITIES: Dict[str, AudioSupportOpportunity] = {
    'job_post': AudioSupportOpportunity(
        slug='job_post',
        title='Audio para "Publicar trabajo"',
        description_es='Necesitamos una voz clara en español que explique el botón "Publicar trabajo" en la app.',
        target_field='Job Post'
    ),
    'my_products': AudioSupportOpportunity(
        slug='my_products',
        title='Audio para "Mis productos"',
        description_es='Ayúdanos a describir la sección "Mis productos" para quienes prefieren audio.',
        target_field='My Products',
        needs_funding=False
    ),
    'my_money': AudioSupportOpportunity(
        slug='my_money',
        title='Audio para "Mi dinero"',
        description_es='Queremos un audio corto que explique cómo consultar los ingresos.',
        target_field='My Money'
    ),
    'pending_jobs': AudioSupportOpportunity(
        slug='pending_jobs',
        title='Audio para "Trabajos pendientes"',
        description_es='Falta la guía en audio que explique qué trabajos necesitan atención.',
        target_field='Pending Jobs'
    ),
    'page_1': AudioSupportOpportunity(
        slug='page_1',
        title='Audio para "Página 1"',
        description_es='Describe en español cómo usar la primera página adicional.',
        target_field='Page 1',
        needs_funding=False
    ),
    'page_2': AudioSupportOpportunity(
        slug='page_2',
        title='Audio para "Página 2"',
        description_es='Necesitamos audio comunitario para la segunda página adicional.',
        target_field='Page 2'
    ),
}


def get_audio_support_opportunity(slug: str) -> AudioSupportOpportunity | None:
    return AUDIO_SUPPORT_OPPORTUNITIES.get(slug)
