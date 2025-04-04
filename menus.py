from instructions import instructions

translations = {
    "en": {
        "welcome": (
            "🎉 *Welcome to the Ultimate Content Bot!* 🎉\n\n"
            "Hey there! I’m your personal assistant for creating *killer Telegram posts* in seconds. "
            "Powered by DeepSeek & Flux, I’ll whip up texts and stunning images faster than you can say 'content!' 🚀\n\n"
            "✨ *What I can do for you:*\n"
            "- Generate 100 posts/month with a subscription\n"
            "- Auto-post to your channel\n"
            "- Free trial: 2 posts to test me out!\n\n"
            "Ready to rock? Pick an option below! 👇"
        ),
        "main_menu": "What’s next? 👇",
        "generate": "✍️ Create Post",
        "generate_text_only": "📝 Text Only",  # Новая кнопка
        "subscribe": "💎 Get Premium",
        "setchannel": "📢 Set Channel",
        "more": "⚙️ More Options",
        "back": "⬅️ Back",
        "about": "ℹ️ About Bot",
        "style_prompt": "Pick your vibe! 👇",
        "expert": "🧠 Expert",
        "hemingway": "📚 Hemingway",
        "ng": "🌍 Nat Geo",
        "journalist": "📰 Journalist",
        "poet": "✒️ Poet",
        "theme_prompt": "How many posts and what topic? (e.g., '3#travel')",
        "theme_saved": "Sweet! '{theme}' set with {post_count} posts.",
        "theme_error": "Oops! Use 'number#theme' (e.g., '3#travel').",
        "no_theme": "Hey, set a theme first with 'More Options'!",
        "generating": "Cooking up post {i}/{post_count} ({progress:.1f}%)...",
        "post_done": "'{title}' is live! {i}/{post_count} ({progress:.1f}%)",
        "post_error": "Uh-oh, '{title}' hit a snag. Moving on... ({progress:.1f}%)",
        "generation_complete": "Done! All posts are ready (100%)! 🎉",
        "titles_error": "Titles didn’t load. Try again?",
        "channel_prompt": (
            "Drop your channel ID (e.g., @MyChannel).\n\n"
            "*How to add me as admin:*\n1. Go to your channel (e.g., tg://resolve?domain={channel}).\n"
            "2. Tap 'Administrators' > 'Add Admin'.\n3. Search for [@Publikatory_Bot](tg://user?id=7607826839) (tap me to copy!) and grant 'Post Messages' rights."
        ),
        "channel_saved": "Channel '{channel}' locked in! 📢",
        "channel_error": "Channel needs to start with @ (e.g., @MyChannel).",
        "channel_not_found": "Channel '{channel}' doesn’t exist or is private. Check the ID!",
        "channel_no_admin": "I’m not an admin in '{channel}'. Make me one first!",
        "no_channel": "Set a channel first in 'More Options'!",
        "subscribe_prompt": "Unlock the magic! Pick a plan: 👇",
        "standard": "🌟 Standard ($40/mo) - 100 posts, Expert style",
        "premium": "💎 Premium ($60/mo) - 100 posts, Any style + Ultra pics",
        "no_subscription": "You need a subscription for this. Hit 'Get Premium'!",
        "subscription_expired": "Your sub expired. Renew it with 'Get Premium'!",
        "subscription_success": "{plan.capitalize()} plan activated! Let’s roll! 🚀",
        "post_limit_reached": "Monthly limit hit! Upgrade or wait till next month.",
        "style_limited": "Standard plan sticks to Expert style only.",
        "language_prompt": "Pick your language! 👇"
    },
    "ru": {  # Добавляем перевод для новой кнопки
        "welcome": (
            "🎉 *Добро пожаловать в Ultimate Content Bot!* 🎉\n\n"
            "Привет! Я твой личный помощник для создания *убийственных постов в Telegram* за секунды. "
            "С DeepSeek и Flux я создам тексты и крутые картинки быстрее, чем ты скажешь 'контент!' 🚀\n\n"
            "✨ *Что я умею:*\n"
            "- Генерировать 100 постов в месяц с подпиской\n"
            "- Автопостинг в твой канал\n"
            "- Бесплатно: 2 поста на пробу!\n\n"
            "Готов зажечь? Выбери опцию ниже! 👇"
        ),
        "main_menu": "Что дальше? 👇",
        "generate": "✍️ Создать пост",
        "generate_text_only": "📝 Только текст",  # Новая кнопка
        "subscribe": "💎 Взять Премиум",
        "setchannel": "📢 Указать канал",
        "more": "⚙️ Еще опции",
        "back": "⬅️ Назад",
        "about": "ℹ️ О боте",
        "style_prompt": "Выбери стиль! 👇",
        "expert": "🧠 Эксперт",
        "hemingway": "📚 Хемингуэй",
        "ng": "🌍 Nat Geo",
        "journalist": "📰 Журналист",
        "poet": "✒️ Поэт",
        "theme_prompt": "Сколько постов и какая тема? (например, '3#путешествия')",
        "theme_saved": "Круто! Тема '{theme}' с {post_count} постами установлена.",
        "theme_error": "Ой! Используй 'число#тема' (например, '3#путешествия').",
        "no_theme": "Сначала установи тему через 'Еще опции'!",
        "generating": "Готовлю пост {i}/{post_count} ({progress:.1f}%)...",
        "post_done": "'{title}' опубликован! {i}/{post_count} ({progress:.1f}%)",
        "post_error": "Упс, с '{title}' что-то пошло не так. Продолжаю... ({progress:.1f}%)",
        "generation_complete": "Готово! Все посты на месте (100%)! 🎉",
        "titles_error": "Заголовки не загрузились. Повторить?",
        "channel_prompt": (
            "Укажи ID канала (например, @MyChannel).\n\n"
            "*Как сделать меня админом:*\n1. Перейди в канал (например, tg://resolve?domain={channel}).\n"
            "2. Выбери 'Администраторы' > 'Добавить'.\n3. Найди [@Publikatory_Bot](tg://user?id=7607826839) (нажми и скопируй!) и дай права 'Публиковать сообщения'."
        ),
        "channel_saved": "Канал '{channel}' установлен! 📢",
        "channel_error": "Канал должен начинаться с @ (например, @MyChannel).",
        "channel_not_found": "Канал '{channel}' не существует или приватный. Проверь ID!",
        "channel_no_admin": "Я не админ в '{channel}'. Назначь меня сначала!",
        "no_channel": "Сначала укажи канал в 'Еще опции'!",
        "subscribe_prompt": "Раскрой магию! Выбери план: 👇",
        "standard": "🌟 Стандарт (40$/мес) - 100 постов, стиль Эксперт",
        "premium": "💎 Премиум (60$/мес) - 100 постов, любой стиль + Ultra-картинки",
        "no_subscription": "Для этого нужна подписка. Жми 'Взять Премиум'!",
        "subscription_expired": "Подписка истекла. Обнови через 'Взять Премиум'!",
        "subscription_success": "План {plan} активирован! Погнали! 🚀",
        "post_limit_reached": "Лимит месяца исчерпан! Обнови план или жди следующего месяца.",
        "style_limited": "Стандартный план ограничен стилем 'Эксперт'.",
        "language_prompt": "Выбери язык! 👇"
    },

    "es": {
        "welcome": (
            "🎉 *¡Bienvenido a Ultimate Content Bot!* 🎉\n\n"
            "¡Hola! Soy tu asistente personal para crear *posts increíbles en Telegram* en segundos. "
            "Con DeepSeek y Flux, genero textos e imágenes geniales más rápido de lo que puedes decir '¡contenido!' 🚀\n\n"
            "✨ *Qué puedo hacer por ti:*\n"
            "- Generar 100 posts/mes con suscripción\n"
            "- Publicar automáticamente en tu canal\n"
            "- Prueba gratis: ¡2 posts para probarme!\n\n"
            "¿Listo para arrasar? ¡Elige abajo! 👇"
        ),
        "main_menu": "¿Qué sigue? 👇",
        "generate": "✍️ Crear post",
        "generate_text_only": "📝 Solo texto",
        "subscribe": "💎 Obtener Premium",
        "setchannel": "📢 Elegir canal",
        "more": "⚙️ Más opciones",
        "back": "⬅️ Volver",
        "about": "ℹ️ Sobre el Bot",
        "style_prompt": "¡Elige tu estilo! 👇",
        "expert": "🧠 Experto",
        "hemingway": "📚 Hemingway",
        "ng": "🌍 Nat Geo",
        "journalist": "📰 Periodista",
        "poet": "✒️ Poeta",
        "theme_prompt": "¿Cuántos posts y qué tema? (ej. '3#viajes')",
        "theme_saved": "¡Genial! '{theme}' establecido con {post_count} posts.",
        "theme_error": "¡Ups! Usa 'número#tema' (ej. '3#viajes').",
        "no_theme": "¡Primero establece un tema en 'Más opciones'!",
        "generating": "Preparando post {i}/{post_count} ({progress:.1f}%)...",
        "post_done": "¡'{title}' está listo! {i}/{post_count} ({progress:.1f}%)",
        "post_error": "Oh no, '{title}' falló. Sigo adelante... ({progress:.1f}%)",
        "generation_complete": "¡Listo! Todos los posts están hechos (100%)! 🎉",
        "titles_error": "Los títulos no cargaron. ¿Reintentar?",
        "channel_prompt": (
            "Dame el ID del canal (ej. @MyChannel).\n\n"
            "*Cómo hacerme admin:*\n1. Ve a tu canal (ej., tg://resolve?domain={channel}).\n"
            "2. Toca 'Administradores' > 'Añadir admin'.\n3. Busca a [@Publikatory_Bot](tg://user?id=7607826839) (¡tócame y copia!) y dame 'Publicar mensajes'."
        ),
        "channel_saved": "¡Canal '{channel}' configurado! 📢",
        "channel_error": "El canal debe empezar con @ (ej. @MyChannel).",
        "channel_not_found": "El canal '{channel}' no existe o es privado. ¡Revisa el ID!",
        "channel_no_admin": "No soy admin en '{channel}'. ¡Agrégame primero!",
        "no_channel": "¡Primero define un canal en 'Más opciones'!",
        "subscribe_prompt": "¡Desbloquea la magia! Elige un plan: 👇",
        "standard": "🌟 Estándar (40$/mes) - 100 posts, estilo Experto",
        "premium": "💎 Premium (60$/mes) - 100 posts, cualquier estilo + imágenes Ultra",
        "no_subscription": "Necesitas una suscripción. ¡Pulsa 'Obtener Premium'!",
        "subscription_expired": "Tu suscripción expiró. ¡Renueva en 'Obtener Premium'!",
        "subscription_success": "¡Plan {plan} activado! ¡A por ello! 🚀",
        "post_limit_reached": "¡Límite mensual alcanzado! Actualiza o espera al próximo mes.",
        "style_limited": "El plan Estándar solo permite el estilo 'Experto'.",
        "language_prompt": "¡Elige tu idioma! 👇"
    },
    "fr": {
        "welcome": (
            "🎉 *Bienvenue chez Ultimate Content Bot!* 🎉\n\n"
            "Salut ! Je suis ton assistant perso pour créer des *posts Telegram de folie* en quelques secondes. "
            "Avec DeepSeek et Flux, je génère textes et images époustouflantes plus vite que tu ne peux dire 'contenu' ! 🚀\n\n"
            "✨ *Ce que je peux faire pour toi :*\n"
            "- Générer 100 posts/mois avec un abonnement\n"
            "- Publier auto sur ton canal\n"
            "- Essai gratuit : 2 posts pour tester !\n\n"
            "Prêt à tout déchirer ? Choisis ci-dessous ! 👇"
        ),
        "main_menu": "Et ensuite ? 👇",
        "generate": "✍️ Créer un post",
        "generate_text_only": "📝 Texte seulement",
        "subscribe": "💎 Prendre Premium",
        "setchannel": "📢 Définir un canal",
        "more": "⚙️ Plus d’options",
        "back": "⬅️ Retour",
        "about": "ℹ️ À propos du Bot",
        "style_prompt": "Choisis ton style ! 👇",
        "expert": "🧠 Expert",
        "hemingway": "📚 Hemingway",
        "ng": "🌍 Nat Geo",
        "journalist": "📰 Journaliste",
        "poet": "✒️ Poète",
        "theme_prompt": "Combien de posts et quel thème ? (ex. '3#voyage')",
        "theme_saved": "Cool ! '{theme}' défini avec {post_count} posts.",
        "theme_error": "Oups ! Utilise 'nombre#thème' (ex. '3#voyage').",
        "no_theme": "Définis d’abord un thème via 'Plus d’options' !",
        "generating": "Préparation du post {i}/{post_count} ({progress:.1f}%)...",
        "post_done": "'{title}' est en ligne ! {i}/{post_count} ({progress:.1f}%)",
        "post_error": "Aïe, souci avec '{title}'. Je continue... ({progress:.1f}%)",
        "generation_complete": "Fini ! Tous les posts sont prêts (100%) ! 🎉",
        "titles_error": "Les titres n’ont pas chargé. Réessayer ?",
        "channel_prompt": (
            "Indique l’ID du canal (ex. @MyChannel).\n\n"
            "*Comment me faire admin :*\n1. Va sur ton canal (ex., tg://resolve?domain={channel}).\n"
            "2. Clique 'Administrateurs' > 'Ajouter admin'.\n3. Cherche [@Publikatory_Bot](tg://user?id=7607826839) (touche et copie !) et donne-moi 'Publier des messages'."
        ),
        "channel_saved": "Canal '{channel}' verrouillé ! 📢",
        "channel_error": "Le canal doit commencer par @ (ex. @MyChannel).",
        "channel_not_found": "Le canal '{channel}' n’existe pas ou est privé. Vérifie l’ID !",
        "channel_no_admin": "Je ne suis pas admin sur '{channel}'. Ajoute-moi d’abord !",
        "no_channel": "Définis un canal via 'Plus d’options' d’abord !",
        "subscribe_prompt": "Débloque la magie ! Choisis un plan : 👇",
        "standard": "🌟 Standard (40$/mois) - 100 posts, style Expert",
        "premium": "💎 Premium (60$/mois) - 100 posts, tout style + images Ultra",
        "no_subscription": "Il te faut un abonnement. Clique 'Prendre Premium' !",
        "subscription_expired": "Ton abonnement a expiré. Renouvelle via 'Prendre Premium' !",
        "subscription_success": "Plan {plan} activé ! On y va ! 🚀",
        "post_limit_reached": "Limite mensuelle atteinte ! Upgrade ou attends le mois prochain.",
        "style_limited": "Le plan Standard est limité au style 'Expert'.",
        "language_prompt": "Choisis ta langue ! 👇"
    },
    "de": {
        "welcome": (
            "🎉 *Willkommen beim Ultimate Content Bot!* 🎉\n\n"
            "Hallo! Ich bin dein persönlicher Assistent, um *geniale Telegram-Posts* in Sekunden zu erstellen. "
            "Mit DeepSeek & Flux zaubere ich Texte und beeindruckende Bilder schneller, als du 'Content' sagen kannst! 🚀\n\n"
            "✨ *Was ich für dich tun kann:*\n"
            "- 100 Posts/Monat mit Abo generieren\n"
            "- Automatisch in deinen Kanal posten\n"
            "- Kostenloser Test: 2 Posts zum Ausprobieren!\n\n"
            "Bereit zu rocken? Wähle unten! 👇"
        ),
        "main_menu": "Was kommt als Nächstes? 👇",
        "generate": "✍️ Post erstellen",
        "generate_text_only": "📝 Nur Text",
        "subscribe": "💎 Premium holen",
        "setchannel": "📢 Kanal festlegen",
        "more": "⚙️ Mehr Optionen",
        "back": "⬅️ Zurück",
        "about": "ℹ️ Über den Bot",
        "style_prompt": "Wähl deinen Stil! 👇",
        "expert": "🧠 Experte",
        "hemingway": "📚 Hemingway",
        "ng": "🌍 Nat Geo",
        "journalist": "📰 Journalist",
        "poet": "✒️ Dichter",
        "theme_prompt": "Wie viele Posts und welches Thema? (z.B. '3#reisen')",
        "theme_saved": "Super! '{theme}' mit {post_count} Posts festgelegt.",
        "theme_error": "Hoppla! Nutze 'Zahl#Thema' (z.B. '3#reisen').",
        "no_theme": "Leg erst ein Thema in 'Mehr Optionen' fest!",
        "generating": "Erstelle Post {i}/{post_count} ({progress:.1f}%)...",
        "post_done": "'{title}' ist live! {i}/{post_count} ({progress:.1f}%)",
        "post_error": "Ohje, '{title}' hat gehakt. Weiter geht’s... ({progress:.1f}%)",
        "generation_complete": "Fertig! Alle Posts sind bereit (100%)! 🎉",
        "titles_error": "Titel konnten nicht geladen werden. Nochmal?",
        "channel_prompt": (
            "Gib die Kanal-ID an (z.B. @MyChannel).\n\n"
            "*Wie mache ich mich zum Admin:*\n1. Geh zu deinem Kanal (z.B., tg://resolve?domain={channel}).\n"
            "2. Tippe 'Administratoren' > 'Admin hinzufügen'.\n3. Suche [@Publikatory_Bot](tg://user?id=7607826839) (tippe und kopiere!) und gib mir 'Nachrichten posten'."
        ),
        "channel_saved": "Kanal '{channel}' gesetzt! 📢",
        "channel_error": "Kanal muss mit @ beginnen (z.B. @MyChannel).",
        "channel_not_found": "Kanal '{channel}' existiert nicht oder ist privat. Überprüfe die ID!",
        "channel_no_admin": "Ich bin kein Admin in '{channel}'. Mach mich zuerst zum Admin!",
        "no_channel": "Leg erst einen Kanal in 'Mehr Optionen' fest!",
        "subscribe_prompt": "Entfessle die Magie! Wähl einen Plan: 👇",
        "standard": "🌟 Standard (40$/Monat) - 100 Posts, Experten-Stil",
        "premium": "💎 Premium (60$/Monat) - 100 Posts, jeder Stil + Ultra-Bilder",
        "no_subscription": "Du brauchst ein Abo. Klick 'Premium holen'!",
        "subscription_expired": "Dein Abo ist abgelaufen. Erneuere es mit 'Premium holen'!",
        "subscription_success": "Plan {plan} aktiviert! Los geht’s! 🚀",
        "post_limit_reached": "Monatslimit erreicht! Upgrade oder warte bis nächsten Monat.",
        "style_limited": "Standard-Plan ist auf 'Experte'-Stil beschränkt.",
        "language_prompt": "Wähl deine Sprache! 👇"
    }
}

language_menu = {
    "inline_keyboard": [
        [{"text": "🇬🇧 English", "callback_data": "lang_en"}, {"text": "🇷🇺 Русский", "callback_data": "lang_ru"}],
        [{"text": "🇫🇷 Français", "callback_data": "lang_fr"}, {"text": "🇪🇸 Español", "callback_data": "lang_es"}],
        [{"text": "🇩🇪 Deutsch", "callback_data": "lang_de"}]
    ]
}

def get_main_menu(lang="en"):
    return {
        "inline_keyboard": [
            [{"text": translations[lang]["generate"], "callback_data": "generate"},
             {"text": translations[lang]["generate_text_only"], "callback_data": "generate_text_only"}],  # Добавили кнопку
            [{"text": translations[lang]["subscribe"], "callback_data": "subscribe"},
             {"text": translations[lang]["setchannel"], "callback_data": "setchannel"}],
            [{"text": translations[lang]["more"], "callback_data": "more"},
             {"text": translations[lang]["about"], "callback_data": "about"}]
        ]
    }

def get_more_menu(lang="en"):
    return {  # Оставляем как было
        "inline_keyboard": [
            [{"text": "🎨 Set Style", "callback_data": "setstyle"},
             {"text": "📝 Set Theme", "callback_data": "settheme"}],
            [{"text": "🌐 Language", "callback_data": "language"},
             {"text": translations[lang]["back"], "callback_data": "back_to_main"}]
        ]
    }

def get_style_menu(lang="en"):
    return {  # Оставляем как было
        "inline_keyboard": [
            [{"text": translations[lang]["expert"], "callback_data": "style_expert"},
             {"text": translations[lang]["hemingway"], "callback_data": "style_hemingway"}],
            [{"text": translations[lang]["ng"], "callback_data": "style_ng"},
             {"text": translations[lang]["journalist"], "callback_data": "style_journalist"}],
            [{"text": translations[lang]["poet"], "callback_data": "style_poet"},
             {"text": translations[lang]["back"], "callback_data": "back_to_main"}]
        ]
    }

def get_subscription_menu(lang="en"):
    return {  # Оставляем как было
        "inline_keyboard": [
            [{"text": translations[lang]["standard"], "callback_data": "sub_standard"}],
            [{"text": translations[lang]["premium"], "callback_data": "sub_premium"}],
            [{"text": translations[lang]["back"], "callback_data": "back_to_main"}]
        ]
    }