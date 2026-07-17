from generator.builder import ChapterBuilder
from model import Project


def build_ars_nouveau_foundations(project: Project, actually_additions_complete: str) -> str:
    chapter = ChapterBuilder(
        project,
        slug="06_ars_nouveau",
        title="Ars Nouveau",
        icon="ars_nouveau:novice_spell_book",
        description=(
            "Begin your magical studies with Source generation, spellbook construction, "
            "glyph inscription, and a practical introductory spell workshop."
        ),
    )

    begin = chapter.quest(
        "begin", "A New Kind of Power", "ars_nouveau:novice_spell_book",
        "Technology has taught you to shape machines and energy. Ars Nouveau begins a different path: shaping Source into programmable magic.",
        0, 0,
    ).depends_on(actually_additions_complete).checkmark().finish()

    notebook = chapter.quest(
        "worn_notebook", "The Worn Notebook", "ars_nouveau:worn_notebook",
        "Obtain the Worn Notebook and keep it nearby. It explains Ars Nouveau structures, rituals, spell components, and progression.",
        2, -2,
    ).depends_on(begin).item("ars_nouveau:worn_notebook").finish()

    archwood = chapter.quest(
        "archwood", "Trees Touched by Magic", "ars_nouveau:blue_archwood_log",
        "Gather Archwood logs. These magical trees provide materials used throughout the mod and often point toward nearby magical resources.",
        2, 1,
    ).depends_on(begin).item("ars_nouveau:blue_archwood_log", 8).finish()

    source_gems = chapter.quest(
        "source_gems", "Crystallized Source", "ars_nouveau:source_gem",
        "Acquire Source Gems, the foundational crafting material for spellbooks, magical devices, and Source infrastructure.",
        4, 1,
    ).depends_on(archwood).item("ars_nouveau:source_gem", 8).finish()

    spellbook = chapter.quest(
        "novice_spell_book", "Your First Spellbook", "ars_nouveau:novice_spell_book",
        "Craft a Novice Spell Book. It stores your spell recipes and lets you combine forms, effects, and augments into custom spells.",
        4, -2,
    ).depends_on(notebook, source_gems).item("ars_nouveau:novice_spell_book").finish()

    scribes_table = chapter.quest(
        "scribes_table", "Write Magic into Form", "ars_nouveau:scribes_table",
        "Craft a Scribe's Table. This workstation inscribes new glyphs into your spellbook when supplied with the required ingredients.",
        6, -2,
    ).depends_on(spellbook).item("ars_nouveau:scribes_table").finish()

    glyph_form = chapter.quest(
        "glyph_form", "Forms Begin the Spell", "ars_nouveau:glyph_touch",
        "Learn a spell form such as Touch or Projectile. Every spell begins by defining how its effects reach a target.",
        8, -3,
    ).depends_on(scribes_table).checkmark().finish()

    glyph_effect = chapter.quest(
        "glyph_effect", "Effects Shape the Result", "ars_nouveau:glyph_break",
        "Learn an effect glyph such as Break, Harm, or Ignite. Effects determine what the spell actually does after its form is resolved.",
        8, -1,
    ).depends_on(scribes_table).checkmark().finish()

    first_spell = chapter.quest(
        "first_spell", "Compose Your First Spell", "ars_nouveau:novice_spell_book",
        "Create and cast a working spell containing at least one form and one effect. Test it somewhere safe before relying on it in combat or mining.",
        10, -2,
    ).depends_on(glyph_form, glyph_effect).checkmark().reward_item("minecraft:lapis_lazuli", 8).finish()

    imbument = chapter.quest(
        "imbuement_chamber", "Imbue the Mundane", "ars_nouveau:imbuement_chamber",
        "Build an Imbuement Chamber. It transforms ordinary materials into magical components and becomes central to early Ars Nouveau crafting.",
        6, 2,
    ).depends_on(source_gems).item("ars_nouveau:imbuement_chamber").finish()

    source_jar = chapter.quest(
        "source_jar", "Bottle the Current", "ars_nouveau:source_jar",
        "Craft a Source Jar to store magical energy. Place it near Source-producing and Source-consuming devices so your workshop has a visible buffer.",
        8, 2,
    ).depends_on(imbument).item("ars_nouveau:source_jar").finish()

    agronomic = chapter.quest(
        "agronomic_sourcelink", "Source from Growth", "ars_nouveau:agronomic_sourcelink",
        "The Agronomic Sourcelink converts nearby plant growth into Source. Build one beside an active crop or tree farm.",
        10, 1,
    ).depends_on(source_jar).item("ars_nouveau:agronomic_sourcelink").finish()

    volcanic = chapter.quest(
        "volcanic_sourcelink", "Source from Flame", "ars_nouveau:volcanic_sourcelink",
        "The Volcanic Sourcelink generates Source from nearby fuel-burning activity. Use it when your base already has steady furnace operations.",
        10, 3,
        optional=True,
    ).depends_on(source_jar).item("ars_nouveau:volcanic_sourcelink").finish()

    relay = chapter.quest(
        "source_relay", "Guide the Flow", "ars_nouveau:relay",
        "Source Relays move Source between devices and jars. Use one to organize a workshop that cannot fit every block around a single jar.",
        12, 2,
    ).depends_on(agronomic).item("ars_nouveau:relay").finish()

    pedestal = chapter.quest(
        "arcane_pedestal", "A Pedestal for Magic", "ars_nouveau:arcane_pedestal",
        "Craft an Arcane Pedestal. Pedestals hold items for magical automation, rituals, and later crafting structures.",
        12, 4,
    ).depends_on(relay).item("ars_nouveau:arcane_pedestal").finish()

    magebloom = chapter.quest(
        "magebloom", "Cultivate Magebloom", "ars_nouveau:magebloom",
        "Grow Magebloom and harvest its fibers. This renewable magical crop supports robes, utility items, and later spellcasting equipment.",
        12, 0,
    ).depends_on(agronomic).item("ars_nouveau:magebloom", 4).finish()

    apparatus = chapter.quest(
        "enchanting_apparatus", "The Enchanting Apparatus", "ars_nouveau:enchanting_apparatus",
        "Build an Enchanting Apparatus with surrounding Arcane Pedestals. This multiblock crafts many of Ars Nouveau's more advanced items.",
        14, 3,
    ).depends_on(pedestal, magebloom).item("ars_nouveau:enchanting_apparatus").finish()

    essence = chapter.quest(
        "first_essence", "Distill Magical Essence", "ars_nouveau:manipulation_essence",
        "Craft your first magical essence with the Enchanting Apparatus. Essences gate many advanced glyphs, devices, and upgrades.",
        16, 3,
    ).depends_on(apparatus).item("ars_nouveau:manipulation_essence").finish()

    spell_turret = chapter.quest(
        "spell_turret", "Magic on Command", "ars_nouveau:basic_spell_turret",
        "Craft a Basic Spell Turret and program it with a safe utility spell. Redstone-controlled casting introduces automated magic.",
        16, 0,
        optional=True,
    ).depends_on(first_spell, essence).item("ars_nouveau:basic_spell_turret").finish()

    mage_armor = chapter.quest(
        "mage_armor", "Dress for the Arcane", "ars_nouveau:arcanist_robes",
        "Craft a piece of Ars Nouveau mage armor. Magical equipment can improve mana capacity, regeneration, and specialized spellcasting builds.",
        16, -2,
        optional=True,
    ).depends_on(magebloom, essence).item("ars_nouveau:arcanist_robes").finish()

    return chapter.quest(
        "foundations_complete", "An Arcane Workshop", "ars_nouveau:source_jar",
        "You can generate and store Source, inscribe glyphs, compose spells, and operate the Enchanting Apparatus. Your formal magical studies can now begin.",
        18, 1,
    ).depends_on(first_spell, relay, apparatus, essence).checkmark().reward_item(
        "ars_nouveau:source_gem", 8
    ).finish()
