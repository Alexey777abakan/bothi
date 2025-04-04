TITLE_PROMPT = """Generate exactly {post_count} short, unique, and engaging titles for Telegram posts, focusing on key events, aspects, or examples of the theme '{theme}'. If the theme is a time period or specific topic (e.g., 'Marvel movies'), distribute titles evenly across key moments or characters, avoiding repetition or duplication of titles or themes. Do not use quotation marks, numbers, or any prefixes/suffixes in the titles. Provide only titles, one per line, without extra text or numbering."""

POST_PROMPT = """Write an SEO-optimized post in {style} style with the title *{title}*. Explore the event, aspect, or example from the title, based on the context of the theme '{theme}', without directly repeating the theme’s full phrasing. Use lively, emotional language, specific examples, and arguments. Length: strictly up to {max_length} characters, including the title and 3 relevant hashtags on a new line. Format: *{title}*\n\n[content]\n\n#hashtag1 #hashtag2 #hashtag3"""

IMAGE_PROMPT = """Create a concise and detailed prompt (150-200 words) for generating a photorealistic image in Flux API, perfectly reflecting the content of a post with the title '{title}' in the context of the theme '{theme}'.

1. **Key scene**: Describe the main action (e.g., caravan travel, competition, protest), characters (e.g., traders, explorers, leaders), and their interactions, matching the title and historical context (e.g., 2nd century BCE, modern day).
2. **Setting**: Specify the location (e.g., desert, stadium, city square), time of day (e.g., sunrise, sunset, night), and visual details enhancing the atmosphere.
3. **Objects**: List items from the title or theme (e.g., silk, medals, flags) with descriptions of color, texture, position, and historical authenticity.
4. **Atmosphere**: Define the mood (e.g., adventure, tension, nostalgia), lighting (e.g., golden sunlight, spotlights, fog), and historical context.
5. **Style**: Photorealism with sharp lines, realistic colors, and high detail.
6. **Composition**: Central object (e.g., person, caravan, symbol) in focus, dynamic or static movement, background (e.g., desert, mountains) reinforcing the theme.
7. Aspect ratio 1:1, 8K resolution."""