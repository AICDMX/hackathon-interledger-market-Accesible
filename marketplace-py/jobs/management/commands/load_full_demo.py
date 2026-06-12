"""
Load a complete, lived-in demo: users, jobs, applications, submissions, and audio.
This creates a marketplace that feels like real people are using it.

Usage:
    python manage.py load_full_demo          # load everything
    python manage.py load_full_demo --reset  # wipe and reload
"""
import json
import os
import shutil
from datetime import timedelta
from decimal import Decimal
from io import StringIO

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from audio.models import AudioSnippet, StaticUIElement
from jobs.models import Job, JobApplication, JobSubmission, PendingPaymentTransaction
from users.models import User


class Command(BaseCommand):
    help = "Load a complete lived-in demo with users, jobs, applications, submissions, and audio"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete all existing demo data before loading",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            self.stdout.write(self.style.WARNING("Resetting demo data..."))
            PendingPaymentTransaction.objects.all().delete()
            JobSubmission.objects.all().delete()
            JobApplication.objects.all().delete()
            Job.objects.all().delete()
            AudioSnippet.objects.all().delete()
            StaticUIElement.objects.all().delete()
            User.objects.exclude(username="admin").delete()
            self.stdout.write(self.style.SUCCESS("All demo data cleared."))

        self._load_users()
        self._load_jobs()
        self._create_applications()
        self._create_submissions()
        self._wire_audio()
        self.stdout.write(self.style.SUCCESS("\n=== Full demo loaded successfully! ==="))
        self._print_summary()

    # ── Users ──────────────────────────────────────────────────────────

    def _load_users(self):
        self.stdout.write("\n── Loading users ──")
        json_file = os.path.join(settings.BASE_DIR, "data", "full_demo_users.json")
        call_command(
            "load_demo_users", json_file=json_file, stdout=StringIO()
        )
        # Update existing users with full profile data
        with open(json_file, "r", encoding="utf-8") as f:
            users_data = json.load(f)
        for ud in users_data:
            try:
                user = User.objects.get(username=ud["username"])
                changed = False
                if ud.get("profile_note") and not user.profile_note:
                    user.profile_note = ud["profile_note"]
                    changed = True
                if ud.get("pretty_name") and user.pretty_name != ud["pretty_name"]:
                    user.pretty_name = ud["pretty_name"]
                    changed = True
                if ud.get("native_languages") and user.native_languages != ud.get("native_languages", ""):
                    user.native_languages = ud["native_languages"]
                    changed = True
                if ud.get("preferred_language") and user.preferred_language != ud.get("preferred_language", "en"):
                    user.preferred_language = ud["preferred_language"]
                    changed = True
                if changed:
                    user.save()
                    self.stdout.write(f"  Updated profile: {user.username}")
            except User.DoesNotExist:
                pass
        self.stdout.write(self.style.SUCCESS(f"  Users: {User.objects.count()} total"))

    # ── Jobs ───────────────────────────────────────────────────────────

    def _load_jobs(self):
        self.stdout.write("\n── Loading jobs ──")
        json_file = os.path.join(settings.BASE_DIR, "data", "full_demo_jobs.json")
        with open(json_file, "r", encoding="utf-8") as f:
            jobs_data = json.load(f)

        created = 0
        for jd in jobs_data:
            if Job.objects.filter(title=jd["title"]).exists():
                continue
            funder_username = jd.get("funder_username", "demo_funder")
            try:
                funder = User.objects.get(username=funder_username)
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f"  Funder '{funder_username}' not found, using demo_funder"
                ))
                funder = User.objects.get(username="demo_funder")

            amount = Decimal(str(jd.get("amount_per_person", 100)))
            max_resp = jd.get("max_responses", 1)
            status = jd.get("status", "recruiting")

            now = timezone.now()
            # Vary dates to look realistic
            days_ago = {"recruiting": 3, "selecting": 7, "submitting": 12,
                        "reviewing": 18, "complete": 30}.get(status, 5)
            created_offset = now - timedelta(days=days_ago)

            job = Job(
                title=jd["title"],
                description=jd["description"],
                target_language=jd.get("target_language_code", "nah"),
                target_dialect=jd.get("target_dialect", ""),
                deliverable_types=jd.get("deliverable_types", "text"),
                amount_per_person=amount,
                budget=amount * max_resp,
                max_responses=max_resp,
                funder=funder,
                status=status,
                recruit_limit=jd.get("recruit_limit", 10),
                submit_deadline_days=jd.get("submit_deadline_days", 7),
            )
            # Set appropriate deadlines per status
            if status == "recruiting":
                job.recruit_deadline = now + timedelta(days=7)
                job.expired_date = now + timedelta(days=14)
            elif status == "selecting":
                job.recruit_deadline = now - timedelta(days=1)
                job.expired_date = now + timedelta(days=14)
            elif status == "submitting":
                job.submit_deadline = now + timedelta(days=5)
                job.expired_date = now + timedelta(days=14)
            elif status == "reviewing":
                job.submit_deadline = now - timedelta(days=2)
                job.expired_date = now + timedelta(days=7)
            elif status == "complete":
                job.expired_date = now - timedelta(days=3)
                job.contract_completed = True

            # Skip auto-transition logic by using bulk-style save
            job.save()
            # Force status in case auto-transition changed it
            if job.status != status:
                Job.objects.filter(pk=job.pk).update(status=status)
                job.status = status

            created += 1

        self.stdout.write(self.style.SUCCESS(f"  Jobs: {created} created, {Job.objects.count()} total"))

    # ── Applications ───────────────────────────────────────────────────

    def _create_applications(self):
        self.stdout.write("\n── Creating applications ──")
        if JobApplication.objects.exists():
            self.stdout.write("  Applications already exist, skipping.")
            return

        # Define which creators apply to which jobs, with realistic notes
        applications = [
            # Recruiting jobs — multiple fresh applications
            {
                "job_title": "Traducir folleto de prevención de diabetes",
                "apps": [
                    ("maria_nahuatl", "pending",
                     "Soy hablante nativa de náhuatl de la Huasteca y he traducido materiales de salud para la SEP durante 6 años. Conozco bien la terminología médica adaptada al náhuatl. Puedo entregar una traducción que suene natural, no como español disfrazado."),
                    ("ernesto_nahuatl", "pending",
                     "Trabajo como promotor de salud comunitaria en la Sierra Norte de Puebla — es exactamente la región que mencionan. Conozco el dialecto local y sé cómo habla la gente sobre salud. He visto cómo la diabetes afecta a nuestras comunidades y este trabajo me importa personalmente."),
                ],
            },
            {
                "job_title": "Grabar mensaje de bienvenida para centro ecoturístico",
                "apps": [
                    ("luis_tsotsil", "pending",
                     "Soy hablante nativo de tsotsil de Zinacantán. He grabado audio para dos campañas de radio comunitaria y tengo experiencia con locución. Puedo darle al mensaje un tono cálido y acogedor, como recibir a alguien en casa."),
                    ("valentina_tseltal", "pending",
                     "Aunque mi lengua materna es tseltal, también hablo tsotsil con fluidez — las dos lenguas son cercanas y crecí escuchando ambas en mi comunidad. Tengo experiencia en producción audiovisual y puedo entregar audio con calidad profesional."),
                ],
            },
            {
                "job_title": "Traducir etiquetas para empaque de café orgánico",
                "apps": [
                    ("luis_tsotsil", "pending",
                     "Mi familia cultiva café en los Altos de Chiapas y hablo el tsotsil de esta región. Conozco las palabras que usamos para hablar del café, la tierra y el trabajo en comunidad. Puedo hacer que las etiquetas suenen auténticas porque vivo esta realidad."),
                ],
            },
            {
                "job_title": "Grabar spot de radio para promover la participación electoral",
                "apps": [
                    ("soledad_kaqchikel", "pending",
                     "Soy kaqchikel de Sololá — conozco bien la región donde se transmitirá el spot. He traducido materiales electorales antes y sé que el tono debe motivar sin sonar como propaganda. Puedo grabar con voz clara y convincente."),
                ],
            },

            # Selecting jobs — some selected, some pending
            {
                "job_title": "Crear arte digital: \"El colibrí y la flor de cempasúchil\"",
                "apps": [
                    ("pedro_zapoteco", "selected",
                     "Soy artista gráfico y he ilustrado dos libros infantiles bilingües. Conozco bien la iconografía mesoamericana y puedo crear algo que sea moderno pero respetuoso de la tradición. Adjunto enlace a mi portafolio en mi perfil."),
                    ("yolanda_huichol", "pending",
                     "Como artista wixárika, trabajo con imágenes que cuentan historias sagradas. Puedo crear una ilustración que capture la conexión entre el colibrí y la flor de cempasúchil con un estilo vibrante inspirado en el arte huichol. Sería un honor participar."),
                    ("juan_mixteco", "pending",
                     "Además de traductor, soy músico y artista. He hecho diseños para eventos comunitarios y portadas de discos. Puedo crear una ilustración digital que combine elementos tradicionales con un estilo contemporáneo."),
                ],
            },
            {
                "job_title": "Traducir derechos del paciente para clínica comunitaria",
                "apps": [
                    ("maria_nahuatl", "selected",
                     "He traducido materiales médicos al náhuatl durante años para la SEP. Conozco la terminología y sé cómo expresar conceptos legales como 'consentimiento informado' y 'confidencialidad' de forma que cualquier hablante de náhuatl entienda."),
                    ("ernesto_nahuatl", "selected",
                     "Trabajo en salud comunitaria en esta misma región. He acompañado a pacientes que no entendían sus derechos y sé exactamente qué palabras usar para que el mensaje sea claro. Este trabajo me parece urgente e importante."),
                ],
            },

            # Submitting jobs — all selected
            {
                "job_title": "Transcribir receta de mole ceremonial narrada por abuela otomí",
                "apps": [
                    ("carlos_otomi", "selected",
                     "Soy hablante nativo de hñähñu del Valle del Mezquital y he trabajado en el diccionario hñähñu-español del INALI. Tengo experiencia transcribiendo audio en otomí y conozco la ortografía estándar. Trataré este audio con el respeto que merece un tesoro familiar."),
                ],
            },
            {
                "job_title": "Grabar derechos de personas detenidas en quechua",
                "apps": [
                    ("ana_quechua", "selected",
                     "Soy quechua de Ayacucho — exactamente la variante que necesitan. He traducido campañas completas de derechos humanos al quechua para el Ministerio de Justicia. Este tema me importa: he visto a personas detenidas que no entendían lo que les decían. Puedo grabar con voz firme y clara."),
                ],
            },
            {
                "job_title": "Traducir y grabar cuento infantil para app educativa",
                "apps": [
                    ("diego_aymara", "selected",
                     "Soy maestro bilingüe y radialista aymara. Tengo experiencia grabando contenido para niños y sé modular mi voz para que suene suave y calmada. Tengo equipo de grabación propio y puedo entregar audio limpio."),
                ],
            },

            # Reviewing jobs — all selected
            {
                "job_title": "Traducir letreros para reserva ecológica comunitaria",
                "apps": [
                    ("pedro_zapoteco", "selected",
                     "Soy zapoteco y conozco la forma en que hablamos sobre la naturaleza y la tierra en nuestra lengua. Los letreros deben sonar como algo que diría un abuelo, no como una traducción de gobierno. Puedo lograr ese tono."),
                ],
            },
            {
                "job_title": "Grabar mensaje para contestadora de clínica comunitaria",
                "apps": [
                    ("raul_mazateco", "selected",
                     "Soy locutora profesional en radio comunitaria de Huautla y hablo mazateco de Huautla — exactamente lo que necesitan. Tengo equipo semiprofesional y entrego audio limpio en MP3. Mi voz se ha usado en mensajes institucionales antes."),
                ],
            },

            # Complete jobs — all selected
            {
                "job_title": "Transcripción de conversación en mercado para archivo lingüístico",
                "apps": [
                    ("elena_triqui", "selected",
                     "Soy triqui de Chicahuaxtla y he trabajado con el CIESAS en proyectos de documentación lingüística. Conozco la ortografía práctica y el sistema tonal. Puedo hacer una transcripción precisa y confiable."),
                ],
            },
            {
                "job_title": "Traducir requisitos de programa de apoyo para artesanas",
                "apps": [
                    ("carmen_chinanteca", "selected",
                     "Soy hablante de chinanteco de Ojitlán y trabajo como intérprete en mi comunidad. He traducido convocatorias y documentos oficiales antes. Sé que las cantidades y fechas deben quedar muy claras para evitar confusiones."),
                ],
            },
            {
                "job_title": "Traducir botones de interfaz para app móvil",
                "apps": [
                    ("maria_nahuatl", "selected",
                     "He trabajado en la localización de dos aplicaciones educativas al náhuatl. Sé que los botones deben ser concisos y naturales. Tengo experiencia encontrando formas cortas de decir las cosas en náhuatl sin perder el significado."),
                ],
            },
        ]

        total = 0
        for app_group in applications:
            try:
                job = Job.objects.get(title=app_group["job_title"])
            except Job.DoesNotExist:
                continue
            for username, status, note in app_group["apps"]:
                try:
                    applicant = User.objects.get(username=username)
                except User.DoesNotExist:
                    continue
                if JobApplication.objects.filter(job=job, applicant=applicant).exists():
                    continue
                JobApplication.objects.create(
                    job=job,
                    applicant=applicant,
                    status=status,
                    profile_note=note,
                )
                total += 1

        self.stdout.write(self.style.SUCCESS(f"  Applications: {total} created"))

    # ── Submissions ────────────────────────────────────────────────────

    def _create_submissions(self):
        self.stdout.write("\n── Creating submissions ──")
        if JobSubmission.objects.exists():
            self.stdout.write("  Submissions already exist, skipping.")
            return

        submissions = [
            # Submitting jobs — work in progress
            {
                "job_title": "Transcribir receta de mole ceremonial narrada por abuela otomí",
                "creator": "carlos_otomi",
                "status": "pending",
                "is_draft": False,
                "text_content": (
                    "Transcripción – Audio de Doña Esperanza (4:02 min)\n\n"
                    "Nuga di mädi da 'yogi nä'ä ra mole...\n"
                    "Mí nzäntho gi tu̱di ra nzoi, ne gi nxa̱di ra zidada...\n"
                    "Nu'ä ra t'uki — di ñuts'i ko ya ju̱ni...\n"
                    "Ne ri hñä ra ndä, ra däthi, ra 'ñe...\n"
                    "Gi pe̱fi xá hño, hinga gi nzinga nzäntho...\n"
                    "[risas] ... mí xi ma ba̱ gá nxo̱ge̱...\n\n"
                    "[Nota del transcriptor: En el minuto 2:15 dice \"chile ancho\" en español, "
                    "marcado en cursiva. En el minuto 3:40 hay ruido de ollas que dificulta "
                    "escuchar una palabra — la marqué con [inaudible]. El resto es claro.]"
                ),
                "note": "He completado la transcripción del audio. Es un tesoro hermoso — su abuela tiene una forma de hablar muy poética. Marqué una palabra inaudible en el minuto 3:40 por ruido de cocina. Todo lo demás está claro. Usé la ortografía estándar del hñähñu del Valle del Mezquital.",
            },
            {
                "job_title": "Grabar derechos de personas detenidas en quechua",
                "creator": "ana_quechua",
                "status": "pending",
                "is_draft": False,
                "text_content": (
                    "Traducción al quechua de Ayacucho:\n\n"
                    "Qampa derechuykikuna:\n"
                    "• Ch'inyakuyta atinki. Imatachus ninki chayqa contraykipi "
                    "apaykachankuman.\n"
                    "• Imarayku hap'isunkichik chayta yachanayki tiyan.\n"
                    "• Huk familiaykita otaq abogadota waqyayta atinki.\n"
                    "• Mana castellanota rimaspayki, huk "
                    "simiykipi interpreteta mañakuyta atinki.\n"
                    "• Hampikuyta necesitaspayki, chaskiyta atinki.\n"
                    "• Mana pipas maqasunkimanchu nitaq "
                    "ñak'arichisunkimanchu.\n"
                    "• Ama ima papeltapas firmaychischu mana "
                    "entiendespaykiqa.\n\n"
                    "Kay derechokunaykitaqa mana pipas "
                    "qichusuykimanchu."
                ),
                "note": "Adjunto la traducción escrita y la grabación de audio (55 segundos). Usé un tono firme pero empático — como le hablarías a alguien que está asustado pero necesita saber que tiene derechos. El audio está limpio, grabado en mi estudio.",
            },
            {
                "job_title": "Traducir y grabar cuento infantil para app educativa",
                "creator": "diego_aymara",
                "status": "pending",
                "is_draft": True,
                "text_content": (
                    "BORRADOR — Traducción al aymara central:\n\n"
                    "Jisk'a conejo phaxsimp uñtatayna, jach'a "
                    "muruq phaxsi.\n"
                    "'Mä uruxa jumaru puriñäni' sasaw arstayna.\n"
                    "Taykapa ñiq'iptatayna ukhamat sarakitayna:\n"
                    "'Jumanx saminakamasti alaxpach jach'awa, "
                    "jisk'a wawäja.'\n"
                    "...\n\n"
                    "[Nota: Estoy trabajando en las últimas dos oraciones. "
                    "Quiero que el ritmo funcione bien para niños. "
                    "Subiré la grabación cuando tenga el texto final.]"
                ),
                "note": "Borrador de la traducción — tengo las primeras 4 oraciones listas. Estoy trabajando en las últimas dos para que el ritmo y la musicalidad funcionen para niños pequeños. Subiré la versión final con audio esta semana.",
            },

            # Reviewing jobs — submitted work ready for review
            {
                "job_title": "Traducir letreros para reserva ecológica comunitaria",
                "creator": "pedro_zapoteco",
                "status": "pending",
                "is_draft": False,
                "text_content": (
                    "LETRERO 1 — Entrada:\n"
                    "\"Zanda gukua lu ni'. Yaga ro' na' nuu ndaani "
                    "guendaranaxhii lídxinu'. Gudxiña lu ni' ne guendarannaxhii.\"\n\n"
                    "LETRERO 2 — Sendero:\n"
                    "\"Gasti' bisiidi'. Bichaa'ya' ca cosa biidi'lu'. "
                    "Qué ganda guni gui'xhi'. Biidxi si guidxi ládxinu'.\"\n\n"
                    "LETRERO 3 — Cascada:\n"
                    "\"Neza sti' guiigu'. Bisiidi' ca mani' ne ca yaga. "
                    "Qué ganda guixhe ca yaga ne ca mani'. "
                    "Ni' runi gapa nisa nayá.\"\n\n"
                    "[Nota: Adapté \"sagrado\" como \"lugar de respeto y cariño\" "
                    "porque en zapoteco de la Sierra no usamos el concepto de "
                    "sagrado de la misma manera. La idea es la misma pero se "
                    "expresa diferente.]"
                ),
                "note": "Aquí están los tres letreros. Hice algunas adaptaciones culturales que explico al final del texto. Lo más importante: \"sagrado\" no tiene traducción directa en nuestro zapoteco — usé una expresión que transmite la misma idea de respeto profundo. Quedo atento a sus comentarios.",
            },
            {
                "job_title": "Grabar mensaje para contestadora de clínica comunitaria",
                "creator": "raul_mazateco",
                "status": "pending",
                "is_draft": False,
                "text_content": (
                    "Traducción al mazateco de Huautla:\n\n"
                    "Kjuatsjoa xi kitsúya_jin ndi̱. Clínica "
                    "Comunitaria Esperanza.\n"
                    "Ni xi je tíña tsja̱ ya ja.\n"
                    "Ja ma'an ndi̱ nixtjín lunes asta viernes, "
                    "las ocho ñá asta las cuatro tjun.\n"
                    "Tjín ndi tuxi, kitsúya_jin ya ne número "
                    "teléfono tuxi. K'uendá tíxa̱ ndi̱ya.\n"
                    "Tu xi 'me urgencia, ndi̱xin ndi̱ clínica "
                    "o kitsúya 911.\n"
                    "Na̱ xá nda ndi̱.\"\n\n"
                    "[Audio adjunto: 26 segundos, MP3 128kbps, "
                    "grabado en estudio casero con tratamiento acústico.]"
                ),
                "note": "Traducción y grabación listas. El audio dura 26 segundos — dentro del rango solicitado. Usé voz profesional y tranquilizadora. Lo grabé en mi estudio casero con tratamiento acústico, así que el audio es limpio sin eco ni ruido. Dejé las palabras 'Clínica Comunitaria Esperanza' y '911' en español porque son nombres propios que la gente reconoce así.",
            },

            # Complete jobs — accepted submissions
            {
                "job_title": "Transcripción de conversación en mercado para archivo lingüístico",
                "creator": "elena_triqui",
                "status": "accepted",
                "is_draft": False,
                "is_complete": True,
                "text_content": (
                    "Transcripción — Conversación en mercado de Tlaxiaco\n"
                    "Duración: 5:03 min | Lengua: Triqui de Chicahuaxtla\n"
                    "Transcriptora: Elena de Jesús Ramírez\n\n"
                    "Hablante A (vendedora de chiles):\n"
                    "Guná³ na³ nej¹ si³ [...] nej¹ nanj¹ da'vi³...\n\n"
                    "Hablante B (compradora):\n"
                    "¿Ñaj² chru³gataj¹ nanj¹ nej¹ si³?\n\n"
                    "Hablante A:\n"
                    "Ná² ga'anj³ si³ [...] ruku³ nanj¹...\n"
                    "[...] [risas]\n\n"
                    "Hablante B:\n"
                    "A'min³ ga'anj³ [...] \"chile ancho\" [...]\n\n"
                    "[Transcripción completa: 847 palabras en triqui, "
                    "12 préstamos del español marcados en cursiva, "
                    "tonos marcados con superíndices numéricos "
                    "según la convención de Hollenbach (1984).]\n\n"
                    "[Nota: La conversación cubre temas de precios, "
                    "calidad de los chiles, una receta de salsa, y "
                    "chismes del pueblo. Las hablantes cambian al español "
                    "para números y algunas marcas comerciales.]"
                ),
                "note": "Transcripción completa con marcación tonal. Identifiqué 12 préstamos del español. La conversación es muy rica lingüísticamente — tiene vocabulario de comercio, alimentos y relaciones sociales. Fue un gusto trabajar en esto.",
            },
            {
                "job_title": "Traducir requisitos de programa de apoyo para artesanas",
                "creator": "carmen_chinanteca",
                "status": "accepted",
                "is_draft": False,
                "is_complete": True,
                "text_content": (
                    "Traducción al chinanteco de Ojitlán:\n\n"
                    "JÑI' KIAA JI̱ M'A ARTESANAS\n\n"
                    "Jña kiaa:\n"
                    "• Kiaa ji̱ jña̱ hma̱ 18 ji̱ñu̱\n"
                    "• Kjonga INE o kie jñu̱ tsei̱\n"
                    "• Kjonga jña kiaa ji̱ (jna̱, tsin, jyá̱ o jña kiaa)\n"
                    "• Tsei̱ ndi̱ ñú\n\n"
                    "Jña ka̱ tsjá:\n"
                    "• Capacitación ki̱ venta ne diseño — tsini̱ fje̱\n"
                    "• $3,000 pesos jñi tsei̱ ka̱ — 6 jñu̱\n"
                    "• Lugar ji̱ feria artesanal regional\n\n"
                    "Ka̱ ngata̱jña: 30 noviembre\n"
                    "Ji̱ casa ejidal — 9 jña̱ asta 2 tsjun\n\n"
                    "[Nota: Dejé \"$3,000 pesos\", \"INE\", y "
                    "\"capacitación\" en español porque son términos "
                    "que la gente reconoce así. Las fechas y horarios "
                    "también los dejé en español para evitar confusiones "
                    "con cifras.]"
                ),
                "note": "Traducción completa. Dejé algunos términos en español que la comunidad usa así (pesos, INE, capacitación) para evitar confusiones con trámites oficiales. Las mujeres de mi comunidad me ayudaron a revisar que todo se entienda bien.",
            },
            {
                "job_title": "Traducir botones de interfaz para app móvil",
                "creator": "maria_nahuatl",
                "status": "accepted",
                "is_draft": False,
                "is_complete": True,
                "text_content": (
                    "Traducción de interfaz — Náhuatl de la Huasteca Veracruzana\n\n"
                    "• Inicio → Pehualistli\n"
                    "• Mis Mensajes → Notlahtolhuan\n"
                    "• Notificaciones → Tenahuatilli\n"
                    "• Cerrar Sesión → Nictlalia\n"
                    "• Siguiente → Niman\n"
                    "• Anterior → Achto\n"
                    "• Regresar → Mocuepa\n"
                    "• Buscar → Tlatemolistli\n"
                    "• Guardar → Nictlalia\n"
                    "• Enviar → Niktitlani\n"
                    "• Cancelar → Amo\n"
                    "• Mi Perfil → Noixiptla\n"
                    "• Configuración → Tlanahuatilli\n"
                    "• Ayuda → Palehuiliztli\n"
                    "• Publicar un nuevo trabajo → Xictlali yancuic tequitl\n"
                    "• Ver todos los trabajos → Xiquitta nochi tequitl\n"
                    "• Mis trabajos → Notequiuh\n"
                    "• Abierto → Tlapohualli\n"
                    "• Cerrado → Tlatzacualli\n"
                    "• En progreso → Mochihuatica\n"
                    "• Completado → Tzonquixtoc\n\n"
                    "[Nota: Mantuve todos los botones en 1-3 palabras. "
                    "\"Cancelar\" lo traduje como \"Amo\" (No) porque es "
                    "más natural y conciso que la traducción literal.]"
                ),
                "note": "Todas las traducciones listas. Logré mantener todos los botones concisos — máximo 3 palabras. Hice una nota sobre 'Cancelar' que traduje como 'Amo' porque es más natural. Si prefieren otra opción puedo ajustar.",
            },
        ]

        total = 0
        for sd in submissions:
            try:
                job = Job.objects.get(title=sd["job_title"])
                creator = User.objects.get(username=sd["creator"])
            except (Job.DoesNotExist, User.DoesNotExist):
                continue
            if JobSubmission.objects.filter(job=job, creator=creator).exists():
                continue

            sub = JobSubmission.objects.create(
                job=job,
                creator=creator,
                status=sd["status"],
                is_draft=sd.get("is_draft", False),
                is_complete=sd.get("is_complete", False),
                text_content=sd.get("text_content", ""),
                note=sd.get("note", ""),
                completed_at=timezone.now() if sd.get("is_complete") else None,
            )
            total += 1

        self.stdout.write(self.style.SUCCESS(f"  Submissions: {total} created"))

    # ── Audio wiring ───────────────────────────────────────────────────

    def _wire_audio(self):
        self.stdout.write("\n── Wiring audio snippets ──")

        # Map of audio files to static UI slugs
        audio_map = {
            "Inicio.mp3": ("nav_home", "Inicio", "navigation"),
            "Comprador.mp3": ("role_buyer", "Comprador", "button"),
            "Otomi.mp3": ("lang_otomi", "Otomí", "button"),
            "Mis-Productos.mp3": ("dashboard_my_products", "Mis Productos", "dashboard"),
            "Mi-Dinero---Mi-Billetera.mp3": ("dashboard_my_money", "Mi Dinero / Mi Billetera", "dashboard"),
            "Mis-Trabajos-por-terminar.mp3": ("dashboard_pending_jobs", "Mis Trabajos por terminar", "dashboard"),
            "Nombre-de-usuario.mp3": ("form_username", "Nombre de usuario", "form"),
            "No-esta-mi-idioma---Solicitar-otro-idioma.mp3": (
                "lang_request_other", "No está mi idioma / Solicitar otro idioma", "button"),
            "Perdon-aun-no-hay-traduccion.mp3": (
                "msg_no_translation", "Perdón, aún no hay traducción", "message"),
            "Los-dos-(contratar---vender).mp3": ("role_both", "Los dos (contratar / vender)", "button"),
            "Adaptar-esto-a-tus-palabras-locales.mp3": (
                "action_localize", "Adaptar esto a tus palabras locales", "button"),
            "Crear-arte-sobre-este-tema.mp3": ("action_create_art", "Crear arte sobre este tema", "button"),
            "Crear-una-versión-local.mp3": ("action_create_local", "Crear una versión local", "button"),
            "Crear-una-versión-local-de-este-audio.mp3": (
                "action_create_local_audio", "Crear una versión local de este audio", "button"),
            "Crear-una-versión-local-de-este-video.mp3": (
                "action_create_local_video", "Crear una versión local de este video", "button"),
            "Contraseña.mp3": ("form_password", "Contraseña", "form"),
            "Confirma-tu-Contraseña.mp3": ("form_confirm_password", "Confirma tu Contraseña", "form"),
            "Ingresar---Iniciar-Sesión.mp3": ("action_login", "Ingresar / Iniciar Sesión", "button"),
            "Ingresar-Iniciar-Sesión.mp3": ("action_login_alt", "Ingresar / Iniciar Sesión", "button"),
            "Escoge-tu-idioma--Qué-idiomas-hablas.mp3": (
                "form_choose_language", "Escoge tu idioma / Qué idiomas hablas", "form"),
            "Número-de-teléfono.mp3": ("form_phone", "Número de teléfono", "form"),
            "Al-registrarte,-aceptas-nuestros-Términos-y-Condiciones-y-nuestra-Política-de-Privacidad.mp3": (
                "msg_terms", "Al registrarte, aceptas nuestros Términos y Condiciones", "message"),
            "Perdón-esto-aún-no-se-ha-traducido.mp3": (
                "msg_not_yet_translated", "Perdón, esto aún no se ha traducido", "message"),
            "Bienvenidos-a-nuestra-casa,-la-casa-del-bosque.-Cuiden-de-nuestra-tierra-como-nosotros-lo-hacemos..mp3": (
                "content_ecoturismo_welcome", "Bienvenidos a nuestra casa", "message"),
            "Este-domingo-son-las-elecciones.-Tu-voto-es-libre-y-secreto.-Participa-para-decidir-el-futuro-de-tu-comunidad.-Acude-a-tu-casilla-con-tu-credencial.-Tu-voz-cuenta.mp3": (
                "content_election_spot", "Spot electoral", "message"),
        }

        # Source directories for audio files
        source_dirs = [
            os.path.join(settings.BASE_DIR, "media", "audio", "snippets", "2025", "11", "09"),
            os.path.join(settings.MEDIA_ROOT, "..", "..", "media", "Audio", "mp3"),
        ]

        # Find the actual source dir with mp3 files
        mp3_source = None
        for d in source_dirs:
            if os.path.isdir(d) and any(f.endswith(".mp3") for f in os.listdir(d)):
                mp3_source = d
                break

        if not mp3_source:
            # Try the project-level media directory
            project_media = os.path.join(settings.BASE_DIR, "..", "media", "Audio", "mp3")
            if os.path.isdir(project_media):
                mp3_source = project_media

        if not mp3_source:
            self.stdout.write(self.style.WARNING("  No audio source directory found, skipping audio wiring."))
            return

        snippet_dest = os.path.join(settings.MEDIA_ROOT, "audio", "snippets", "demo")
        os.makedirs(snippet_dest, exist_ok=True)

        ct = ContentType.objects.get_for_model(StaticUIElement)
        created_elements = 0
        created_snippets = 0

        for filename, (slug, label_es, category) in audio_map.items():
            source_path = os.path.join(mp3_source, filename)
            if not os.path.isfile(source_path):
                # Try the snippets dir naming
                alt_name = filename.replace("(", "").replace(")", "").replace(",", "")
                source_path = os.path.join(mp3_source, alt_name)
                if not os.path.isfile(source_path):
                    continue

            # Create StaticUIElement
            elem, elem_created = StaticUIElement.objects.get_or_create(
                slug=slug,
                defaults={"label_es": label_es, "category": category},
            )
            if elem_created:
                created_elements += 1

            # Copy audio file to media
            dest_path = os.path.join(snippet_dest, filename)
            if not os.path.isfile(dest_path):
                shutil.copy2(source_path, dest_path)

            # Create AudioSnippet
            relative_path = os.path.join("audio", "snippets", "demo", filename)
            snippet, snip_created = AudioSnippet.objects.get_or_create(
                content_type=ct,
                object_id=elem.pk,
                target_field="label",
                language_code="oto",
                defaults={
                    "file": relative_path,
                    "status": "ready",
                    "transcript": label_es,
                },
            )
            if snip_created:
                created_snippets += 1

        self.stdout.write(self.style.SUCCESS(
            f"  UI Elements: {created_elements} created, Audio Snippets: {created_snippets} created"
        ))

    # ── Summary ────────────────────────────────────────────────────────

    def _print_summary(self):
        self.stdout.write("\n── Demo Summary ──")
        funders = User.objects.filter(role="funder").count()
        creators = User.objects.filter(role="creator").count()
        both = User.objects.filter(role="both").count()
        self.stdout.write(f"  Users: {funders} funders, {creators} creators, {both} both")
        for status in ["draft", "recruiting", "selecting", "submitting", "reviewing", "complete"]:
            count = Job.objects.filter(status=status).count()
            if count:
                self.stdout.write(f"  Jobs ({status}): {count}")
        self.stdout.write(f"  Applications: {JobApplication.objects.count()}")
        self.stdout.write(f"  Submissions: {JobSubmission.objects.count()}")
        self.stdout.write(f"  Audio Snippets: {AudioSnippet.objects.count()}")

        self.stdout.write("\n── Demo Logins ──")
        self.stdout.write("  All passwords: demo123")
        self.stdout.write("  Funders: demo_funder, voces_vivas, clinica_esperanza, cafe_sierra, instituto_electoral")
        self.stdout.write("  Active creators: carlos_otomi, maria_nahuatl, ana_quechua, pedro_zapoteco")
        self.stdout.write("  Both: miguel_both, sofia_both")
